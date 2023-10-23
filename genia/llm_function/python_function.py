import logging
import re

from typing import Any

from genia.llm_function.llm_function import LLMFunction


import os
import importlib


def load_classes_from_directory(directory):
    for dirpath, dirnames, filenames in os.walk(directory):
        for name in filenames:
            if name.endswith(".py"):
                path = os.path.join(dirpath, name)
                module_name = os.path.splitext(path)[0].replace("/", ".")
                spec = importlib.util.spec_from_file_location(module_name, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)


class PythonFunction(LLMFunction):
    logger = logging.getLogger(__name__)

    def __init__(self):
        load_classes_from_directory("genia/tools")

    def sanitize_input(self) -> str:
        # Removes `, whitespace & python from start
        self = re.sub(r"^(\s|`)*(?i:python)?\s*", "", self)
        # Removes whitespace & ` from end
        self = re.sub(r"(\s|`)*$", "", self)
        return self

    def evaluate(self, function_config: dict, parameters: dict) -> Any:
        try:
            fq_class_name = function_config.get("class")
            module_name_str, _, class_name = fq_class_name.rpartition(".")
            module = importlib.import_module(module_name_str)
            if class_obj := getattr(module, class_name):
                instance = class_obj()  # Instantiate the class
                method = getattr(instance, function_config.get("method"))  # Get the method object
                return str(method(**parameters))  # Invoke the method
            else:
                self.logger.error("Class %s not found.", class_name)
                raise Exception(f"function config error: {function_config}")
        except Exception as e:
            error_str = f"{type(e).__name__}: {str(e)}"
            self.logger.exception(error_str)
            return error_str
