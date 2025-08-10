// SSH Tester v3 — wxWidgets 3.2 + libssh (C++17)
// Recursos: password, keyboard-interactive, chave privada; known_hosts (API nova); comando pós-login

#include <wx/wx.h>
#include <wx/listctrl.h>
#include <wx/spinctrl.h>
#include <wx/tokenzr.h>
#include <wx/socket.h>
#include <wx/filedlg.h>
#include <wx/filename.h>

#include <thread>
#include <atomic>
#include <chrono>
#include <optional>
#include <vector>

#include <libssh/libssh.h>
#include <libssh/callbacks.h>

// ===== UTF-8 helper (arruma acentuação na UI) =====
static inline wxString U8(const char* s) { return wxString::FromUTF8(s); }

// ===== Resultado =====
struct SSHResult {
    wxString host, ip, fingerprint, stdout_text, error, auth{U8("password")};
    int port{22}, time_ms{0};
    bool ok{false};
};

// ===== Helpers =====
static std::optional<wxString> ResolveIP(const wxString& host) {
    wxIPV4address addr;
    if (addr.Hostname(host) && !addr.IPAddress().empty())
        return addr.IPAddress();
    return std::nullopt;
}

// API nova para known_hosts (libssh >= 0.10)
static int AcceptOrCheckKnownHost(ssh_session s) {
#if LIBSSH_VERSION_INT >= SSH_VERSION_INT(0,10,0)
    int st = ssh_session_is_known_server(s);
    switch (st) {
        case SSH_KNOWN_HOSTS_OK:        return SSH_OK;
        case SSH_KNOWN_HOSTS_NOT_FOUND: // sem known_hosts
        case SSH_KNOWN_HOSTS_UNKNOWN:   // host ainda não conhecido
            return ssh_session_update_known_hosts(s); // aceitar e gravar (laboratório)
        case SSH_KNOWN_HOSTS_CHANGED:
        case SSH_KNOWN_HOSTS_OTHER:
        case SSH_KNOWN_HOSTS_ERROR:
        default:
            return SSH_ERROR; // rejeita por segurança
    }
#else
    if (ssh_is_server_known(s) != SSH_SERVER_KNOWN_OK) return ssh_write_knownhost(s);
    return SSH_OK;
#endif
}

static int AuthPassword(ssh_session s, const wxString& pass) {
    return ssh_userauth_password(s, nullptr, pass.mb_str().data());
}

static int AuthKBI(ssh_session s, const wxString& user, const wxString& pass) {
    int rc = ssh_userauth_kbdint(s, user.mb_str().data(), nullptr);
    if (rc == SSH_AUTH_ERROR) return rc;

    while (rc == SSH_AUTH_INFO) {
        int np = ssh_userauth_kbdint_getnprompts(s);
        for (int i = 0; i < np; ++i) {
            char echo = 0;
            const char* prompt = ssh_userauth_kbdint_getprompt(s, i, &echo);
            if (!prompt) return SSH_AUTH_ERROR;   // falha ao obter prompt
            // respondemos todos os prompts com a "senha"
            ssh_userauth_kbdint_setanswer(s, i, pass.mb_str().data());
        }
        rc = ssh_userauth_kbdint(s, user.mb_str().data(), nullptr);
    }
    return rc;
}

static int AuthPrivateKey(ssh_session s, const wxString& user, const wxString& keyPath, const wxString& passphrase) {
    ssh_key pkey = nullptr;
    int rc = ssh_pki_import_privkey_file(keyPath.mb_str().data(),
                                         passphrase.empty() ? nullptr : passphrase.mb_str().data(),
                                         nullptr, nullptr, &pkey);
    if (rc != SSH_OK) return SSH_AUTH_ERROR;
    rc = ssh_userauth_publickey(s, user.mb_str().data(), pkey);
    ssh_key_free(pkey);
    return rc;
}

