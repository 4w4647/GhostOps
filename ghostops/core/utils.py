from datetime import datetime
from colorama import Fore, Style, init

# Automatically reset color after each print
init(autoreset=True)

# Mapping of module categories to terminal colors
CATEGORY_COLORS: dict[str, str] = {
    "scanner": Fore.CYAN,
    "payload": Fore.GREEN,
    "exploit": Fore.RED,
    "evasion": Fore.YELLOW,
    "postexp": Fore.MAGENTA,
    "handler": Fore.LIGHTBLUE_EX,
}


def get_category_color(category: str) -> str:
    """
    Returns the color associated with a given module category.

    Args:
        category (str): The module category (e.g., "payload", "scanner")

    Returns:
        str: A colorama color string, defaulting to reset if unknown
    """
    return CATEGORY_COLORS.get(category.lower(), Fore.RESET)


class Logger:
    """
    Logger class for colorized terminal output based on log type.
    Supports 'good', 'info', 'warn', and 'flaw' log types.
    """

    _LOG_TYPES: dict[str, dict[str, str]] = {
        "good": {"frame": "+", "color": Fore.GREEN},
        "info": {"frame": "*", "color": Fore.CYAN},
        "warn": {"frame": "!", "color": Fore.YELLOW},
        "flaw": {"frame": "-", "color": Fore.RED},
    }

    @staticmethod
    def log(log_type: str, message: str, *, timestamp: bool = False) -> None:
        """
        Print a formatted, colorized log message to the console.

        Args:
            log_type (str): One of 'good', 'info', 'warn', 'flaw'
            message (str): The message to display
            timestamp (bool, optional): Whether to prefix the message with a timestamp
        """
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

        print(f"{time_str}{color}{frame}{Style.RESET_ALL} {message}")


def host_to_hex(host: str) -> str:
    """
    Convert an IPv4 address to its hexadecimal representation (reversed).

    Args:
        host (str): An IPv4 address (e.g., "192.168.0.1")

    Returns:
        str: Reversed hexadecimal string (e.g., "0100a8c0")
    """
    return "".join([f"{int(octet):02x}" for octet in host.split(".")][::-1])


def port_to_hex(port: int | str) -> str:
    """
    Convert a port number to its hexadecimal representation (little endian).

    Args:
        port (int | str): The port number

    Returns:
        str: Hexadecimal string (e.g., "5000" for port 80)
    """
    port = int(port)
    return f"{port & 0xFF:02x}{(port >> 8) & 0xFF:02x}"
