<h1 align="center">
<img alt="" src="https://i.imgur.com/YOUR_LOGO.png"/>
<br>
SSH Tester
</h1>

<h4 align="center">

O **SSH Tester** é uma aplicação para testar conexões SSH de forma simples e rápida.  
Possui versões em **C++** (usando wxWidgets + libssh) e **Python** (usando Tkinter + Paramiko).  
Permite autenticação com usuário e senha, execução de comandos pós-login e exibição dos resultados em interface gráfica.

</h4>

<p align="center">
<img alt="Github language count" src="https://img.shields.io/github/languages/count/aragonxpd154/SSH-Tester">
<img alt="Repository size" src="https://img.shields.io/github/repo-size/aragonxpd154/SSH-Tester">
<img alt="Github last commit" src="https://img.shields.io/github/last-commit/aragonxpd154/SSH-Tester">
<a href="https://github.com/aragonxpd154/SSH-Tester/issues">
<img alt="Repository issues" src="https://img.shields.io/github/issues/aragonxpd154/SSH-Tester"> 
</a>
<img alt="Github license" src="https://img.shields.io/github/license/aragonxpd154/SSH-Tester">
</p>

<p align="center">
<a href="#rocket-technologies">Technologies</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
<a href="#information_source-how-to-use">How To Use</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
<a href="#ssh-features">Features</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
<a href="#status">Development Status</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
<a href="#memo-license">License</a>
</p>

<p align="center">
<img alt="SSH Tester Screenshot" src="https://github.com/aragonxpd154/SSH-Tester/blob/master/screenshot.png">
</p>

---

## :rocket: Technologies

O projeto conta com duas implementações:

### **Versão C++**
- [C++17](https://isocpp.org/)
- [wxWidgets 3.2](https://www.wxwidgets.org/)
- [libssh](https://www.libssh.org/)
- [MinGW-w64](http://mingw-w64.org/)

### **Versão Python**
- [Python 3.x](https://www.python.org/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html)
- [Paramiko](http://www.paramiko.org/)

---

## :information_source: How To Use

### **Compilar e executar (C++)**

```bash
# Clonar repositório
git clone https://github.com/aragonxpd154/SSH-Tester
cd SSH-Tester/cpp_version

# Compilar no MinGW
g++ main.cpp -o ssh_tester.exe \
  -std=gnu++17 -DUNICODE -D_UNICODE \
  `wx-config --cxxflags --libs std,net` \
  -lssh -lws2_32 -lcrypt32 -lz

# Executar
./ssh_tester.exe
````
```bash
# Clonar repositório
git clone https://github.com/aragonxpd154/SSH-Tester
cd SSH-Tester/python_version

# Instalar dependências
pip install paramiko

# Executar
python ssh_tester.py
````
## :computer: SSH Features
    Lista de Hosts — Campo para inserir múltiplos servidores (host ou host:porta).
    Usuário e Senha — Campos para autenticação.
    Porta padrão — 22 por padrão, ajustável.
    Comando pós-login — Comando a ser executado automaticamente após autenticação.
    Tabela de Resultados — Mostra host, IP, status, tempo de resposta, fingerprint e STDOUT.
    Botão Testar — Inicia testes.
    Botão Parar — Interrompe testes em andamento.

:memo: License

Este projeto está sob a licença GPL v3.0 — veja o arquivo LICENSE.