// ===== Conexão =====
static SSHResult RunSSH(const wxString& host, int port,
                        const wxString& user,
                        const wxString& pass,
                        const wxString& cmd,
                        const wxString& authMethod,      // "password" | "keyboard-interactive" | "private-key"
                        const wxString& keyPath,
                        const wxString& passphrase) {
    SSHResult r; r.host = host; r.port = port; r.auth = authMethod;
    auto t0 = std::chrono::steady_clock::now();

    ssh_session s = ssh_new();
    if (!s) { r.error = U8("ssh_new falhou"); return r; }

    ssh_options_set(s, SSH_OPTIONS_HOST, host.mb_str().data());
    ssh_options_set(s, SSH_OPTIONS_PORT, &port);
    if (!user.empty()) ssh_options_set(s, SSH_OPTIONS_USER, user.mb_str().data());
    int to_us = 15 * 1000 * 1000; // 15s
    ssh_options_set(s, SSH_OPTIONS_TIMEOUT_USEC, &to_us);

    if (ssh_connect(s) != SSH_OK) {
        r.error = wxString::Format(U8("Conexão: %s"), ssh_get_error(s));
        ssh_free(s);
        r.time_ms = (int)std::chrono::duration_cast<std::chrono::milliseconds>(
                        std::chrono::steady_clock::now() - t0).count();
        return r;
    }

    if (auto ip = ResolveIP(host)) r.ip = *ip;

    // fingerprint SHA256
    ssh_key k = nullptr; unsigned char* hash = nullptr; size_t hlen = 0;
    if (ssh_get_server_publickey(s, &k) == SSH_OK &&
        ssh_get_publickey_hash(k, SSH_PUBLICKEY_HASH_SHA256, &hash, &hlen) == SSH_OK) {
        wxString fp; fp.reserve(hlen*2);
        for (size_t i=0;i<hlen;++i) fp += wxString::Format("%02x", hash[i]);
        r.fingerprint = fp;
        ssh_clean_pubkey_hash(&hash);
    }
    if (k) ssh_key_free(k);

    // known_hosts
    if (AcceptOrCheckKnownHost(s) != SSH_OK) {
        r.error = U8("Host key inválida/alterada (known_hosts)");
        ssh_disconnect(s); ssh_free(s);
        r.time_ms = (int)std::chrono::duration_cast<std::chrono::milliseconds>(
                        std::chrono::steady_clock::now() - t0).count();
        return r;
    }

    // autenticação
    int rc = SSH_AUTH_ERROR;
    if (authMethod == U8("password")) {
        rc = AuthPassword(s, pass);
    } else if (authMethod == U8("keyboard-interactive")) {
        rc = AuthKBI(s, user, pass);
    } else if (authMethod == U8("private-key")) {
        rc = AuthPrivateKey(s, user, keyPath, passphrase);
    }

    if (rc != SSH_AUTH_SUCCESS) {
        r.error = wxString::Format(U8("Auth (%s): %s"), authMethod, ssh_get_error(s));
        ssh_disconnect(s); ssh_free(s);
        r.time_ms = (int)std::chrono::duration_cast<std::chrono::milliseconds>(
                        std::chrono::steady_clock::now() - t0).count();
        return r;
    }

    // comando opcional
    if (!cmd.empty()) {
        ssh_channel ch = ssh_channel_new(s);
        if (!ch) r.error = U8("ssh_channel_new falhou");
        else if (ssh_channel_open_session(ch) != SSH_OK) r.error = U8("ssh_channel_open_session falhou");
        else if (ssh_channel_request_exec(ch, cmd.mb_str().data()) != SSH_OK) r.error = U8("ssh_channel_request_exec falhou");
        else {
            char buf[4096]; int n; wxString out;
            while ((n = ssh_channel_read(ch, buf, sizeof(buf), 0)) > 0) {
                out.append(wxString::FromUTF8(buf, n));
            }
            r.stdout_text = out;
            ssh_channel_send_eof(ch);
        }
        if (ch) { ssh_channel_close(ch); ssh_channel_free(ch); }
    }

    ssh_disconnect(s); ssh_free(s);
    r.ok = true;
    r.time_ms = (int)std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::steady_clock::now() - t0).count();
    return r;
}

