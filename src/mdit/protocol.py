from __future__ import annotations

from typing import (
    Protocol as _Protocol,
    runtime_checkable as _runtime_checkable,
    TYPE_CHECKING as _TYPE_CHECKING,
)

from pyprotocol import Stringable
from htmp.protocol import AttrsInputType as _AttrsInputType

from mdit.target.md import Config as MDTargetConfig
from mdit.target.rich import Config as RichTargetConfig

if _TYPE_CHECKING:
    from rich.console import RenderableType


TargetConfig = MDTargetConfig | RichTargetConfig
TargetConfigs = dict[str, TargetConfig] | None
TargetConfigInput = TargetConfig | str | None

HTMLAttrsType = _AttrsInputType


@_runtime_checkable
class MDITRenderable(_Protocol):
    """Protocol for MDIT renderable objects."""

    @property
    def code_fence_count(self) -> int:
        ...

    def source(self, target: TargetConfigInput = None, filters: str | list[str] | None = None) -> str | RenderableType:
        ...


ContainerContentType = Stringable | MDITRenderable
ContentConditionType = str | list[str] | tuple[str] | None
ContainerInputType = (
    ContainerContentType
    | list[ContainerContentType | tuple[ContainerContentType, ContentConditionType]]
    | dict[str | int, ContainerContentType | tuple[ContainerContentType, ContentConditionType]]
    | None
)

