from abc import ABC, abstractmethod
from argparse import ArgumentParser
from colorama import Style
from ghostops.core.utils import get_category_color


class BaseModule(ABC):
    """
    Abstract Base Class for all GhostOps modules.

    Each module must inherit from BaseModule and implement:
    - `main(args)`: The execution logic
    - `add_arguments(parser)`: Defines CLI arguments

    Metadata fields should be defined in each subclass.
    """

    # Module metadata (should be set in subclasses)
    module_name: str = None  # Unique name of the module
    module_description: str = None  # Brief description of functionality
    module_author: str = None  # Author name and contact
    module_category: str = None  # Module category (e.g., payload, postexp)
    module_target_os: list[str] = []  # Supported OS types (e.g., ["windows", "linux"])
    module_target_architecture: list[str] = (
        []
    )  # Supported architectures (e.g., ["x86", "x64"])

    @staticmethod
    @abstractmethod
    def main(args) -> None:
        """
        Entry point for the module's execution.
        Must be implemented by the subclass.

        Args:
            args: Parsed command-line arguments.

        Returns:
            None
        """
        pass

    @staticmethod
    @abstractmethod
    def add_arguments(parser: ArgumentParser) -> None:
        """
        Adds command-line arguments specific to the module.
        Must be implemented by the subclass.

        Args:
            parser (ArgumentParser): An instance of argparse.ArgumentParser.

        Returns:
            None
        """
        pass

    @classmethod
    def show_info(cls) -> None:
        """
        Displays module metadata in a formatted and colorized output.
        Useful for interactive module listings or help menus.

        Returns:
            None
        """
        category_color = get_category_color(cls.module_category or "")
        label_style = Style.BRIGHT
        reset = Style.RESET_ALL

        print(f"{label_style}Name        - {reset}{cls.module_name or '<missing>'}")
        print(
            f"{label_style}Description - {reset}{cls.module_description or '<missing>'}"
        )
        print(f"{label_style}Author      - {reset}{cls.module_author or '<missing>'}")
        print(
            f"{label_style}Category    - {reset}{category_color}{cls.module_category or '<missing>'}{reset}"
        )
        print(
            f"{label_style}Target OS   - {reset}{', '.join(cls.module_target_os) or '<missing>'}"
        )
        print(
            f"{label_style}Target Arch - {reset}{', '.join(cls.module_target_architecture) or '<missing>'}"
        )
        print()