// ===== Sobre =====
class AboutDlg : public wxDialog {
public:
    AboutDlg(wxWindow* parent)
    : wxDialog(parent, wxID_ANY, U8("Sobre o aplicativo"), wxDefaultPosition, wxSize(480, 320))
    {
        auto* p = new wxPanel(this);
        auto* v = new wxBoxSizer(wxVERTICAL);

        auto* title = new wxStaticText(p, wxID_ANY, U8("SSH Tester v3"));
        title->SetFont(wxFontInfo(12).Bold());
        v->Add(title, 0, wxALL | wxALIGN_CENTER_HORIZONTAL, 8);

        auto* lbl = new wxStaticText(p, wxID_ANY,
            U8("Ferramenta para testar conectividade e autenticação SSH (password, KBI, chave)\n"
               "e executar um comando pós-login.\n\n"
               "Autor: Marcos Silva (Sr. Aragones)\n"
               "Licença: GPL-3.0"));
        lbl->SetForegroundColour(wxColour(70,70,70));
        v->Add(lbl, 0, wxALL | wxALIGN_CENTER_HORIZONTAL, 6);

        v->AddStretchSpacer();
        v->Add(new wxButton(p, wxID_OK, U8("OK")), 0, wxALL | wxALIGN_CENTER_HORIZONTAL, 10);

        p->SetSizer(v);
        CentreOnParent();
    }
};

