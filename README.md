# 👻 GhostOps - Command & Control Framework

**GhostOps** is a modular Command & Control (C2) framework for adversary simulation, red teaming, and offensive security operations. It is designed to be simple, extensible, and powerful — supporting multiple OS and architectures through clearly defined modules.

---
![image](https://github.com/user-attachments/assets/be2b4052-d7fa-442e-b991-9a745352c4d3)

## 📁 Project Structure

```
ghostops/
├── core/
│   ├── module_base.py
│   └── utils.py
├── ghostops.py
├── modules/
│   ├── evasion/
│   ├── exploit/
│   ├── handler/
│   ├── payload/
│   ├── postexp/
│   ├── scanner/
│   └── execute/
│
├── LICENSE
├── poetry.lock
├── pyproject.toml
└── README.md
```

---

## 🚀 Getting Started

### 📦 Installation

> Python 3.8+ is required. Use a virtual environment.
```bash
sudo apt install mingw-w64 -y
```

```bash
git clone https://github.com/4w4647/ghostops.git
cd ghostops
poetry install
```

### ▶️ Listing Modules

```bash
poetry run ghostops list
```

### ▶️ Running a Module

```bash
poetry run ghostops module module_name
```

---

## 🧩 Writing Your Own Module

Modules in GhostOps inherit from `BaseModule`, and must implement:

- Metadata: name, description, author, etc.
- `add_arguments()` method for CLI arguments
- `main()` method for logic

---

### ✅ Minimal Example — Hello World Module

This is the simplest working module:

```python
# File: ghostops/modules/examples/hello_world.py

from ghostops.core.module_base import BaseModule
from ghostops.core.utils import Logger
import argparse

class HelloWorld(BaseModule):
    module_name = "HelloWorld"
    module_description = "Prints Hello, World! using Logger."
    module_author = "Your Name <your@email.com>"
    module_category = "examples"
    module_target_os = ["windows", "linux"]
    module_target_architecture = ["x86", "x64"]

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        pass  # No arguments needed for this simple example

    @staticmethod
    def main(args):
        Logger.log("info", "Hello, World!")
```

---

## 📂 Adding Your Module

1. Choose the correct category folder (e.g., `payload`, `postexp`, etc.)
2. Create your module Python file
3. Inherit from `BaseModule`
4. Define required metadata and logic
5. Test it via the CLI

---

## 🤝 Contributing

Pull requests are welcome!

### How to contribute:

1. Fork the repo
2. Create a new branch (`feature/my-new-module`)
3. Add your module and test it
4. Push your branch
5. **Create a pull request targeting the `main` branch**

---

## 📜 License

This project is licensed under the [BSD 3-Clause](LICENSE).

---

## ⚠️ Disclaimer

GhostOps is intended **strictly for authorized use in red teaming, security research, and education**. Unauthorized or malicious use is strictly prohibited.

---

## 📫 Contact

**Maintainer:** Awagat Dhungana  
📧 [4w4647@gmail.com](mailto:4w4647@gmail.com)
