from __future__ import annotations

from typing import Protocol as _Protocol, runtime_checkable as _runtime_checkable, Any, Literal
from dataclasses import dataclass as _dataclass
import copy as _copy

from pyprotocol import Stringable


@_runtime_checkable
class MDCode(_Protocol):
    """An object representing Markdown code."""

    _IS_MD_CODE: Any

    def str(self, target: str | None = None, filters: str | list[str] | None = None) -> str:
        ...

    def __str__(self) -> str:
        return self.str()

    @property
    def code_fence_count(self) -> int:
        ...


ContainerContentType = Stringable | MDCode
ContentConditionType = str | list[str] | tuple[str] | None
ContainerInputType = (
    ContainerContentType
    | list[ContainerContentType | tuple[ContainerContentType, ContentConditionType]]
    | dict[str | int, ContainerContentType | tuple[ContainerContentType, ContentConditionType]]
    | None
)


@_dataclass
class TargetConfig:
    prefer_md: bool
    attrs_block: bool
    attrs_inline: bool
    target_anchor: bool
    fence: Literal["`", ":", "~"]
    directive_admo: bool
    directive_code: bool
    directive_image: bool
    directive_figure: bool
    directive_toctree: bool
    alerts: bool
    picture_theme: bool

    def copy(self) -> TargetConfig:
        return _copy.deepcopy(self)

TargetConfigType = TargetConfig | Literal["sphinx", "github", "pypi"]