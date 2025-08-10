#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH Tester v3 — GUI com splash + about + autenticação robusta
- Conecta em SSH, autentica (password / fallback keyboard-interactive), executa comando opcional
- Tela de boas-vindas (splash)
- Exporta resultados em CSV
Requer: paramiko
"""

import os, sys, csv, queue, socket, tempfile, base64, threading, time
from concurrent.futures import ThreadPoolExecutor

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ====== Metadados do app ======
APP_TITLE  = "SSH Tester v3"
VERSION    = "3.0.0"
DATE       = "2025-08-10"
AUTHOR     = "Marcos Silva (Sr. aragonxpd154)"
LICENSE    = "GPL-3.0"

# ====== Ícone e imagens em Base64 ======
# 
ICON_ICO_B64   = b"""AAABAAEAIBUAAAEAIAD8CgAAFgAAACgAAAAgAAAAKgAAAAEAIAAAAAAAgAoAAAAAAAAAAAAAAAAAAAAAAAD7/vz/5+no/9rb2v/g4eD/4uTi/+Lk4v/i5OL/4uTi/+Lj4v/i4+L/4uTj/+Pk4//i4+L/4uTi/+Lj4v/i5OP/4uTj/+Lk4v/i5OL/4uTi/+Pk4v/i5OL/4uTj/+Lk4v/j5OL/4+Tj/+Lk4//i5OL/4uPi/+Lj4v/g4eD/3N3d//f6+P/d397/1tfW/8/Pz//Pz8//z8/P/8/Pz//Pz8//z8/P/8/Pz//Oz8//z8/P/8/Pz//Pz8//z8/P/8/Pz//Pz8//z8/P/8/Pz//Pz8//z8/Q/8/Pz//Pz8//z8/P/8/Pz//Pz9D/z8/P/8/Pz//Pz8//zs/P/9XW1f/h4uH/9fj2/+Pk4//Z2tr/ra2v/6qpq/+qqav/qair/6qpq/+qqav/qqmq/6qpqv+qqav/qqmr/6qpq/+pqar/qqmr/6qpq/+qqav/qair/6qpq/+qqav/qqmr/6qpq/+pqav/qqmr/6qpqv+qqar/qamr/6mpq/+pqKr/urm5/+rr6f/1+Pb/5ebl/9TV1f+op6n/p6ao/6emqP+mpaj/p6ao/6emqP+npqj/pqan/6elqP+npqj/p6ao/6emp/+npqf/p6ao/6emqP+npqj/p6ao/6emqP+npqf/p6ao/6elqP+npqj/p6an/6amp/+mpqf/p6ao/6alp/+ysrL/5ebk//X49//k5uX/1NXV/6ioqf+npqj/p6ao/6alp/+npqj/qKep/6inqf+npqj/pqWo/6emqP+npqj/pqan/6inqP+np6n/qKep/6emqP+npqj/p6ao/6enqP+np6n/p6ao/6enqP+npqj/p6ao/6emqP+npqj/pqWn/7Oys//l5uT/9fj2/+Xm5f/U1dX/qKip/6emqP+op6n/urq7/8vLy//U1NT/1NTU/8nKyv+xsbP/pqWn/6ysrf/FxMT/09PT/9TU1P/T09P/u7u8/6inqf+mpqf/vr69/8nKy/+oqKr/p6ao/6alp/+4uLn/zM3N/6qqrP+mpaf/s7Ky/+Xm5P/1+Pb/5Obl/9TV1f+oqKn/p6an/6inqf/Hx8j/xcXG/8XFxv/Hx8f/1dXU/93e3v+wsLL/sbGx/8rLy//Cw8P/wcHC/8jIyP/g4eD/urq8/6Wkpv/Kycn/293d/6mpq/+np6j/pqWn/8LCwv/g4eH/rKyt/6alp/+zsrP/5ebk//X49//k5uX/09XV/6ioqf+srK3/tra3/8PExP/Hx8f/ycnI/87Pzv/Y2df/6Oro/72+v/+qqqr/qaqq/6mpqv+srK3/tbW2/+Tl5P/ExMX/paSm/8nJyP/b3Nz/qair/6emqP+mpaf/wsLC/9/g4P+srK3/pqWn/7Oys//l5uX/9fj2/+Tl5f/Y2dn/xsbF/9jZ2f/g4eD/4eLi/+Tl5P/j5OP/5ufm/+fo5//f4N//0NHQ/7q7u/+9vL3/0NHR/9vc2//e397/1dfW/7Oztf+lpKb/ycnI/9rc3P+pqKv/p6ao/6alp//CwsL/3+Dg/6yrrf+mpaf/s7Kz/+Xm5P/1+Pf/5ufm/+Lk4//Z2tn/4eLh/+Lj4v/k5eT/6uzq/+vs6//g4eD/1tjX/9PV1P/T1dT/1tfW/+Tl5P/P0ND/vr6+/7W1tf+srK3/qaip/6alp//Jycj/3d/e/6uqrf+mpaj/paSm/8HBwf/f4eD/q6ut/6Wlp/+zsrP/5ebk//b59//q7Or/5Obl/9bX1v/Z2tn/4eLh/+zt7P/t7u3/4eLh/+Dh4P/Y2tj/2dva/9PU0//Z2tj/6Oro/8bGx/+1tbb/uLi4/7e3uP+srKz/qKeo/8nIyP/o6ej/yMnJ/6+vsf+ysrP/09PT/9rb3P+qqqz/pqWo/7Kys//l5uT/9vn4/+vt7P/k5uX/1tfW/9bX1v/Z2tr/4+Xk/+/x7//u8O7/6evp/+rs6v/j5eT/09XT/9bW1f/g4d//5ebl/97g3//a29r/09XV/7CwsP+pqan/ysrJ/9/h4P/Pz8//1NTU/9bW1v/a29v/urq8/6amqP+mpaf/s7Kz/+Xm5P/2+fj/6+3s/+Tm5f/W19b/1tfW/9bX1v/Y2dj/4uLh/+Xm5v/m5+b/5ebl/+Pj4//Y2dj/09TT/9TV0//W19b/1NXU/8HBwf+wsLD/q6ys/6qqqv/Ly8r/2tzc/6qqrP+trK7/rayu/6uqrP+npqj/p6ao/6alp/+zsrP/5ebk//b5+P/r7ez/5Obl/9fX1//W19b/1tfW/9XX1v/b3Nv/3+Df/+Hi4f/i4+L/4uPj/+Lj4v/a3Nr/1NXU/9PV1P/U1dT/0dPS/7y9vf+rq6v/qqqq/8vLyv/b3dz/q6us/6enqP+npqj/p6an/6emqP+npqj/pqWn/7Oys//l5uT/9vn4/+vt7P/m5+f/2NnY/9jZ2P/c3dz/2dva/+Di4P/j5eT/3+Df/+Dh4f/i4+P/4uPi/+Pk4//a29r/1NXT/9TV0//U1dX/0NLQ/7y9vf+rrKz/trW2/7u8vP+sq6z/qamq/6enqP+npqj/p6ao/6enqP+mpqj/s7Kz/+Xm5P/2+fj/6+3s/+jq6f/d3t3/6+3r/+rs6//i5OP/3+Dg//Dy8P/r7ez/3t/f/+Lj4v/i4+L/4uPi/+Lj4v/a3Nv/1NXU/9PV1P/U1dT/09TS/7/Av/+rq6v/qqqq/6urq/+qq6v/qamq/6enqP+npqf/p6ao/6alqP+zsrP/5ebk//b59//r7ez/6erq/9vb2v/d3dz/29zb/9nZ2f/h4uH/4OHg/9rb2v/X2Nf/3t/e/+Lj4v/j5OP/4+Tj/+Pk4//a29v/09XU/9PV0//U1dT/0dPS/76+vv+srKz/q6us/6urq/+rq6v/qKeo/6amqP+npqj/pqWo/7Oys//l5uT/9vn4/+zt7P/p6+r/2drZ/9jZ2f/Y2dj/19jX/9bY1//W1tb/1tfW/9bX1v/X2Nf/3t/e/+Dh4P/i4uH/4uPi/+Hi4v/Z2tn/1tfV/9XW1f/T1dT/0tPT/7y9vf+tra7/ra2t/6qqq/+npqj/pqao/6amqP+lpaj/srKy/+bn5f/4+/n/7/Dv//L08//l5+b/4uPi/+Hj4v/g4eD/3d7d/9na2f/Y2dn/2drZ/9na2f/Y2dj/2dnZ/9zd3P/c3Nz/2tva/9rb2v/Z2tn/2NrZ/9XW1f/U1tT/0tPS/8/Qz//T1NP/xMTF/7/AwP/AwMH/wMDB/7/AwP/Ky8v/5ufm//z//f/3+vj/9Pf1//X39v/19/b/9ff2//P29P/y9fP/7vHu/+zv7f/r7ez/6evp/+fp5//l5uX/4ePi/+Di4P/g4uD/3+Hf/97g3v/g4eD/4OLg/97f3v/e4N7/4OLg/+bo5v/m6Of/5ujn/+bo5//m6Of/5ujn/+bo5//o6uj//f/+//3+/f/6/Pv/+fv6//r7+v/6+/r/+vz7//r8+//7/Pv/+/38//v8/P/7/fv/+/z7//n7+v/5+/r/+fv6//n7+v/5+/r/+fv6//n7+v/5+/r/+fv6//n7+v/5+/r/+vv6//n7+v/5+/r/+vv6//n7+v/5+/r/+fv6//r7+v8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="""       # .ico em base64 (opcional)
ICON_XBM_PATH  = "@/usr/share/pixmaps/ssh-teste-xbm.xbm"  # fallback Linux (opcional)
SPLASH_PNG_B64 = b""""""       # PNG em base64 (opcional) para splash
ABOUT_PNG_B64  = b"""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
"""       # PNG em base64 (opcional) para janela Sobre

