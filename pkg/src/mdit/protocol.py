from __future__ import annotations

from typing import (
    Protocol as _Protocol,
    runtime_checkable as _runtime_checkable,
    TYPE_CHECKING as _TYPE_CHECKING,
)

from protocolman import Stringable
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
ContainerContentConditionType = str | list[str] | tuple[str] | None
ContainerContentSingleInputType = (
    ContainerContentType
    | tuple[ContainerContentType, ContainerContentConditionType]
    | tuple[ContainerContentType, ContainerContentConditionType, str | int]
    | dict[str | int, ContainerContentType | tuple[ContainerContentType, ContainerContentConditionType]]
    | None
)
ContainerContentInputType = ContainerContentSingleInputType | list[ContainerContentSingleInputType]
