from abc import ABC, abstractmethod
from colorama import Style
from ghostops.core.utils import get_category_color


class BaseModule(ABC):
    module_name: str = None
    module_description: str = None
    module_author: str = None
    module_category: str = None
    module_target_os: list = []
    module_target_architecture: list = []

    @staticmethod
    @abstractmethod
    def main(args):
        pass

    @staticmethod
    @abstractmethod
    def add_arguments(parser):
        pass

    @classmethod
    def show_info(cls):
        category_color = get_category_color(cls.module_category or "")
        neutral = Style.BRIGHT

        print(
            f"{neutral}Name        - {Style.RESET_ALL}{cls.module_name or '<missing>'}"
        )
        print(
            f"{neutral}Description - {Style.RESET_ALL}{cls.module_description or '<missing>'}"
        )
        print(
            f"{neutral}Author      - {Style.RESET_ALL}{cls.module_author or '<missing>'}"
        )
        print(
            f"{neutral}Category    - {Style.RESET_ALL}{category_color}{cls.module_category or '<missing>'}{Style.RESET_ALL}"
        )
        print(
            f"{neutral}Target OS   - {Style.RESET_ALL}{', '.join(cls.module_target_os) or '<missing>'}"
        )
        print(
            f"{neutral}Target Arch - {Style.RESET_ALL}{', '.join(cls.module_target_architecture) or '<missing>'}"
        )
        print()
