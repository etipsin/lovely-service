import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from pydantic.schema import schema

from service.data_classes import base


def import_dataclasses(any_dataclass_module: Any) -> None:
    """
    Import all dataclasses from dataclasses' directory.
    This function expects all dataclasses to be in a single directory,
    without any subdirectories.

        Example:

        /data_classes/
            some_dataclasses.py

            other_dataclasses.py

    One of the files should be imported and passed to this function.

    :param any_dataclass_module: A single dataclasses' module.
    """

    # Get path to the data_classes directory
    classes_path = Path(any_dataclass_module.__file__).parent

    # Base module package name
    package_name = any_dataclass_module.__name__.rsplit(sep=".", maxsplit=1)[0]

    # Iterate over all modules inside and import them
    for (_, name, _) in pkgutil.iter_modules(path=[classes_path]):
        importlib.import_module(f".{name}", package_name)


# Recursively get all subclasses of a class
def all_subclasses(cls) -> set:
    """
    Get all subclasses of a class.

    :param cls: class.
    :return: a set of subclasses.
    """
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)]
    )


def get_definitions(any_dataclass_module: Any) -> dict:
    """
    Return Swagger objects definitions.
    This function recursively takes all subclasses of BaseClass
     and generates a full schema for them.

    This function expects all dataclasses to be in a single directory,
    without any subdirectories.

        Example:

        /data_classes/
            some_dataclasses.py

            other_dataclasses.py

    One of the files should be imported and passed to this function.

    :param any_dataclass_module: A single dataclasses' module.

    :return: Swagger definitions.
    """
    import_dataclasses(any_dataclass_module)

    subclasses = all_subclasses(base.BaseClass)

    top_level_schema = schema(subclasses, ref_prefix="#/components/schemas/")
    definitions = {
        k: v
        for k, v in sorted(
            top_level_schema["definitions"].items(), key=lambda item: item[0]
        )
    }

    return definitions


@dataclass
class CustomError:
    """
    error_code - HTTP error code.
    error_dataclass_path - Path inside the swagger.json.

    Example:
        error_code = 400
        error_dataclass_path = "#/components/schemas/Examples/responses/400"
    """

    error_code: int
    error_dataclass_path: str


def update_function_docstring_with_swagger(
    function,
    enable_400_error: bool = True,
    enable_500_error: bool = True,
    custom_errors: List[CustomError] = None,
):
    """
    Update function docstring with swagger schema.

    :param function: Function to be updated.
    :param enable_400_error: Add default 400 code example.
    :param enable_500_error: Add default 500 code example.
    :param custom_errors: List of custom errors.
    :return: Updated function.
    """

    # Fix problems with non-filled docstrings
    if not function.__doc__:
        function.__doc__ = ""

    # If there is no schema declared in current docstring
    if function.__doc__.find("---") == -1:
        current_docstring = function.__doc__.strip().split("\n", 1)
        summary = current_docstring[0]
        description = current_docstring[-1].strip().replace("\n", "\n        ")

        module = " ".join(
            [
                name.capitalize()
                for name in function.__module__.rsplit(".", 1)[-1].split("_")
            ]
        )

        # Function annotation
        data_annotation = function.__annotations__["data"]
        return_annotation = function.__annotations__["return"]

        # Union data annotation
        try:
            data_schema: str = (
                f"$ref: '#/components/schemas/{data_annotation.__name__}'"
            )
        except Exception:
            data_schema: str = f"oneOf:\n"
            classes: tuple = data_annotation.__args__

            for single_class in classes:
                data_schema += (
                    "    " * 6
                    + f"  - $ref: '#/components/schemas/{single_class.__name__}'\n"
                )

        # Create a docstring
        new_docstring = f"""
        {current_docstring}

        ---
        security:
            - bearerAuth: []
        summary: {summary}
        tags:
            - {module}
        description: |
            {description}
        requestBody:
            required: true
            content:
                application/json:
                    schema:
                        {data_schema}
        responses:
            '200':
                description: Успешная операция.
                content:
                    application/json:
                        schema:
                            $ref: '#/components/schemas/{return_annotation.__name__}'
        """

        # Add http error examples
        if enable_400_error:
            new_docstring += """
            '400':
                $ref: '#/components/schemas/Examples/default/400'
            """

        if enable_500_error:
            new_docstring += """
            '500':
                $ref: '#/components/schemas/Examples/default/500'
            """

        if custom_errors:
            for custom_error in custom_errors:
                new_docstring += f"""
            '{custom_error.error_code}':
                $ref: '{custom_error.error_dataclass_path}'
            """

        function.__doc__ = new_docstring

    return function
