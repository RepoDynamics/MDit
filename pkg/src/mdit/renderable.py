from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING
import copy as _copy
import re as _re

from mdit import target as _target
from mdit import display as _display

if _TYPE_CHECKING:
    from mdit.protocol import MDTargetConfig, RichTargetConfig, TargetConfigs, TargetConfigInput
    from rich.console import RenderableType


class Renderable:

    def __init__(
        self,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx"
    ):
        self.target_configs = {
            "sphinx": _target.sphinx(),
            "github": _target.github(),
            "pypi": _target.pypi(),
            "console": _target.console(),
        } | (target_configs or {})
        self.target_default = target_default

    @property
    def code_fence_count(self) -> int:
        return 0

    def source(self, target: TargetConfigInput = None, filters: str | list[str] | None = None) -> str | RenderableType:
        target = self._resolve_target(target)
        if isinstance(target, _target.rich.Config):
            return self._source_rich(target=target, filters=filters)
        return self._source_md(target=target, filters=filters)

    def display(self, target: TargetConfigInput = None, filters: str | list[str] | None = None) -> None:
        """Display the element in an IPython notebook."""
        target = self._resolve_target(target)
        output = self.source(target=target, filters=filters)
        if isinstance(target, _target.rich.Config):
            _display.console(output)
        else:
            _display.ipython(output)
        return

    def copy(self):
        return _copy.deepcopy(self)

    def _resolve_target(self, target: TargetConfigInput = None) -> MDTargetConfig | RichTargetConfig:
        target = target or self.target_default
        if isinstance(target, (_target.md.Config, _target.rich.Config)):
            return target
        return self.target_configs[target]

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        return ""

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        return ""

    @staticmethod
    def _count_code_fence(content: str) -> int:
        pattern = _re.compile(r'^\s{0,3}(`{3,}|~{3,}|:{3,})', _re.MULTILINE)
        matches = pattern.findall(str(content))
        return max(len(match) for match in matches) if matches else 0