# ====== Paramiko (autenticação SSH) ======
try:
    import paramiko
except Exception as e:
    raise SystemExit("Paramiko é obrigatório. Instale com:  pip install paramiko\n\n"+str(e))

# Timeouts razoáveis
CONNECT_TIMEOUT = 12.0
AUTH_TIMEOUT    = 18.0
READ_TIMEOUT    = 12.0
MAX_WORKERS_DEFAULT = 10
DEFAULT_PORT = 22

# ---------- util: gravar icon base64 para arquivo temporário ----------
def set_app_icon(win: tk.Tk | tk.Toplevel):
    # Windows: .ico
    if ICON_ICO_B64:
        try:
            path = os.path.join(tempfile.gettempdir(), "ssh_tester_v3.ico")
            if not os.path.exists(path):
                with open(path, "wb") as f:
                    f.write(base64.b64decode(ICON_ICO_B64))
            win.iconbitmap(path)
            return
        except Exception:
            pass
    # Linux XBM (se existir)
    try:
        if ICON_XBM_PATH and os.path.exists(ICON_XBM_PATH.replace("@","")):
            win.iconbitmap(ICON_XBM_PATH)
    except Exception:
        pass

# ---------- Splash Screen ----------
class Splash(tk.Toplevel):
    def __init__(self, master, timeout_ms=2000):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        frm = ttk.Frame(self, padding=18)
        frm.pack(fill="both", expand=True)

        img_lbl = None
        if SPLASH_PNG_B64:
            try:
                import tkinter as tk_
                img_data = base64.b64decode(SPLASH_PNG_B64)
                self._splash_img = tk_.PhotoImage(data=img_data)
                img_lbl = ttk.Label(frm, image=self._splash_img)
                img_lbl.pack()
            except Exception:
                pass

        ttk.Label(frm, text=APP_TITLE, font=("Segoe UI", 16, "bold")).pack(pady=(8, 2))
        ttk.Label(frm, text=f"Versão {VERSION}  •  {LICENSE}", foreground="#777").pack()
        ttk.Label(frm, text="Inicializando…", foreground="#555").pack(pady=(6, 0))
        self.update_idletasks()

        # centraliza
        w, h = 420, 220
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        set_app_icon(self)

        # fecha em timeout
        self.after(timeout_ms, self.destroy)

