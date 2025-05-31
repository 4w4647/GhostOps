from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

CATEGORY_COLORS: dict[str, str] = {
    "scanner": Fore.BLUE,
    "payload": Fore.GREEN,
    "exploit": Fore.RED,
    "evasion": Fore.YELLOW,
    "postexp": Fore.MAGENTA,
}


def get_category_color(category: str) -> str:
    return CATEGORY_COLORS.get(category.lower(), Fore.RESET)


class Logger:
    _LOG_TYPES: dict[str, dict[str, str]] = {
        "good": {"frame": "+", "color": Fore.GREEN},
        "info": {"frame": "*", "color": Fore.CYAN},
        "warn": {"frame": "!", "color": Fore.YELLOW},
        "flaw": {"frame": "-", "color": Fore.RED},
    }

    @staticmethod
    def log(log_type: str, message: str, *, timestamp: bool = False) -> None:
        log_type = log_type.lower()

        if log_type not in Logger._LOG_TYPES:
            print(f"? {message}")
            return

        config = Logger._LOG_TYPES[log_type]
        frame = config["frame"]
        color = config["color"]
        time_str = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] " if timestamp else ""
        )

        print(f"{time_str} {color}{frame}{Style.RESET_ALL} {message}")


def host_to_hex(host):
    return "".join([f"{int(octet):02x}" for octet in host.split(".")][::-1])


def port_to_hex(port):
    port = int(port)
    return f"{port & 0xFF:02x}{(port >> 8) & 0xFF:02x}"
