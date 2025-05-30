import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from ghostops.core.module_base import BaseModule
from ghostops.core.utils import Logger

class TcpPortScanner(BaseModule):
    module_name = "TcpPortScanner"
    module_description = "Scans open TCP ports using pure Python sockets."
    module_author = "Awagat Dhungana <4w46747@gmail.com>"
    module_category = "scanner"
    module_target_os = ["generic"]
    module_target_architecture = ["generic"]

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("--host", required=True, help="Target hostname or IP address")
        parser.add_argument("--port", required=True, help="Ports to scan (e.g. 22,80,443 or 1-1024)")
        parser.add_argument("--threads", required=True, type=int, help="Number of concurrent threads")

    @staticmethod
    def main(args):
        Logger.log("info", f"HOST     - {args.host}")
        Logger.log("info", f"PORT     - {args.port}")
        Logger.log("info", f"THREADS  - {args.threads}")
        print()

        ports = TcpPortScanner.parse_ports(args.port)
        open_ports = TcpPortScanner.scan_tcp(args.host, ports, args.threads)

        if open_ports:
            print(f"Open ports (TCP):")
            for port in sorted(open_ports):
                print(f"  - {port}")
            print()
            Logger.log("good", f"Total {len(open_ports)} open port(s)")
        else:
            Logger.log("warn", "No open ports detected.")

    @staticmethod
    def parse_ports(port_str):
        ports = set()
        for part in port_str.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                ports.update(range(start, end + 1))
            else:
                ports.add(int(part))
        return ports

    @staticmethod
    def scan_tcp(host, ports, threads):
        open_ports = []

        def scan(port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    if sock.connect_ex((host, port)) == 0:
                        return port
            except socket.error as e:
                Logger.log("flaw", f"TCP error on port {port}: {e}")
            return None

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(scan, port): port for port in ports}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    open_ports.append(result)

        return open_ports