# ---------- Carregar chave privada (opcional) ----------
def load_pkey(path: str, passphrase: str | None):
    loaders = (
        paramiko.RSAKey.from_private_key_file,
        paramiko.ECDSAKey.from_private_key_file,
        paramiko.Ed25519Key.from_private_key_file,
        paramiko.DSSKey.from_private_key_file,
    )
    last = None
    for L in loaders:
        try:
            return L(path, password=passphrase or None)
        except Exception as e:
            last = e
    raise last or RuntimeError("Falha ao carregar chave privada.")

# ---------- Autenticação (prioriza Transport.auth_password) ----------
from paramiko import AuthenticationException, SSHException

def try_auth_with_fallback(host, port, username, password, pkey_obj,
                           accept_unknown_hostkey, verify_command, kbi_enable):
    """
    Retorna: ok, latency_ms, banner, fingerprint, auth_method, stdout, stderr
    """
    banner = fingerprint = auth_method = ""
    cmd_out = cmd_err = ""
    ok = False
    latency_ms = None

    t0 = time.perf_counter()
    # TCP
    sock = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT)
    tr = paramiko.Transport(sock)
    tr.start_client(timeout=READ_TIMEOUT)

    # banner/fingerprint
    try:
        b = tr.get_banner()
        banner = b if isinstance(b, str) else (b.decode(errors="ignore") if b else "")
    except Exception:
        banner = ""
    try:
        key = tr.get_remote_server_key()
        fingerprint = key.get_base64()
    except Exception:
        fingerprint = ""

    # política de host key (simples): se não aceita desconhecida e não há fingerprint, aborta
    if not accept_unknown_hostkey and not fingerprint:
        tr.close()
        raise SSHException("Host key desconhecida (AutoAddPolicy desativado)")

    # 1) password direto (comportamento que resolveu seu caso)
    try:
        if username:
            tr.auth_password(username, password or "")
            latency_ms = int((time.perf_counter() - t0) * 1000)
            auth_method = "password"
            ok = True
    except AuthenticationException as e:
        allowed = getattr(e, "allowed_types", []) or []
        # 2) fallback: keyboard-interactive com mesma senha
        if kbi_enable and ("keyboard-interactive" in allowed) and password:
            try:
                tr.auth_interactive_dumb(username, password)
                latency_ms = int((time.perf_counter() - t0) * 1000)
                auth_method = "keyboard-interactive"
                ok = True
            except Exception:
                tr.close()
                raise
        else:
            tr.close()
            raise
    except Exception:
        tr.close()
        raise

    # comando opcional
    if ok and verify_command:
        chan = tr.open_session(timeout=READ_TIMEOUT)
        chan.exec_command(verify_command)
        try:
            cmd_out = chan.makefile("r", -1).read().decode(errors="ignore").strip()
            cmd_err = chan.makefile_stderr("r", -1).read().decode(errors="ignore").strip()
        finally:
            chan.close()

    tr.close()
    return ok, latency_ms, banner, fingerprint, auth_method, cmd_out, cmd_err