// ===== GUI principal =====
class MainFrame : public wxFrame {
public:
    MainFrame() : wxFrame(nullptr, wxID_ANY, U8("SSH Tester v3 (wxWidgets + libssh)"), wxDefaultPosition, wxSize(1024,640)) {
        auto* panel = new wxPanel(this);
        auto* vbox = new wxBoxSizer(wxVERTICAL);

        vbox->Add(new wxStaticText(panel, wxID_ANY, U8("Hosts (um por linha; aceita host ou host:porta):")), 0, wxALL, 8);
        txtHosts = new wxTextCtrl(panel, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, wxTE_MULTILINE);
        txtHosts->SetMinSize(wxSize(-1, 100));
        vbox->Add(txtHosts, 0, wxEXPAND | wxLEFT | wxRIGHT, 8);

        auto* grid = new wxFlexGridSizer(3, 8, 6, 6);
        grid->AddGrowableCol(7);

        grid->Add(new wxStaticText(panel, wxID_ANY, U8("Usuário:")), 0, wxALIGN_CENTER_VERTICAL);
        txtUser = new wxTextCtrl(panel, wxID_ANY, "");
        grid->Add(txtUser, 0, wxEXPAND);

        grid->Add(new wxStaticText(panel, wxID_ANY, U8("Senha:")), 0, wxALIGN_CENTER_VERTICAL);
        txtPass = new wxTextCtrl(panel, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, wxTE_PASSWORD);
        grid->Add(txtPass, 0, wxEXPAND);

        grid->Add(new wxStaticText(panel, wxID_ANY, U8("Porta padrão:")), 0, wxALIGN_CENTER_VERTICAL);
        spinPort = new wxSpinCtrl(panel, wxID_ANY, "22", wxDefaultPosition, wxDefaultSize, wxSP_ARROW_KEYS, 1, 65535, 22);
        grid->Add(spinPort, 0);

        grid->Add(new wxStaticText(panel, wxID_ANY, U8("Comando pós-login:")), 0, wxALIGN_CENTER_VERTICAL);
        txtCmd = new wxTextCtrl(panel, wxID_ANY, "whoami");
        grid->Add(txtCmd, 0, wxEXPAND);

        grid->Add(new wxStaticText(panel, wxID_ANY, U8("Auth:")), 0, wxALIGN_CENTER_VERTICAL);
        choiceAuth = new wxChoice(panel, wxID_ANY);
        choiceAuth->Append(U8("password"));
        choiceAuth->Append(U8("keyboard-interactive"));
        choiceAuth->Append(U8("private-key"));
        choiceAuth->SetSelection(0);
        grid->Add(choiceAuth, 0, wxEXPAND);

        grid->Add(new wxStaticText(panel, wxID_ANY, U8("Arquivo de chave:")), 0, wxALIGN_CENTER_VERTICAL);
        txtKey = new wxTextCtrl(panel, wxID_ANY, "");
        grid->Add(txtKey, 0, wxEXPAND);
        auto* btnBrowse = new wxButton(panel, wxID_ANY, U8("..."));
        grid->Add(btnBrowse, 0);

        grid->Add(new wxStaticText(panel, wxID_ANY, U8("Passphrase:")), 0, wxALIGN_CENTER_VERTICAL);
        txtPassphrase = new wxTextCtrl(panel, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, wxTE_PASSWORD);
        grid->Add(txtPassphrase, 0, wxEXPAND);

        btnTest = new wxButton(panel, wxID_ANY, U8("Testar"));
        grid->Add(btnTest, 0);
        btnStop = new wxButton(panel, wxID_ANY, U8("Parar"));
        grid->Add(btnStop, 0);

        vbox->Add(grid, 0, wxEXPAND | wxLEFT | wxRIGHT | wxTOP, 8);

        list = new wxListCtrl(panel, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxLC_REPORT | wxLC_SINGLE_SEL);
        list->InsertColumn(0, U8("Host"), wxLIST_FORMAT_LEFT, 180);
        list->InsertColumn(1, U8("IP"), wxLIST_FORMAT_LEFT, 130);
        list->InsertColumn(2, U8("Porta"), wxLIST_FORMAT_LEFT, 60);
        list->InsertColumn(3, U8("OK"), wxLIST_FORMAT_LEFT, 50);
        list->InsertColumn(4, U8("Tempo (ms)"), wxLIST_FORMAT_LEFT, 90);
        list->InsertColumn(5, U8("Auth"), wxLIST_FORMAT_LEFT, 140);
        list->InsertColumn(6, U8("Fingerprint (SHA256)"), wxLIST_FORMAT_LEFT, 300);
        list->InsertColumn(7, U8("STDOUT"), wxLIST_FORMAT_LEFT, 300);
        list->InsertColumn(8, U8("Erro"), wxLIST_FORMAT_LEFT, 320);
        vbox->Add(list, 1, wxEXPAND | wxALL, 8);

        statusLbl = new wxStaticText(panel, wxID_ANY, U8("Pronto"));
        vbox->Add(statusLbl, 0, wxLEFT | wxRIGHT | wxBOTTOM, 8);

        panel->SetSizer(vbox);

        // menu Sobre
        auto* menubar = new wxMenuBar();
        auto* menuAjuda = new wxMenu();
        menuAjuda->Append(wxID_ABOUT, U8("Sobre"));
        menubar->Append(menuAjuda, U8("Ajuda"));
        SetMenuBar(menubar);
        Bind(wxEVT_MENU, [=](wxCommandEvent&){ AboutDlg dlg(this); dlg.ShowModal(); }, wxID_ABOUT);

        // eventos
        btnTest->Bind(wxEVT_BUTTON, &MainFrame::OnTest, this);
        btnStop->Bind(wxEVT_BUTTON, &MainFrame::OnStop, this);
        btnBrowse->Bind(wxEVT_BUTTON, [=](wxCommandEvent&){
            wxFileDialog dlg(this, U8("Selecionar chave privada"), "", "", U8("Chaves (*.*)|*.*"),
                             wxFD_OPEN | wxFD_FILE_MUST_EXIST);
            if (dlg.ShowModal()==wxID_OK) txtKey->SetValue(dlg.GetPath());
        });
        choiceAuth->Bind(wxEVT_CHOICE, [=](wxCommandEvent&){
            bool isKey = (choiceAuth->GetStringSelection()==U8("private-key"));
            txtKey->Enable(isKey);
            txtPassphrase->Enable(isKey);
        });
        // estado inicial
        txtKey->Enable(false);
        txtPassphrase->Enable(false);

        CreateStatusBar();
        SetStatusText(U8("wxWidgets 3.2 + libssh"));
    }

private:
    wxTextCtrl *txtHosts{}, *txtUser{}, *txtPass{}, *txtCmd{}, *txtKey{}, *txtPassphrase{};
    wxSpinCtrl *spinPort{};
    wxChoice   *choiceAuth{};
    wxButton   *btnTest{}, *btnStop{};
    wxListCtrl *list{};
    wxStaticText *statusLbl{};
    std::vector<std::thread> workers;
    std::atomic<bool> cancel{false};

