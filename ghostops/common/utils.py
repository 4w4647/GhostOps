from colorama import Fore, Style, init
from datetime import datetime


class Banner:
    BANNER = """
┏┓┓     ┏┓   
┃┓┣┓┏┓┏╋┃┃┏┓┏
┗┛┛┗┗┛┛┗┗┛┣┛┛
          ┛  
"""

    @staticmethod
    def print_banner():
        print(Banner.BANNER)


class Logger:
    _initialized = False

    _LOG_TYPES: dict[str, dict[str, str]] = {
        "good": {"frame": "+", "color": Fore.GREEN},
        "info": {"frame": "*", "color": Fore.CYAN},
        "warn": {"frame": "!", "color": Fore.YELLOW},
        "flaw": {"frame": "-", "color": Fore.RED},
    }

    @staticmethod
    def _ensure_init():
        if not Logger._initialized:
            init(autoreset=True)
            Logger._initialized = True

    @staticmethod
    def log(log_type: str, message: str, *, timestamp: bool = False) -> None:
        log_type = log_type.lower()

        if log_type not in Logger._LOG_TYPES:
            print(f"? {message}")
            return

        frame = Logger._LOG_TYPES[log_type]["frame"]
        color = Logger._LOG_TYPES[log_type]["color"]
        reset = Style.RESET_ALL
        dtime = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] " if timestamp else ""
        )

        print(f"{dtime}{color}{frame}{reset} {message}")


class HexConvert:
    @staticmethod
    def host_to_hex(host: str) -> str:
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
        if not (0 < port < 65536):
            raise ValueError(f"Port must be between 1 and 65535, got {port}")
        return f"{port & 0xFF:02x}{(port >> 8) & 0xFF:02x}"
