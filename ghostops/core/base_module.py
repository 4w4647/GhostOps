from abc import ABC, abstractmethod
from typing import List
from ghostops.common.utils import Logger


class BaseModule(ABC):
    name: str = None
    description: str = None
    author: str = None
    category: str = None
    os: List[str] = None
    arch: List[str] = None

    @staticmethod
    @abstractmethod
    def register_arguments(parser):
        pass

    @staticmethod
    @abstractmethod
    def run(args):
        pass

    @classmethod
    def validate(cls, module_name: str) -> bool:
        expected_name = to_pascal_case(module_name)
        required_str_fields = ["name", "description", "author", "category"]
        required_list_fields = ["os", "arch"]
        errors = []

        for field in required_str_fields:
            value = getattr(cls, field, None)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"`{field}` must be a non-empty string.")

        for field in required_list_fields:
            value = getattr(cls, field, None)
            if (
                not isinstance(value, list)
                or not value
                or not all(isinstance(i, str) and i.strip() for i in value)
            ):
                errors.append(
                    f"`{field}` must be a non-empty list of non-empty strings."
                )

        if cls.__name__ != expected_name:
            errors.append(
                f"Class name '{cls.__name__}' must match PascalCase module name '{expected_name}'."
            )
        if cls.name != expected_name:
            errors.append(
                f"`name` must match PascalCase module name '{expected_name}'."
            )

        for method in ["register_arguments", "run"]:
            fn = cls.__dict__.get(method)
            if not callable(fn):
                errors.append(f"Missing static method `{method}()`.")

        for error in errors:
            Logger.log("flaw", f"Validation error in module '{module_name}': {error}")

        return not errors

    @classmethod
    def info(cls):
        Logger.log("info", f"Module      - {cls.name}")
        Logger.log("info", f"Description - {cls.description}")
        Logger.log("info", f"Author      - {cls.author}")
        Logger.log("info", f"Category    - {cls.category}")
        Logger.log("info", f"OS          - {', '.join(cls.os)}")
        Logger.log("info", f"Arch        - {', '.join(cls.arch)}")
        print()


def to_pascal_case(name: str) -> str:
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))