    static std::pair<wxString,int> ParseHost(const wxString& s, int defPort) {
        auto pos = s.Find(':');
        if (pos == wxNOT_FOUND) return {s, defPort};
        long p = defPort;
        s.SubString(pos+1, s.length()-1).ToLong(&p);
        return { s.SubString(0, pos-1), (int)p };
    }

    void OnTest(wxCommandEvent&) {
        cancel.store(false);
        list->DeleteAllItems();
        statusLbl->SetLabel(U8("Testando…"));

        const int defPort = spinPort->GetValue();
        wxString user = txtUser->GetValue();
        wxString pass = txtPass->GetValue();
        wxString cmd  = txtCmd->GetValue();
        wxString auth = choiceAuth->GetStringSelection();
        wxString key  = txtKey->GetValue();
        wxString pph  = txtPassphrase->GetValue();

        std::vector<std::pair<wxString,int>> targets;
        wxStringTokenizer tkz(txtHosts->GetValue(), "\r\n");
        while (tkz.HasMoreTokens()) {
            wxString line = tkz.GetNextToken().Trim(true).Trim(false);
            if (line.empty() || line.StartsWith("#")) continue;
            targets.push_back(ParseHost(line, defPort));
        }
        if (targets.empty()) {
            wxMessageBox(U8("Informe ao menos um host."), U8("Aviso"), wxOK | wxICON_INFORMATION, this);
            statusLbl->SetLabel(U8("Pronto"));
            return;
        }

        for (auto [host, port] : targets) {
            workers.emplace_back([=]() {
                if (cancel.load()) return;
                auto res = RunSSH(host, port, user, pass, cmd, auth, key, pph);
                wxTheApp->CallAfter([=]() {
                    long i = list->InsertItem(list->GetItemCount(), res.host);
                    list->SetItem(i, 1, res.ip);
                    list->SetItem(i, 2, wxString::Format("%d", res.port));
                    list->SetItem(i, 3, res.ok ? U8("✔") : U8("✖"));
                    list->SetItem(i, 4, wxString::Format("%d", res.time_ms));
                    list->SetItem(i, 5, res.auth);
                    list->SetItem(i, 6, res.fingerprint);
                    list->SetItem(i, 7, res.stdout_text.Left(800));
                    list->SetItem(i, 8, res.error);
                });
            });
        }

        std::thread([this]() {
            for (auto& t : workers) if (t.joinable()) t.join();
            workers.clear();
            wxTheApp->CallAfter([=]() { statusLbl->SetLabel(U8("Concluído")); });
        }).detach();
    }

    void OnStop(wxCommandEvent&) {
        cancel.store(true);
        statusLbl->SetLabel(U8("Cancelando…"));
    }
};

// ===== App =====
class MyApp : public wxApp {
public:
    bool OnInit() override {
        if (ssh_init() != SSH_OK) {
            wxMessageBox(U8("Falha ao inicializar libssh"), U8("Erro"), wxOK | wxICON_ERROR);
            return false;
        }
        auto* f = new MainFrame();
        f->Show();
        return true;
    }
    int OnExit() override {
        ssh_finalize();
        return 0;
    }
};

wxIMPLEMENT_APP(MyApp);
