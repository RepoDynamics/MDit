from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING, Callable, Sequence

import mdit as _mdit
from mdit import element as _elem
from mdit.renderable import Renderable as _Renderable
import rich as _rich

if _TYPE_CHECKING:
    from rich.console import RenderableType
    from mdit.container import Container, MDContainer
    from mdit.element import FrontMatter, Heading
    from mdit.protocol import TargetConfigs, TargetConfigInput, ContainerContentInputType, RichTargetConfig, MDTargetConfig


class Document(_Renderable):

    def __init__(
        self,
        heading: Heading | None,
        body: MDContainer,
        section: Container,
        footer: MDContainer,
        frontmatter: FrontMatter | None = None,
        frontmatter_conditions: list[str] | None = None,
        separate_sections: bool = False,
        current_section_key: list[str | int] = None,
        toctree_args: dict[str, str] | None = None,
        toctree_dirhtml: bool = True,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
        deep_section_generator: Callable[[Document], str] | None = None,
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.heading = heading
        self.body = body
        self.section = section
        self.footer = footer
        self.frontmatter = frontmatter
        self.frontmatter_conditions = frontmatter_conditions or []
        self.separate_sections = separate_sections
        self.toctree_args = toctree_args or {}
        self.toctree_dirhtml = toctree_dirhtml
        self.deep_section_generator = deep_section_generator
        if not current_section_key:
            self._current_section_key = []
            self._current_section = self
        else:
            self._current_section_key = current_section_key
            self._current_section = self
            for key in current_section_key:
                self._current_section = self._current_section.section[key].content
        return

    @property
    def current_section(self) -> Document:
        return self._current_section

    @property
    def current_section_key(self) -> tuple[str | int, ...]:
        return tuple(self._current_section_key)

    @property
    def current_section_level(self) -> int:
        return len(self._current_section_key) + 1

    def open_section(
        self,
        heading: Heading | MDContainer | ContainerContentInputType,
        key: str | int | None = None,
        conditions: list[str] | None = None,
    ):
        new_section = _mdit.document(heading=heading)
        reg_key = self.current_section.section.append(content=new_section, conditions=conditions, key=key)
        self._current_section_key.append(reg_key)
        self._current_section = new_section
        return

    def close_section(self, target_level: int | None = None):
        curr_level = self.current_section_level
        if not target_level:
            target_level = curr_level - 1
        if not (0 < target_level < curr_level):
            raise ValueError(
                f"Target level must be between 1 and the current section level ({curr_level}), "
                f"but got {target_level}."
            )
        self._current_section_key = self._current_section_key[:target_level - 1]
        section = self
        for key in self._current_section_key:
            section = section.section[key].content
        self._current_section = section
        return

    def display(
        self,
        target: TargetConfigInput = None,
        filters: str | list[str] | None = None,
        heading_number: int | list[int] = 1,
        heading_number_explicit: bool = True,
        separate_sections: bool | None = None,
    ) -> None:
        target = self._resolve_target(target)
        output = self.render(
            target=target,
            filters=filters,
            heading_number=heading_number,
            heading_number_explicit=heading_number_explicit,
            separate_sections=separate_sections,
        )
        if isinstance(target, _mdit.target.rich.Config):
            return _mdit.display.console(output)
        return _mdit.display.browser(output)

    def render(
        self,
        target: TargetConfigInput = None,
        filters: str | list[str] | None = None,
        heading_number: int | list[int] = 1,
        heading_number_explicit: bool = True,
        separate_sections: bool | None = None,
    ) -> str | RenderableType:
        target = self._resolve_target(target)
        document = self.source(
            target=target,
            filters=filters,
            heading_number=heading_number,
            heading_number_explicit=heading_number_explicit,
            separate_sections=separate_sections,
        )
        if isinstance(target, _mdit.target.rich.Config):
            return document
        return target.renderer(document)

    def source(
        self,
        target: TargetConfigInput = None,
        filters: str | list[str] | None = None,
        heading_number: int | Sequence[int] = 1,
        heading_number_explicit: bool = True,
        separate_sections: bool | None = None,
    ) -> str | dict[str, str] | RenderableType:
        target = self._resolve_target(target)
        heading_number = list(heading_number) if isinstance(heading_number, Sequence) else [1] * heading_number
        if isinstance(target, _mdit.target.md.Config):
            if target.directive_toctree:
                doc = self._str_md_multi(
                    target=target,
                    filters=filters,
                    heading_number=heading_number,
                    separate_sections=separate_sections,
                )
                return doc
            return self._str_md_single(
                target=target,
                filters=filters,
                heading_number=heading_number,
                heading_number_explicit=heading_number_explicit,
            )
        return self._source_rich(
            target=target,
            filters=filters,
            heading_number=heading_number,
            heading_number_explicit=heading_number_explicit,
        )

    def depth(
        self,
        target: TargetConfigs | None = None,
        filters: str | list[str] | None = None,
    ) -> int:
        section_depths = (
            doc.depth(target=target, filters=filters)
            for doc in self.section.elements(target=target, filters=filters, source=False)
        )
        return 1 + max(section_depths, default=0)

    def _str_md_single(
        self,
        target: TargetConfigs,
        filters: str | list[str] | None,
        heading_number: list[int],
        heading_number_explicit: bool,
    ) -> dict[str, str]:
        content = [self.body.source(target=target, filters=filters)]
        for idx, (key, (section, conditions)) in enumerate(self.section.items()):
            if not filters or not conditions or any(filter in conditions for filter in filters):
                subsections_str = section.source(
                    target=target,
                    filters=filters,
                    heading_number=heading_number + [idx + 1],
                    heading_number_explicit=heading_number_explicit,
                )
                content.append(subsections_str)
        footer = self.footer.source(target=target, filters=filters)
        if footer:
            content.append(footer)
        page_content = "\n\n".join(content).strip()
        heading_level = len(heading_number)
        page = self._initialize_page(heading_level=heading_level, target=target, filters=filters)
        if self.heading:
            with self.heading.temp(level=heading_number, explicit_number=heading_number_explicit):
                heading = self.heading.source(target=target, filters=filters)
        else:
            heading = ""
        if heading_level < 7:
            page.extend([heading, page_content])
        else:
            if target.directive_toggle:
                # When toggle directive is used, it doesn't accept a title,
                # so the heading is added above the toggle
                page.append(heading)
            # Otherwise <details> is used, which displays the title
            page.append(_mdit.element.toggle(page_content, title=heading).source(target=target))
        return "\n\n".join(page).strip()


    def _str_md_multi(
        self,
        target: MDTargetConfig,
        filters: str | list[str] | None,
        heading_number: list[int],
        separate_sections: bool | None,
    ) -> dict[str, str]:
        heading_level = len(heading_number)
        document = {}
        page = self._initialize_page(heading_level=heading_level, target=target, filters=filters)
        if self.heading:
            with self.heading.temp(level=heading_number, explicit_number=False):
                page.append(self.heading.source(target=target, filters=filters))
        separate_sections = (self.depth(target=target, filters=filters) > 6) or (
            separate_sections if separate_sections is not None else self.separate_sections
        )
        if separate_sections:
            toctree_children = [
                f"{key}/index" if self.toctree_dirhtml else key for key in self.section.keys()
            ]
            toctree = _elem.toctree(*toctree_children, **self.toctree_args)
            page.append(toctree.source(target=target, filters=filters))
        content = self.body.source(target=target, filters=filters)
        if content:
            page.append(content)
        for key, (section, conditions) in self.section.items():
            if not filters or not conditions or any(filter in conditions for filter in filters):
                subsections_str = section.source(
                    target=target,
                    filters=filters,
                    heading_number=[1] if separate_sections else heading_number + [1],
                    separate_sections=False if separate_sections is False else None,
                )
                if not separate_sections:
                    page.append(subsections_str["index"])
                    continue
                for sub_key, sub_section in subsections_str.items():
                    if sub_key == "index":
                        doc_key = f"{key}/index" if self.toctree_dirhtml else str(key)
                        document[doc_key] = sub_section
                    else:
                        document[f"{key}/{sub_key}"] = sub_section
        footer = self.footer.source(target=target, filters=filters)
        if footer:
            page.append(footer)
        document["index"] = f"{"\n\n".join(page).strip()}\n"
        return document

    def _source_rich(
        self,
        target: RichTargetConfig,
        filters: str | list[str] | None,
        heading_number: list[int] = 1,
        heading_number_explicit: bool = True,
    ) -> RenderableType:
        content = []
        if self.heading:
            with self.heading.temp(
                level=heading_number,
                explicit_number=heading_number_explicit,
            ):
                content.append(self.heading.source(target=target, filters=filters))
        elif len(heading_number) != 1:
            raise ValueError("Document must have a heading if heading level is not 1.")
        content.append(self.body.source(target=target, filters=filters))
        for idx, (key, (section, conditions)) in enumerate(self.section.items()):
            if not filters or not conditions or any(filter in conditions for filter in filters):
                subsection = section.source(
                    target=target,
                    filters=filters,
                    heading_number=heading_number + [idx + 1],
                    heading_number_explicit=heading_number_explicit,
                )
                content.append(subsection)
        footer = self.footer.source(target=target, filters=filters)
        if footer:
            content.append(footer)
        return _rich.console.Group(*content)

    def _initialize_page(self, heading_level: int, target: TargetConfigs, filters: str | list[str] | None):
        page = []
        if self.frontmatter and heading_level == 1 and (
            not filters
            or not self.frontmatter_conditions
            or any(filter in self.frontmatter_conditions for filter in filters)
        ):
            frontmatter = self.frontmatter.source(target=target, filters=filters)
            if frontmatter:
                page.append(frontmatter)
        return page
