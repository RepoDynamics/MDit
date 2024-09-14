"""Work with JSON schemas defined by the package."""

from typing import Callable as _Callable

import referencing as _referencing
from referencing import jsonschema as _ref_jsonschema
import jsonschemata as _jsonschemata
import pyserials as _ps

from mdit.data import file as _file


_REGISTRY = None
_SCHEMATA = None


def make_registry(
    dynamic: bool = False,
    crawl: bool = True,
    add_resources: list[dict | _referencing.Resource | tuple[str, dict | _referencing.Resource]] | None = None,
    add_resources_default_spec: _referencing.Specification = _ref_jsonschema.DRAFT202012,
    retrieval_func: _Callable[[str], str | _referencing.Resource] = None,
) -> tuple[_referencing.Registry, dict[str, dict]]:
    schemata = _file.schema(relative_uri=False)
    resources = add_resources or []
    for schema in schemata.values():
        _jsonschemata.edit.required_last(schema)
        resources.append(schema)
    registry = _jsonschemata.registry.make(
        dynamic=dynamic,
        crawl=crawl,
        add_resources=resources,
        add_resources_default_spec=add_resources_default_spec,
        retrieval_func=retrieval_func,
    )
    return registry, schemata


def validate(data: dict, schema_id: str):
    global _REGISTRY, _SCHEMATA
    if not _REGISTRY:
        _REGISTRY, _SCHEMATA = make_registry()
    _ps.validate.jsonschema(
        data=data,
        schema=_SCHEMATA[schema_id],
        registry=_REGISTRY,
        fill_defaults=True,
    )
    return