# ---------- Worker ----------
def test_ssh_host(host, port, username, password, pkey_path, passphrase,
                  accept_unknown_hostkey, verify_command, kbi_enable):
    started = time.perf_counter()
    try:
        ip = socket.gethostbyname(host)
    except Exception:
        ip = ""

    result = {
        "host": host, "ip": ip, "port": port,
        "ok": False, "latency_ms": "", "time_ms": 0,
        "banner": "", "fingerprint": "", "auth_method": "",
        "cmd_stdout": "", "cmd_stderr": "", "error": ""
    }

    try:
        pkey_obj = load_pkey(pkey_path, passphrase) if pkey_path else None
        ok, lat, ban, fp, method, out, err = try_auth_with_fallback(
            host, port, (username or "").strip(), (password or ""),
            pkey_obj, accept_unknown_hostkey, (verify_command or ""), kbi_enable
        )
        result.update({
            "ok": ok, "latency_ms": lat, "banner": ban,
            "fingerprint": fp, "auth_method": method,
            "cmd_stdout": out, "cmd_stderr": err
        })
    except AuthenticationException as e:
        result["error"] = f"Auth falhou: {e}"
    except socket.timeout:
        result["error"] = "Timeout de conexão"
    except Exception as e:
        result["error"] = str(e)
    finally:
        result["time_ms"] = int((time.perf_counter() - started) * 1000)
    return result

