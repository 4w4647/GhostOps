import os
import importlib
import inspect
import argparse
from colorama import Style
from ghostops.core.utils import get_category_color, Logger
from ghostops.core.module_base import BaseModule


class GhostOps:
    BASE_DIR = "ghostops/modules"
    PREFIX = "ghostops.modules"

    @staticmethod
    def print_banner():
        print(
            """
┏┓┓     ┏┓   
┃┓┣┓┏┓┏╋┃┃┏┓┏
┗┛┛┗┗┛┛┗┗┛┣┛┛
          ┛  
"""
        )

    def __init__(self):
        self.modules = []

    def discover_modules(self):
        for root, _, files in os.walk(self.BASE_DIR):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    rel_path = os.path.relpath(
                        os.path.join(root, file), start=os.getcwd()
                    )
                    mod_path = rel_path.replace(os.sep, ".").rsplit(".", 1)[0]
                    if mod_path.startswith(self.PREFIX):
                        self.modules.append(mod_path)
        return self.modules

    @staticmethod
    def snake_to_pascal(snake_str):
        return "".join(word.capitalize() for word in snake_str.split("_"))

    def load_modules(self):
        required_metadata = [
            "module_name",
            "module_description",
            "module_author",
            "module_category",
            "module_target_os",
            "module_target_architecture",
        ]
        loaded = []

        for mod in self.modules:
            try:
                module = importlib.import_module(mod)
                filename = mod.rsplit(".", 1)[-1]
                expected_classname = self.snake_to_pascal(filename)

                classes = [
                    cls
                    for _, cls in inspect.getmembers(module, inspect.isclass)
                    if cls.__module__ == mod and cls.__name__ == expected_classname
                ]

                if not classes:
                    raise ImportError(
                        f"Expected class '{expected_classname}' not found in module {mod}"
                    )

                module_class = classes[0]

                if not issubclass(module_class, BaseModule):
                    raise ImportError(
                        f"Class {module_class.__name__} must inherit from BaseModule"
                    )

                missing = [
                    field
                    for field in required_metadata
                    if not hasattr(module_class, field)
                ]
                if missing:
                    raise ImportError(
                        f"Class {module_class.__name__} missing metadata: {', '.join(missing)}"
                    )

                if not hasattr(module_class, "main") or not callable(
                    getattr(module_class, "main")
                ):
                    raise ImportError(
                        f"Class {module_class.__name__} missing callable 'main' method"
                    )

                loaded.append((mod, module_class))

            except Exception as e:
                Logger.log("flaw", f"Failed to load {mod}: {e}")

        return loaded

    def load(self):
        self.discover_modules()
        return self.load_modules()

    def list_modules(self, category_filter=None, os_filter=None, arch_filter=None):
        found = False

        for _, module_class in self.load():
            category = getattr(module_class, "module_category", "").lower()
            os_list = [o.lower() for o in getattr(module_class, "module_target_os", [])]
            arch_list = [
                a.lower()
                for a in getattr(module_class, "module_target_architecture", [])
            ]

            if category_filter and category != category_filter.lower():
                continue
            if os_filter and os_filter.lower() not in os_list:
                continue
            if arch_filter and arch_filter.lower() not in arch_list:
                continue

            found = True

            module_class.show_info()

        if not found:
            Logger.log("warn", "No modules matched the given filters.")

    def get_module_by_name(self, name: str):
        for mod_path, module_class in self.load():
            class_name = module_class.__name__.lower()
            file_name = mod_path.rsplit(".", 1)[-1].lower()
            if name.lower() == class_name or name.lower() == file_name:
                return mod_path, module_class
        return None, None


def main():
    GhostOps.print_banner()

    parser = argparse.ArgumentParser(
        description="GhostOps - Command and Control Framework."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    list_parser = subparsers.add_parser("list", help="List available modules")
    list_parser.add_argument("--category", type=str, help="Filter by category")
    list_parser.add_argument("--os", type=str, help="Filter by target OS")
    list_parser.add_argument("--arch", type=str, help="Filter by architecture")

    module_parser = subparsers.add_parser(
        "module", help="Execute or inspect a specific module"
    )
    module_parser.add_argument("module_name", help="Module class or filename")
    module_parser.add_argument(
        "module_args", nargs=argparse.REMAINDER, help=argparse.SUPPRESS
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    ghostops = GhostOps()

    if args.command == "list":
        ghostops.list_modules(
            category_filter=args.category, os_filter=args.os, arch_filter=args.arch
        )
        return

    if args.command == "module":
        _, module_class = ghostops.get_module_by_name(args.module_name)

        if not module_class:
            Logger.log("flaw", f"Module '{args.module_name}' not found.")
            return

        module_class.show_info()

        module_arg_parser = argparse.ArgumentParser(prog=args.module_name)
        if hasattr(module_class, "add_arguments") and callable(
            getattr(module_class, "add_arguments")
        ):
            module_class.add_arguments(module_arg_parser)

        if "--help" in args.module_args or "-h" in args.module_args:
            module_arg_parser.print_help()
            return

        try:
            module_args = module_arg_parser.parse_args(args.module_args)
            module_class.main(module_args)
        except Exception as e:
            Logger.log("flaw", f"Execution failed: {e}")


if __name__ == "__main__":
    main()
