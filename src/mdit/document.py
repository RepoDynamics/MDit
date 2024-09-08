from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING

from mdit import element as _elem, target as _target
from mdit.protocol import TargetConfig as _TargetConfig

if _TYPE_CHECKING:
    from mdit.container import Container, MDContainer
    from mdit.element import FrontMatter, Heading
    from mdit.protocol import TargetConfigType


class Document:

    _TARGET_CONFIG = {
        "sphinx": _target.sphinx(),
        "github": _target.github(),
        "pypi": _target.pypi(),
    }

    def __init__(
        self,
        heading: Heading | None,
        body: MDContainer,
        section: Container,
        footer: MDContainer,
        frontmatter: FrontMatter | None = None,
        frontmatter_conditions: list[str] | None = None,
        separate_sections: bool = False,
        toctree_args: dict[str, str] | None = None,
        toctree_dirhtml: bool = True,
        default_output_target: TargetConfigType = "sphinx",
    ):
        self.heading = heading
        self.body = body
        self.section = section
        self.footer = footer
        self.frontmatter = frontmatter
        self.frontmatter_conditions = frontmatter_conditions or []
        self.separate_sections = separate_sections
        self.toctree_args = toctree_args or {}
        self.toctree_dirhtml = toctree_dirhtml
        self.default_output_target = default_output_target
        return

    def str(
        self,
        target: TargetConfigType | None = None,
        filters: str | list[str] | None = None,
        heading_level: int = 1,
        separate_sections: bool | None = None,
        heading_level_raise: bool = True,
    ) -> tuple[str, dict[str, str]]:
        if heading_level > 6:
            if heading_level_raise:
                raise ValueError("Heading level cannot be greater than 6.")
            heading_level = 6
        target = self._resolve_target(target)
        document = {}
        page = []
        if self.frontmatter and heading_level == 1 and (
            not filters
            or not self.frontmatter_conditions
            or any(filter in self.frontmatter_conditions for filter in filters)
        ):
            frontmatter = self.frontmatter.str(target=target, filters=filters)
            if frontmatter:
                page.append(frontmatter)
        if self.heading:
            self.heading.level = heading_level
            page.append(self.heading.str(target=target, filters=filters))
        elif heading_level != 1:
            raise ValueError("Document must have a heading if heading level is not 1.")
        separate_sections = separate_sections if separate_sections is not None else self.separate_sections
        if separate_sections and target.directive_toctree:
            toctree_children = [
                f"{key}/index" if self.toctree_dirhtml else key for key in self.section.keys()
            ]
            toctree = _elem.toctree(content=toctree_children, **self.toctree_args)
            page.append(toctree.str(target=target, filters=filters))

        content = self.body.str(target=target, filters=filters)
        if content:
            page.append(content)

        for key, (section, conditions) in self.section.items():
            if not filters or not conditions or any(filter in conditions for filter in filters):
                section_str, subsections_str = section.str(
                    target=target,
                    filters=filters,
                    heading_level=1 if separate_sections else heading_level + 1,
                    separate_sections=False if separate_sections is False else None,
                )
                if separate_sections:
                    document[f"{key}/index" if self.toctree_dirhtml else str(key)] = section_str
                    for sub_key, sub_section in subsections_str.items():
                        document[f"{key}/{sub_key}"] = sub_section
                else:
                    page.append(section_str)

        footer = self.footer.str(target=target, filters=filters)
        if footer:
            page.append(footer)
        return f"{"\n\n".join(page).strip()}\n", document

    def _resolve_target(self, target: TargetConfigType | None = None) -> _TargetConfig:
        target = target or self.default_output_target
        if isinstance(target, _TargetConfig):
            return target
        return self._TARGET_CONFIG[target]