# ---------- Janela Sobre ----------
class AboutWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Sobre")
        set_app_icon(self)
        self.resizable(False, False)
        frm = ttk.Frame(self, padding=14)
        frm.pack(fill="both", expand=True)

        if ABOUT_PNG_B64:
            try:
                self._img = tk.PhotoImage(data=base64.b64decode(ABOUT_PNG_B64))
                ttk.Label(frm, image=self._img).pack()
            except Exception:
                pass

        ttk.Label(frm, text=APP_TITLE, font=("Segoe UI", 14, "bold")).pack(pady=(6,2))
        ttk.Label(frm, text=f"Versão {VERSION} — {DATE}").pack()
        ttk.Label(frm, text=f"Autor: {AUTHOR}").pack()
        ttk.Label(frm, text=f"Licença: {LICENSE}", foreground="#666").pack(pady=(0,8))
        ttk.Separator(frm).pack(fill="x", pady=8)
        ttk.Label(frm, justify="left",
                  text="Ferramenta para testar conectividade e autenticação SSH "
                       "(password / keyboard-interactive) e executar um comando de verificação."
                  ).pack()
        ttk.Button(frm, text="OK", command=self.destroy).pack(pady=(12,0))

        self.update_idletasks()
        w, h = 460, 360
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

# ---------- App Principal ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1000x640")
        self.minsize(980, 600)
        set_app_icon(self)

        # Splash (não modal)
        try:
            self.withdraw()
            s = Splash(self, timeout_ms=1800)
            self.after(1850, self.deiconify)
        except Exception:
            self.deiconify()

        # Estado
        self.q = queue.Queue()
        self.executor: ThreadPoolExecutor | None = None
        self.futures = []
        self.stop_flag = threading.Event()

        self.var_port = tk.IntVar(value=DEFAULT_PORT)
        self.var_workers = tk.IntVar(value=MAX_WORKERS_DEFAULT)
        self.var_username = tk.StringVar(value="")
        self.var_password = tk.StringVar(value="")
        self.var_key = tk.StringVar(value="")
        self.var_passphrase = tk.StringVar(value="")
        self.var_accept_unknown = tk.BooleanVar(value=True)
        self.var_kbi = tk.BooleanVar(value=True)
        self.var_cmd = tk.StringVar(value="")
        self.var_filter = tk.StringVar(value="")
        self.var_status = tk.StringVar(value="Pronto")

        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        # Menu
        menubar = tk.Menu(self)
        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Importar lista…", command=self.on_import)
        m_file.add_command(label="Exportar CSV…", command=self.on_export)
        m_file.add_separator()
        m_file.add_command(label="Sair", command=self.destroy)
        menubar.add_cascade(label="Arquivo", menu=m_file)

        m_help = tk.Menu(menubar, tearoff=0)
        m_help.add_command(label="Sobre", command=lambda: AboutWindow(self))
        menubar.add_cascade(label="Ajuda", menu=m_help)
        self.config(menu=menubar)

        # Hosts
        top = ttk.Frame(self, padding=10); top.pack(fill="x")
        ttk.Label(top, text="Hosts (um por linha; aceita host ou host:porta):").grid(row=0, column=0, sticky="w")
        self.txt_hosts = tk.Text(top, height=6)
        self.txt_hosts.grid(row=1, column=0, columnspan=7, sticky="nsew", pady=(4,8))
        top.grid_columnconfigure(6, weight=1)
        scr = ttk.Scrollbar(top, orient="vertical", command=self.txt_hosts.yview)
        self.txt_hosts.configure(yscrollcommand=scr.set)
        scr.grid(row=1, column=7, sticky="ns", pady=(4,8))

        # Credenciais
        cred = ttk.LabelFrame(self, text="Autenticação", padding=10)
        cred.pack(fill="x", padx=10)
        ttk.Label(cred, text="Usuário:").grid(row=0, column=0, sticky="w")
        ttk.Entry(cred, textvariable=self.var_username, width=20).grid(row=0, column=1, sticky="w", padx=(4,12))
        ttk.Label(cred, text="Senha:").grid(row=0, column=2, sticky="w")
        ttk.Entry(cred, textvariable=self.var_password, show="•", width=20).grid(row=0, column=3, sticky="w", padx=(4,12))
        ttk.Label(cred, text="Chave privada:").grid(row=1, column=0, sticky="w", pady=(8,0))
        ttk.Entry(cred, textvariable=self.var_key, width=40).grid(row=1, column=1, columnspan=2, sticky="w", pady=(8,0))
        ttk.Button(cred, text="Selecionar…", command=self._choose_key).grid(row=1, column=3, sticky="w", pady=(8,0))
        ttk.Label(cred, text="Passphrase:").grid(row=1, column=4, sticky="w", pady=(8,0))
        ttk.Entry(cred, textvariable=self.var_passphrase, show="•", width=18).grid(row=1, column=5, sticky="w", pady=(8,0))
        ttk.Checkbutton(cred, text="Aceitar host key desconhecida (AutoAddPolicy)", variable=self.var_accept_unknown).grid(row=2, column=0, columnspan=6, sticky="w", pady=(8,0))
        ttk.Checkbutton(cred, text="Tentar keyboard-interactive (fallback)", variable=self.var_kbi).grid(row=3, column=0, columnspan=6, sticky="w")

        # Opções
        opts = ttk.LabelFrame(self, text="Opções de teste", padding=10)
        opts.pack(fill="x", padx=10, pady=(8,0))
        ttk.Label(opts, text="Porta padrão:").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(opts, from_=1, to=65535, textvariable=self.var_port, width=6).grid(row=0, column=1, sticky="w", padx=(4,16))
        ttk.Label(opts, text="Workers:").grid(row=0, column=2, sticky="w")
        ttk.Spinbox(opts, from_=1, to=200, textvariable=self.var_workers, width=6).grid(row=0, column=3, sticky="w", padx=(4,16))
        ttk.Label(opts, text="Comando pós-login (opcional):").grid(row=0, column=4, sticky="w")
        ttk.Entry(opts, textvariable=self.var_cmd, width=32).grid(row=0, column=5, sticky="w", padx=(4,0))
        ttk.Button(opts, text="Testar", command=self.on_test).grid(row=0, column=6, sticky="e", padx=(10,0))
        ttk.Button(opts, text="Parar", command=self.on_stop).grid(row=0, column=7, sticky="w")

        # Filtro/IO
        io = ttk.Frame(self, padding=(10,6,10,0)); io.pack(fill="x")
        ttk.Label(io, text="Filtro:").pack(side="left")
        ent_filter = ttk.Entry(io, textvariable=self.var_filter, width=40)
        ent_filter.pack(side="left", padx=(4,10))
        self.var_filter.trace_add("write", lambda *_: self._apply_filter())
        ttk.Button(io, text="Importar lista…", command=self.on_import).pack(side="left")
        ttk.Button(io, text="Exportar CSV…", command=self.on_export).pack(side="left", padx=(6,0))
        ttk.Button(io, text="Sobre", command=lambda: AboutWindow(self)).pack(side="right")

        # Tabela
        table = ttk.Frame(self, padding=10); table.pack(expand=True, fill="both")
        cols = ("host","ip","port","ok","latency_ms","time_ms","auth_method","banner","fingerprint","cmd_stdout","cmd_stderr","error")
        headers = {"host":"Host","ip":"IP","port":"Porta","ok":"OK","latency_ms":"Latência (ms)","time_ms":"Total (ms)","auth_method":"Auth","banner":"Banner","fingerprint":"Fingerprint","cmd_stdout":"STDOUT","cmd_stderr":"STDERR","error":"Erro"}
        widths  = {"host":160,"ip":140,"port":60,"ok":50,"latency_ms":100,"time_ms":90,"auth_method":120,"banner":240,"fingerprint":240,"cmd_stdout":260,"cmd_stderr":220,"error":260}
        self.tree = ttk.Treeview(table, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.pack(side="left", expand=True, fill="both")
        scr2 = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scr2.set); scr2.pack(side="right", fill="y")

        # Status
        status = ttk.Frame(self, padding=(10,4)); status.pack(fill="x")
        self.progress = ttk.Progressbar(status, mode="indeterminate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(0,8))
        ttk.Label(status, textvariable=self.var_status).pack(side="right")

    # ----- Ações UI -----
    def _choose_key(self):
        p = filedialog.askopenfilename(title="Selecionar chave privada",
                                       filetypes=[("Chaves SSH","*.pem *.key *id_rsa *id_ecdsa *id_ed25519 *id_dsa *id_dss *"), ("Todos","*.*")])
        if p: self.var_key.set(p)

    def on_import(self):
        p = filedialog.askopenfilename(title="Importar lista",
                                       filetypes=[("Texto","*.txt *.list *.cfg *.conf"), ("Todos","*.*")])
        if not p: return
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            self.txt_hosts.delete("1.0","end")
            self.txt_hosts.insert("1.0", f.read())

    def on_export(self):
        p = filedialog.asksaveasfilename(title="Exportar CSV", defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not p: return
        rows = [self.tree.item(i,"values") for i in self.tree.get_children("")]
        cols = ("host","ip","port","ok","latency_ms","time_ms","auth_method","banner","fingerprint","cmd_stdout","cmd_stderr","error")
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(cols); w.writerows(rows)
        messagebox.showinfo("Exportado", f"Salvo em:\n{p}")

    def on_test(self):
        raw = self.txt_hosts.get("1.0","end").strip()
        if not raw:
            messagebox.showwarning("Aviso","Informe ao menos um host.")
            return
        default_port = self.var_port.get()
        targets = []
        for line in raw.splitlines():
            s = line.strip()
            if not s or s.startswith("#"): continue
            if ":" in s:
                h, p = s.rsplit(":",1)
                try: targets.append((h.strip(), int(p)))
                except: targets.append((h.strip(), default_port))
            else:
                targets.append((s, default_port))

        # Limpa resultados
        for iid in self.tree.get_children(""): self.tree.delete(iid)

        self.stop_flag.clear()
        self.var_status.set(f"Testando {len(targets)} host(s)…")
        self.progress.start(100)

        uname = self.var_username.get().strip() or None
        pwd   = self.var_password.get() or ""
        key   = self.var_key.get().strip() or None
        pph   = self.var_passphrase.get() or None
        acc   = self.var_accept_unknown.get()
        cmd   = self.var_cmd.get().strip() or ""
        kbi   = self.var_kbi.get()

        maxw  = max(1, min(200, int(self.var_workers.get())))
        self.executor = ThreadPoolExecutor(max_workers=maxw)
        self.futures.clear()

        def submit_all():
            for host, port in targets:
                if self.stop_flag.is_set(): break
                fut = self.executor.submit(
                    test_ssh_host, host, port, uname, pwd, key, pph, acc, cmd, kbi
                )
                fut.add_done_callback(lambda f: self.q.put(f.result()))
                self.futures.append(fut)
            threading.Thread(target=self._wait_all, daemon=True).start()

        threading.Thread(target=submit_all, daemon=True).start()

    def _wait_all(self):
        for f in self.futures:
            try: f.result()
            except Exception: pass
        if self.executor:
            self.executor.shutdown(wait=False); self.executor = None
        self.futures.clear(); self.stop_flag.clear()
        self.after(0, self._finish)

    def _finish(self):
        self.progress.stop(); self.var_status.set("Concluído")

    def on_stop(self):
        self.stop_flag.set(); self.var_status.set("Cancelando…")
        if self.executor:
            self.executor.shutdown(wait=False); self.executor=None
        self.progress.stop()

    def _poll_queue(self):
        try:
            while True:
                r = self.q.get_nowait()
                self._insert_row(r)
        except queue.Empty:
            pass
        finally:
            self.after(120, self._poll_queue)

    def _insert_row(self, r: dict):
        vals = (
            r.get("host",""), r.get("ip",""), r.get("port",""),
            "✔" if r.get("ok") else "✖",
            r.get("latency_ms",""), r.get("time_ms",""),
            r.get("auth_method",""), r.get("banner",""), r.get("fingerprint",""),
            (r.get("cmd_stdout","") or "")[:300],
            (r.get("cmd_stderr","") or "")[:200],
            r.get("error",""),
        )
        self.tree.insert("", "end", values=vals)
        self._apply_filter()

    def _apply_filter(self):
        needle = self.var_filter.get().lower().strip()
        for iid in self.tree.get_children(""):
            text = " ".join(str(v) for v in self.tree.item(iid,"values")).lower()
            if needle and needle not in text:
                self.tree.detach(iid)
            else:
                self.tree.reattach(iid, "", "end")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
