"""Get package data files."""

from pathlib import Path as _Path

import pkgdata as _pkgdata
import pyserials as _ps


path = _pkgdata.get_package_path_from_caller(top_level=True) / "data"


def template(group: str, name: str) -> str:
    """Get the string content of a template."""
    dir_path = path / "template" / group
    for filepath in dir_path.iterdir():
        if filepath.stem == name:
            return filepath.read_text()


def schema(schema_id: str | None = None, relative_uri: bool = True) -> dict:
    """Get all JSON schemas as a dictionary of schema IDs to schema objects.

    Parameters
    ----------
    schema_id : str, optional
        If provided, return only the schema with the given ID, otherwise all schemas.
        The schema ID can be either an absolute or relative URI, i.e., with or without
        the "https://docsman.repodynamics.com/schema/" prefix.
    relative_uri : bool, default: True
        Only applies when `schema_id` is not provided:
        If True, the schema IDs (i.e., the keys of the returned dictionary)
        will be relative URIs instead of absolute URIs,
        i.e., without the "https://docsman.repodynamics.com/schema/" prefix.

    Returns
    -------
    dict
        If `schema_id` is provided, the schema object is returned,
        otherwise a dictionary of JSON schemas with their IDs as keys.
        The schema IDs are relative URIs if `relative_uri` is True.
    """
    dir_path = path / "schema"
    if schema_id:
        filepath = dir_path / schema_id.removeprefix("https://docsman.repodynamics.com/schema/")
        filepath_full = filepath.with_suffix(".yaml")
        return _ps.read.yaml_from_file(path=filepath_full)
    schemas = {}
    for filepath in dir_path.glob("**/*.yaml"):
        schema = _ps.read.yaml_from_file(path=filepath)
        schema_id = schema["$id"].removeprefix(
            "https://docsman.repodynamics.com/schema/" if relative_uri else ""
        )
        schemas[schema_id] = schema
    return schemas


def from_filepath(filepath: str | _Path) -> str | dict | list:
    """Get a package data file from its relative path.

    Parameters
    ----------
    filepath : str
        Path of the data file relative to the package's `data` directory.

    Returns
    -------
    file_content : str | dict | list
        The content of the file.
        If the file is a serialized data structure (e.g., JSON or YAML),
        the content will be deserialized, otherwise a string is returned.
    """
    absolute_filepath = path / filepath
    if absolute_filepath.suffix in (".json", ".yaml", ".yml", "toml"):
        return _ps.read.from_file(path=absolute_filepath)
    return absolute_filepath.read_text()
