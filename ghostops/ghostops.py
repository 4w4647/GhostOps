import os
import sys
import argparse
import importlib.util
from ghostops.common.utils import Banner, Logger
from ghostops.core.base_module import BaseModule


class GhostOps:
    def __init__(self, modules_path="ghostops/modules"):
        Banner.print_banner()

        self.modules_path = modules_path
        self.validated_modules = []

    def validate_module(self, module_path, module_name):
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception as e:
            Logger.log("flaw", f"Failed to import module '{module_name}': {e}")
            return

        for attr in vars(module).values():
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseModule)
                and attr is not BaseModule
            ):
                if attr.validate(module_name):
                    self.validated_modules.append(attr)
                return

    def discover_modules(self):
        if not os.path.isdir(self.modules_path):
            Logger.log("flaw", f"Invalid modules directory: '{self.modules_path}'")
            return

        for root, _, files in os.walk(self.modules_path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    path = os.path.join(root, file)
                    name = file[:-3]
                    self.validate_module(path, name)

    def list_modules(self):
        for mod in self.validated_modules:
            mod.info()

    def get_module_by_name(self, name):
        for mod in self.validated_modules:
            if mod.__name__ == name:
                return mod
        return None


def main():
    ghostops = GhostOps()
    ghostops.discover_modules()

    parser = argparse.ArgumentParser(
        description="GhostOps - Command and Control Framework", add_help=False
    )
    parser.add_argument(
        "--module", metavar="ModuleName", help="Specify the module to execute"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all available modules"
    )
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show help message and exit"
    )

    args, unknown_args = parser.parse_known_args()

    if args.help and not args.module:
        parser.print_help()
        return

    if args.list:
        ghostops.list_modules()
        return

    if not args.module:
        parser.print_help()
        return

    module_cls = ghostops.get_module_by_name(args.module)
    if not module_cls:
        Logger.log("flaw", f"Module '{args.module}' not found.")
        return

    mod_parser = argparse.ArgumentParser(
        prog=f"ghostops --module {args.module}", description=module_cls.description
    )

    if hasattr(module_cls, "register_arguments") and callable(
        module_cls.register_arguments
    ):
        module_cls.register_arguments(mod_parser)

    if args.help or "--help" in unknown_args or "-h" in unknown_args:
        mod_parser.print_help()
        return

    try:
        mod_args = mod_parser.parse_args(unknown_args)
        module_cls.info()
        module_cls.run(mod_args)
    except Exception as e:
        Logger.log("flaw", f"Execution failed: {e}")
