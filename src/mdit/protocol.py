from __future__ import annotations

from typing import Protocol as _Protocol, runtime_checkable as _runtime_checkable, TYPE_CHECKING as _TYPE_CHECKING
from dataclasses import dataclass as _dataclass, asdict as _asdict
import copy as _copy

if _TYPE_CHECKING:
    from typing import Any, Callable, Literal
    from pyprotocol import Stringable
    from ansi_sgr.protocol import ANSIInlineStyle, ANSIBlockStyle, ANSIAdmonitionStyle, ANSICodeBlockStyle


@_runtime_checkable
class MDCode(_Protocol):
    """An object representing Markdown code."""

    _IS_MD_CODE: Any

    def source(self, target: str | None = None, filters: str | list[str] | None = None) -> str:
        ...

    def __str__(self) -> str:
        return self.source()

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
    field_list: bool
    fence: Literal["`", ":", "~"]
    directive_admo: bool
    directive_code: bool
    directive_image: bool
    directive_figure: bool
    directive_toctree: bool
    directive_toggle: bool
    alerts: bool
    picture_theme: bool
    renderer: Callable[[dict], str]

    def copy(self) -> TargetConfig:
        return _copy.deepcopy(self)

    @property
    def dict(self) -> dict:
        return _asdict(self)


@_dataclass
class ANSITargetConfig:
    code_span: ANSIInlineStyle
    heading: list[ANSIBlockStyle]
    field_list_title: ANSIInlineStyle
    field_list_description: ANSIBlockStyle
    admonition_note: ANSIAdmonitionStyle
    admonition_important: ANSIAdmonitionStyle
    admonition_hint: ANSIAdmonitionStyle
    admonition_seealso: ANSIAdmonitionStyle
    admonition_tip: ANSIAdmonitionStyle
    admonition_attention: ANSIAdmonitionStyle
    admonition_caution: ANSIAdmonitionStyle
    admonition_warning: ANSIAdmonitionStyle
    admonition_danger: ANSIAdmonitionStyle
    admonition_error: ANSIAdmonitionStyle
    code_block: ANSICodeBlockStyle

    @property
    def dict(self) -> dict:
        return _asdict(self)



TargetConfigType = TargetConfig | ANSITargetConfig | Literal["sphinx", "github", "pypi", "ansi"]