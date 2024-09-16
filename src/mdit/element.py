from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING, Sequence as _Sequence
from types import FunctionType as _FunctionType
from contextlib import contextmanager as _contextmanager
import re as _re

import htmp as _htmp
import pyserials as _ps
import pybadger as _bdg
import pycolorit as _pcit
import rich
import rich.syntax
import rich.panel
import rich.text

import mdit as _mdit
import rich.rule
from mdit.protocol import MDITRenderable as _MDITRenderable

from mdit.renderable import Renderable as _Renderable

if _TYPE_CHECKING:
    from typing import Literal, Sequence
    from rich.console import RenderableType
    from rich.panel import Panel
    from mdit import MDContainer
    from mdit.protocol import MDTargetConfig, RichTargetConfig, Stringable, ContainerContentInputType, TargetConfigs, HTMLAttrsType, ContainerContentSingleInputType


class Element(_Renderable):

    def __init__(
        self,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        return

    @_contextmanager
    def temp(self, **kwargs):
        orig_val = {}
        new_attrs = []
        try:
            for key, new_value in kwargs.items():
                if hasattr(self, key):
                    orig_val[key] = getattr(self, key)
                else:
                    new_attrs.append(key)
                setattr(self, key, new_value)
            yield
        finally:
            for key, old_value in orig_val.items():
                setattr(self, key, old_value)
            for key in new_attrs:
                delattr(self, key)

    def __str__(self):
        return self.source()

    @staticmethod
    def _wrap(
        content: str,
        container: Stringable | None,
        attrs_container: dict,
    ) -> str:
        if not (container and attrs_container):
            return content
        container_func = getattr(_htmp.element, str(container))
        return container_func(_htmp.elementor.markdown(content), attrs_container).source(indent=-1)


class Admonition(Element):

    MYST_TO_GH_TYPE = {
        "note": "note",
        "important": "important",
        "hint": "tip",
        "seealso": "tip",
        "tip": "tip",
        "attention": "warning",
        "caution": "warning",
        "warning": "warning",
        "danger": "caution",
        "error": "caution",
    }

    MYST_TO_EMOJI = {
        "note": "ℹ️",
        "important": "❗",
        "hint": "💡",
        "seealso": "↪️",
        "tip": "💡",
        "attention": "⚠️",
        "caution": "⚠️",
        "warning": "⚠️",
        "danger": "🚨",
        "error": "❌",
    }

    def __init__(
        self,
        type: Literal[
            "note",
            "important",
            "hint",
            "seealso",
            "tip",
            "attention",
            "caution",
            "warning",
            "danger",
            "error"
        ],
        content: MDContainer,
        title: Stringable = "",
        footer: Stringable = "",
        dropdown: bool = False,
        opened: bool = True,
        classes: list[Stringable] | None = None,
        add_type_class: bool = True,
        name: Stringable | None = None,
        type_github: Literal["note", "tip", "important", "warning", "caution"] | None = None,
        title_bold: bool = True,
        title_tight: bool = True,
        emoji: str | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.type = type
        self.title = title
        self.content = content
        self.footer = footer
        self.dropdown = dropdown
        self.opened = opened
        self.classes = classes or []
        self.add_type_class = add_type_class
        self.name = name
        self.type_github = type_github or self.MYST_TO_GH_TYPE[type]
        self.title_bold = title_bold
        self.title_tight = title_tight
        self.emoji = emoji or self.MYST_TO_EMOJI[type]
        return

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> Panel:
        content = self.content.source(target=target, filters=filters)
        return getattr(target, f"admonition_{self.type}").make(content=content, title=str(self.title), subtitle=str(self.footer))

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(target=target, filters=filters).strip()
        content_full = f"{content}\n\n---\n\n{self.footer}".strip() if self.footer else content
        if target.directive_admo:
            return self._str_admo(content=content_full, target=target, filters=filters)
        if target.alerts:
            return self._str_alert(content=content_full, target=target, filters=filters)
        return self._str_blockquoute(content=content_full, target=target, filters=filters)

    def _str_admo(self, content: str, target: TargetConfigs, filters: str | list[str] | None = None):
        classes = []
        if self.add_type_class:
            classes.append(self.type)
        if self.classes:
            classes.extend(self.classes)
        if self.dropdown:
            classes.append("dropdown")
        if self.opened:
            classes.append("toggle-shown")
        options = {"class": list(set(classes)), "name": self.name}
        return directive(
            name="admonition",
            args=self.title,
            options=options,
            content=content,
        ).source(target=target, filters=filters)

    def _str_alert(self, content: str, target: TargetConfigs, filters: str | list[str] | None = None):
        lines = [f"[!{self.type_github.upper()}]"]
        new_target = target.copy()
        new_target.alerts = False  # Alerts cannot contain other alerts
        title = str(self.title)
        if self.title_bold:
            title = _htmp.element.strong(title)
        if self.dropdown:
            details_content = [_htmp.element.summary(title), _htmp.elementor.markdown(content)]
            details_str = str(_htmp.element.details(details_content, {"open": self.opened}))
            lines.extend(details_str.splitlines())
        else:
            if self.title_tight:
                lines.append(f"{title}{"\\" if content else ""}")
            else:
                lines.append(title)
                if content:
                    lines.append("")
            lines.extend(content.splitlines())
        return "\n".join(f"> {line}" for line in lines)

    def _str_blockquoute(self, content: str, target: TargetConfigs, filters: str | list[str] | None = None):
        lines = []
        title = str(self.title)
        if self.title_bold:
            title = _htmp.element.strong(title)
        if self.dropdown:
            summary = f"{self.emoji}&ensp;{title}"
            details_content = [_htmp.element.summary(summary), _htmp.elementor.markdown(content)]
            details_str = str(_htmp.element.details(details_content, {"open": self.opened}))
            lines.extend(details_str.splitlines())
        else:
            if self.title_tight:
                lines.append(f"{title}{"\\" if content else ""}")
            else:
                lines.append(title)
                if content:
                    lines.append("")
            lines.extend(content.splitlines())
        return "\n".join(f"> {line}" for line in lines)

    @property
    def code_fence_count(self) -> int:
        return max(self.content.code_fence_count, 2) + 1


class Attribute(Element):

    def __init__(
        self,
        content: _MDITRenderable | Stringable,
        block: bool,
        classes: list[Stringable] | Stringable | None = None,
        name: Stringable | None = None,
        attrs: dict | None = None,
        comment: Stringable | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.block = block
        self.classes = classes
        self.name = name
        self.attrs = attrs or {}
        self.comment = comment
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(
            target=target, filters=filters
        ) if isinstance(self.content, _MDITRenderable) else str(self.content)
        if not (target.attrs_block if self.block else target.attrs_inline):
            return content
        attrs = []
        if self.name:
            attrs.append(f"#{self.name}")
        if self.classes:
            if isinstance(self.classes, (list, tuple)):
                for class_name in self.classes:
                    attrs.append(f".{class_name}")
            else:
                attrs.append(f".{self.classes}")
        for key, value in self.attrs.items():
            if value:
                attrs.append(f"{key}={value}")
        if self.comment:
            attrs.append(f"% {self.comment}")
        if not attrs:
            return content
        attributor = f"{{{" ".join(attrs)}}}"
        if self.block:
            return f"{attributor}\n{content.lstrip()}"
        return f"[{content.strip()}]{attributor}"

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        return self.content.source(
            target=target, filters=filters
        ) if isinstance(self.content, _MDITRenderable) else str(self.content)


class BlockImage(Element):
    def __init__(
        self,
        src: Stringable,
        src_dark: Stringable | None = None,
        title: Stringable | None = None,
        alt: Stringable | None = None,
        height: Stringable | None = None,
        width: Stringable | None = None,
        scale: Stringable | None = None,
        align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
        link: Stringable | None = None,
        caption: MDContainer | None = None,
        width_figure: Stringable | None = None,
        classes: list[Stringable] | None = None,
        classes_light: list[Stringable] | None = None,
        classes_dark: list[Stringable] | None = None,
        classes_figure: list[Stringable] | None = None,
        name: Stringable | None = None,
        attrs_img: dict | None = None,
        attrs_source_light: dict | None = None,
        attrs_source_dark: dict | None = None,
        attrs_picture: dict | None = None,
        attrs_figcaption: dict | None = None,
        attrs_figure: dict | None = None,
        attrs_a: dict | None = None,
        container: Stringable | None = "div",
        attrs_container: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.src = src
        self.src_dark = src_dark
        self.title = title
        self.alt = alt
        self.height = height
        self.width = width
        self.scale = scale
        self.align = align
        self.link = link
        self.classes = classes or []
        self.classes_light = classes_light or []
        self.classes_dark = classes_dark or []
        self.name = name
        self.caption = caption
        self.width_figure = width_figure
        self.classes_figure = classes_figure or []
        self.attrs_img = attrs_img or {}
        self.attrs_source_light = attrs_source_light or {}
        self.attrs_source_dark = attrs_source_dark or {}
        self.attrs_picture = attrs_picture or {}
        self.attrs_figcaption = attrs_figcaption or {}
        self.attrs_figure = attrs_figure or {}
        self.attrs_a = attrs_a or {}
        self.container = container
        self.attrs_container = attrs_container or {}
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        target = self._resolve_target(target)
        if target.directive_image or target.directive_figure:
            return self._str_directive(target=target, filters=filters)
        attrs_img = self._make_img_attrs() | {
            "src": self.src,
            "title": self.title,
            "class": self.classes + self.classes_light,
            "id": self.name,
        } | self.attrs_img
        image = _htmp.elementor.picture_color_scheme(
            src_light=self.src,
            src_dark=self.src_dark,
            attrs_img=attrs_img,
            attrs_source_light=self.attrs_source_light,
            attrs_source_dark=self.attrs_source_dark,
            attrs_picture=self.attrs_picture,
        ) if self.src_dark and target.picture_theme else _htmp.element.img(attrs_img)
        caption = self.caption.source(target=target, filters=filters)
        if caption:
            caption_tag = _htmp.element.figcaption(caption, self.attrs_figcaption)
            image = _htmp.element.figure([image, caption_tag], self.attrs_figure)
        if self.link:
            attrs_a = {"href": self.link, "alt": self.alt} | self.attrs_a
            image = _htmp.element.a(image, attrs_a)
        attrs_container = self.attrs_container
        if self.align:
            attrs_container = {"align": self.align} | attrs_container
        return self._wrap(content=str(image), container=self.container, attrs_container=attrs_container)

    @property
    def code_fence_count(self) -> int:
        return max(self.caption.code_fence_count, 2) + 1

    def _make_img_attrs(self):
        img_attrs = {
            "alt": self.alt,
            "height": self.height,
            "width": self.width,
        }
        return img_attrs

    def _str_directive(self, target: TargetConfigs, filters: str | list[str] | None = None):
        options = self._make_img_attrs() | {
            "scale": self.scale,
            "align": self.align,
            "target": self.link,
            "class": self.classes + self.classes_light,
            "name": self.name,
        }
        if not target.directive_image:
            directive_name = "figure"
        elif not target.directive_figure:
            directive_name = "image"
        else:
            directive_name = "figure" if self.caption or self.width_figure or self.classes_figure else "image"
        if directive_name == "figure":
            options |= {
                "figwidth": self.width_figure,
                "figclass": self.classes_figure,
            }
            content = self.caption.source(target=target, filters=filters) if self.caption else None
        else:
            content = None
        figure_light = directive(
            name=directive_name,
            args=self.src,
            options=options,
            content=content,
        ).source(target=target, filters=filters)
        if not self.src_dark:
            return figure_light
        options["class"] = self.classes + self.classes_dark
        figure_dark = directive(
            name=directive_name,
            args=self.src_dark,
            options=options,
            content=content,
        ).source(target=target, filters=filters)
        return f"{figure_light}\n{figure_dark}"


class BlockQuote(Element):

    def __init__(
        self,
        content: MDContainer,
        cite: MDContainer | None = None,
        name: Stringable | None = None,
        classes: list[Stringable] | None = None,
        attrs: dict | None = None,
        attrs_cite: dict | None = None,
        container: Stringable | None = "div",
        attrs_container: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.cite = cite
        self.name = name
        self.classes = classes or []
        self.attrs = attrs or {}
        self.attrs_cite = attrs_cite if attrs_cite is not None else {"align": "right", "style": {"text-align": "right"}}
        self.container = container
        self.attrs_container = attrs_container or {}
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:

        def make_md_blockquote(lines: list[str]) -> str:
            return "\n".join(f"> {line}" for line in lines)

        target = self._resolve_target(target)
        content = self.content.source(target=target, filters=filters)
        cite = self.cite.source(target=target, filters=filters) if self.cite else None
        cite_line = f"—{cite}"
        if not (content or cite):
            return ""
        if not target.prefer_md:
            blockquote_content = [_htmp.elementor.markdown(content)]
            if cite:
                blockquote_content.append(_htmp.element.p(cite_line, self.attrs_cite))
            blockquote = _htmp.element.blockquote(
                blockquote_content,
                self.attrs | {"class": self.classes, "id": self.name},
            ).source(indent=-1)
            return self._wrap(content=blockquote, container=self.container, attrs_container=self.attrs_container)
        lines = content.splitlines()
        if not (self.classes or self.name or cite):
            return make_md_blockquote(lines)
        if target.attrs_block:
            return attribute(
                content=make_md_blockquote(lines),
                block=True,
                classes=self.classes,
                name=self.name,
                attrs={"attribution": cite} if cite else None,
            ).source(target=target, filters=filters)
        if cite:
            lines.append(cite_line)
        blockquote = make_md_blockquote(lines)
        if self.name and target.target_anchor:
            return target_anchor(
                content=blockquote,
                name=self.name,
            ).source(target=target, filters=filters)
        return blockquote


class Card(Element):

    def __init__(
        self,
        header: MDContainer | None = None,
        title: Stringable | None = None,
        body: MDContainer | None = None,
        footer: MDContainer | None = None,
        width: Literal["auto"] | int | None = None,
        margin: Literal["auto", 0, 1, 2, 3, 4, 5] | tuple[
            Literal["auto", 0, 1, 2, 3, 4, 5], ...] | None = None,
        text_align: Literal["left", "center", "right", "justify"] | None = None,
        img_background: Stringable | None = None,
        img_top: Stringable | None = None,
        img_bottom: Stringable | None = None,
        img_alt: Stringable | None = None,
        link: Stringable | None = None,
        link_type: Literal["url", "ref", "doc", "any"] | None = None,
        link_alt: Stringable | None = None,
        shadow: Literal["sm", "md", "lg", "none"] | None = None,
        classes_card: list[str] | None = None,
        classes_header: list[str] | None = None,
        classes_body: list[str] | None = None,
        classes_footer: list[str] | None = None,
        classes_title: list[str] | None = None,
        classes_img_top: list[str] | None = None,
        classes_img_bottom: list[str] | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.header = header
        self.title = title
        self.body = body
        self.footer = footer
        self.width = width
        self.margin = margin
        self.text_align = text_align
        self.img_background = img_background
        self.img_top = img_top
        self.img_bottom = img_bottom
        self.img_alt = img_alt
        self.link = link
        self.link_type = link_type
        self.link_alt = link_alt
        self.shadow = shadow
        self.classes_card = classes_card or []
        self.classes_header = classes_header or []
        self.classes_body = classes_body or []
        self.classes_footer = classes_footer or []
        self.classes_title = classes_title or []
        self.classes_img_top = classes_img_top or []
        self.classes_img_bottom = classes_img_bottom or []
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = []
        if self.header:
            header = self.header.source(target=target, filters=filters)
            content.extend([header, "^^^"])
        if self.body:
            content.append(self.body.source(target=target, filters=filters))
        if self.footer:
            footer = self.footer.source(target=target, filters=filters)
            content.extend(["+++", footer])
        content_str = "\n".join(content)
        options = {
            "width": self.width,
            "margin": self.margin,
            "text-align": self.text_align,
            "img-background": self.img_background,
            "img-top": self.img_top,
            "img-bottom": self.img_bottom,
            "img-alt": self.img_alt,
            "link": self.link,
            "link-type": self.link_type,
            "link-alt": self.link_alt,
            "shadow": self.shadow,
            "class-card": self.classes_card,
            "class-header": self.classes_header,
            "class-body": self.classes_body,
            "class-footer": self.classes_footer,
            "class-title": self.classes_title,
            "class-img-top": self.classes_img_top,
            "class-img-bottom": self.classes_img_bottom,
        }
        return directive(
            name="card",
            args=self.title,
            options=options,
            content=content_str,
        ).source(target=target, filters=filters)


class CodeBlock(Element):

    def __init__(
        self,
        content: Stringable,
        language: Stringable | None = None,
        caption: Stringable | None = None,
        line_num: bool = False,
        line_num_start: int | None = None,
        emphasize_lines: list[int] | None = None,
        force: bool = False,
        name: Stringable | None = None,
        classes: Stringable | list[Stringable] | None = None,
        degrade_to_diff: bool = True,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.language = language
        self.caption = caption
        self.line_num = line_num
        self.line_num_start = line_num_start
        self.emphasize_lines = emphasize_lines or []
        self.force = force
        self.name = name
        self.classes = classes or []
        self.degrade_to_diff = degrade_to_diff
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        if target.directive_code:
            options = {
                "caption": self.caption,
                "linenos": bool(self.line_num or self.line_num_start),
                "lineno-start": self.line_num_start,
                "emphasize-lines": self.emphasize_lines,
                "force": self.force,
                "name": self.name,
                "class": self.classes,
            }
            return directive(
                name="code-block",
                args=self.language,
                options=options,
                content=self.content,
            ).source(target=target, filters=filters)
        fence = target.fence * self.code_fence_count
        content = str(self.content)
        if self.emphasize_lines and self.degrade_to_diff:
            language = "diff"
            content_lines = content.splitlines()
            content = "\n".join(
                f"- {line}" if i + 1 in self.emphasize_lines else line
                for i, line in enumerate(content_lines)
            )
        else:
            language = self.language
        start_line = f"{fence}{language}"
        block = f"{start_line}\n{content}\n{fence}"
        if self.caption:
            return f"**{self.caption}**\n{block}"
        return block

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> rich.panel.Panel:
        return target.code_block.make(
            code=str(self.content).strip(),
            lexer=str(self.language) if self.language else None,
            title=str(self.caption) if self.caption else None,
            subtitle=str(self.language) if self.language else None,
            line_numbers=self.line_num,
            start_line=self.line_num_start or 1,
            highlight_lines=set(self.emphasize_lines) or None,
        )

    @property
    def code_fence_count(self):
        return max(self._count_code_fence(str(self.content)), 2) + 1


class CodeSpan(Element):

    def __init__(
        self,
        content: Stringable,
        language: Stringable | None = None,
        attrs: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.language = language
        self.attrs = attrs or {}
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        if not target.prefer_md:
            return _htmp.element.code(self.content, self.attrs).source(indent=-1)
        return f"`{self.content}`"

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        return target.code_span.make(str(self.content))


class Directive(Element):

    def __init__(
        self,
        name: Stringable,
        args: MDContainer | None = None,
        options: dict[Stringable, Stringable | list[Stringable] | None] | None = None,
        content: MDContainer | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.name = name
        self.args = args
        self.options = options or {}
        self.content = content
        return

    @property
    def code_fence_count(self) -> int:
        return max(self.content.code_fence_count, 2) + 1

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:

        def options():
            if not self.options:
                return ""
            option_lines = []
            for key, value in self.options.items():
                if not value:
                    continue
                if value is True:
                    val_str = ""
                elif isinstance(value, (list, tuple)):
                    val_str = ", ".join(str(val).strip() for val in value)
                else:
                    val_str = str(value)
                    if "\n" in val_str:
                        val_content = "\n".join(f":{' ' * 3}{line}" for line in val_str.splitlines())
                        val_str = f"|\n{val_content}"
                option_lines.append(f":{key}: {val_str}".strip())
            return f"{"\n".join(option_lines)}\n"

        target = self._resolve_target(target)
        content = f"\n{self.content.source(target=target, filters=filters)}\n\n" if self.content else ""
        fence = target.fence * self.code_fence_count
        args = self.args.source(target=target, filters=filters) if self.args else ""
        start_line = f"{fence}{{{self.name}}} {args}"
        opts = options()
        return f"{start_line}\n{opts}{content}{fence}"


class DropDown(Element):

    def __init__(
        self,
        content: MDContainer,
        title: MDContainer | None = None,
        footer: MDContainer | None = None,
        opened: bool = False,
        color: Literal["primary", "secondary", "success", "danger", "warning", "info", "light", "dark", "muted"] | None = None,
        icon: str | None = None,
        octicon: str | None = None,
        chevron: Literal["right-down", "down-up"] | None = None,
        animate: Literal["fade-in", "fade-in-slide-down"] | None = None,
        margin: Literal["auto", 0, 1, 2, 3, 4, 5] | tuple[Literal["auto", 0, 1, 2, 3, 4, 5], ...] | None = None,
        name: Stringable | None = None,
        classes_container: list[Stringable] | None = None,
        classes_title: list[Stringable] | None = None,
        classes_body: list[Stringable] | None = None,
        class_rich: Stringable | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.title = title
        self.footer = footer
        self.opened = opened
        self.color = color
        self.icon = icon
        self.octicon = octicon
        self.chevron = chevron
        self.animate = animate
        self.margin = margin
        self.name = name
        self.classes_container = classes_container or []
        self.classes_title = classes_title or []
        self.classes_body = classes_body or []
        self.class_rich = class_rich
        return

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        content = self.content.source(target=target, filters=filters)
        title = self.title.source(target=target, filters=filters) if self.title else ""
        if self.icon:
            title = rich.text.Text.assemble(str(self.icon), title)
        footer = self.footer.source(target=target, filters=filters).strip() if self.footer else None
        config = target.dropdown_class.get(str(self.class_rich), target.dropdown)
        return config.make(content=content, title=title, subtitle=footer)

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        title = self.title.source(target=target, filters=filters).strip() if self.title else ""
        content = self.content.source(target=target, filters=filters).strip()
        footer = self.footer.source(target=target, filters=filters).strip() if self.footer else ""
        content_full = f"{content}\n\n---\n\n{footer}".strip()
        if target.direcive_dropdown:
            options = {
                "open": self.opened,
                "color": self.color,
                "icon": self.octicon,
                "chevron": self.chevron,
                "animate": self.animate,
                "margin": self.margin,
                "class-container": self.classes_container,
                "class-title": self.classes_title,
                "class-body": self.classes_body,
                "name": self.name,
            }
            return directive(
                name="dropdown",
                args=f"{self.icon} {title}" if self.icon and not self.octicon else title,
                options=options,
                content=content_full,
            ).source(target=target, filters=filters)
        title = f"{self.icon} {title}" if self.icon else self.title
        details_content = [_htmp.element.summary(title), _htmp.elementor.markdown(content)]
        return str(_htmp.element.details(details_content, {"open": self.opened}))


class FieldListItem(Element):
    def __init__(
        self,
        title: MDContainer,
        description: MDContainer | None = None,
        indent: int = 3,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.title = title
        self.description = description
        self.indent = indent
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        title = self.title.source(target=target, filters=filters)
        description = self.description.source(target=target, filters=filters) if self.description else ""
        indent = " " * (self.indent if target.field_list else 2)  # 2 for normal list
        description_indented = "\n".join(f"{indent}{line}" for line in description.splitlines()).strip()
        if target.field_list:
            return f":{title}: {description}".strip()
        return f"- **{title}**{f": {description_indented}" if description_indented else ''}"

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        item = (
            self.title.source(target=target, filters=filters),
            self.description.source(target=target, filters=filters) if self.description else ""
        )
        return target.field_list.make([item])


class FieldList(Element):

    def __init__(
        self,
        content: MDContainer,
        name: Stringable | None = None,
        classes: list[Stringable] | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.name = name
        self.classes = classes or []
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(target=target, filters=filters)
        if (self.classes or self.name) and target.attrs_block:
            return attribute(
                content=content,
                block=True,
                classes=self.classes,
                name=self.name,
            ).source(target=target, filters=filters)
        if self.name and target.target_anchor:
            return target_anchor(
                content=content,
                name=self.name,
            ).source(target=target, filters=filters)
        return content

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        items = [
            (
                item.title.source(target=target, filters=filters),
                item.description.source(target=target, filters=filters) if item.description else ""
            ) for item in self.content.elements(target=target, filters=filters)
        ]
        return target.field_list.make(items)

    def append(
        self,
        name: ContainerContentInputType | MDContainer | None = None,
        body: ContainerContentInputType | MDContainer | None = None,
        conditions: str | list[str] | None = None,
        key: str | int | None = None,
        indent: int = 4,
        content_separator_name: str = "",
        content_separator_body: str = "\n\n",
    ):
        list_item = field_list_item(
            title=name,
            description=body,
            indent=indent,
            content_separator_name=content_separator_name,
            content_separator_body=content_separator_body,
        )
        self.content.append(list_item, conditions=conditions, key=key)
        return


class FrontMatter(Element):

    def __init__(
        self,
        content: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content or {}
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        if not self.content:
            return ""
        content = _ps.write.to_yaml_string(data=self.content).strip()
        return f"---\n{content}\n---"


class Heading(Element):
    def __init__(
        self,
        content: MDContainer,
        level: Literal[1, 2, 3, 4, 5, 6] | Sequence[int] = 1,
        explicit_number: bool = False,
        name: Stringable | None = None,
        classes: list[Stringable] | None = None,
        attrs: dict | None = None,
        container: Stringable | None = "div",
        container_inline: Stringable | None = "span",
        attrs_container: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.level = list(level) if isinstance(level, _Sequence) else [1] * level
        self.content = content
        self.name = name
        self.classes = classes or []
        self.attrs = attrs or {}
        self.container = container
        self.container_inline = container_inline
        self.attrs_container = attrs_container or {}
        self.explicit_number = explicit_number
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = self._make_content(self.content.source(target=target, filters=filters))
        level = len(self.level)
        if not target.prefer_md:
            attrs = {"class": self.classes, "id": self.name}
            h = _htmp.elementor.heading(
                level=level,
                content=_htmp.elementor.markdown(content),
                attrs=self.attrs | attrs,
            ).source(indent=-1) if level < 7 else content
            return self._wrap(
                content=h,
                container=self.container if level < 7 else self.container_inline,
                attrs_container=self.attrs_container,
            )
        if level > 6:
            return f"**{content}**"
        heading_str = f"{'#' * level} {content}"
        if (self.classes or self.name) and target.attrs_block:
            return attribute(
                content=heading_str,
                block=True,
                classes=self.classes,
                name=self.name,
            ).source(target=target, filters=filters)
        if self.name and target.target_anchor:
            return target_anchor(
                content=heading_str,
                name=self.name,
            ).source(target=target, filters=filters)
        return heading_str

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        content = self._make_content(self.content.source(target=target, filters=filters))
        style = target.heading[min(len(self.level), len(target.heading)) - 1]
        return style.make(content=content)

    def _make_content(self, content: str) -> str:
        if not self.explicit_number:
            return content
        section_num = ".".join(str(num) for num in self.level)
        return f"{section_num}. {content}"


class HTML(Element):

    def __init__(
        self,
        content: MDContainer,
        tag: Stringable,
        attrs: dict | None = None,
        inline: bool = False,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.tag = tag
        self.attrs = attrs or {}
        self.inline = inline
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(target=target, filters=filters)
        error_msg = f"Element '{self.tag}' is not a valid HTML element."
        try:
            tag_func = getattr(_htmp.element, str(self.tag))
        except AttributeError:
            raise AttributeError(error_msg)
        if not isinstance(tag_func, _FunctionType):
            raise AttributeError(error_msg)
        if not self.inline:
            content = _htmp.elementor.markdown(content)
        return tag_func(content, self.attrs).source(indent=-1)


class InlineImage(Element):
    def __init__(
        self,
        src: Stringable,
        src_dark: Stringable | None = None,
        title: Stringable | None = None,
        alt: Stringable | None = None,
        height: Stringable | None = None,
        width: Stringable | None = None,
        align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
        link: Stringable | None = None,
        classes: list[Stringable] | None = None,
        name: Stringable | None = None,
        attrs_img: dict | None = None,
        attrs_source_light: dict | None = None,
        attrs_source_dark: dict | None = None,
        attrs_picture: dict | None = None,
        attrs_a: dict | None = None,
        container: Stringable | None = "span",
        attrs_container: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.src = src
        self.src_dark = src_dark
        self.title = title
        self.alt = alt
        self.height = height
        self.width = width
        self.align = align
        self.link = link
        self.classes = classes or []
        self.name = name
        self.attrs_img = attrs_img or {}
        self.attrs_source_light = attrs_source_light or {}
        self.attrs_source_dark = attrs_source_dark or {}
        self.attrs_picture = attrs_picture or {}
        self.attrs_a = attrs_a or {}
        self.container = container
        self.attrs_container = attrs_container or {}
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        img_attrs = {
            "src": self.src,
            "title": self.title,
            "alt": self.alt,
            "height": self.height,
            "width": self.width,
            "align": self.align,
            "class": self.classes,
            "id": self.name,
        } | self.attrs_img
        image = _htmp.elementor.picture_color_scheme(
            src_light=self.src,
            src_dark=self.src_dark,
            attrs_img=img_attrs,
            attrs_source_light=self.attrs_source_light,
            attrs_source_dark=self.attrs_source_dark,
            attrs_picture=self.attrs_picture,
        ) if self.src_dark and target.picture_theme else _htmp.element.img(img_attrs)
        if self.link:
            attrs_a = {"href": self.link, "alt": self.alt} | self.attrs_a
            image = _htmp.element.a(image, attrs_a)
        return self._wrap(content=str(image), container=self.container, attrs_container=self.attrs_container)


class Paragraph(Element):

    def __init__(
        self,
        content: MDContainer,
        name: Stringable | None = None,
        classes: list[Stringable] | None = None,
        attrs: dict | None = None,
        container: Stringable | None = "div",
        attrs_container: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.name = name
        self.classes = classes or []
        self.attrs = attrs or {}
        self.container = container
        self.attrs_container = attrs_container or {}
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(target=target, filters=filters)
        if not content:
            return ""
        if not target.prefer_md:
            ps = [
                _htmp.element.p(
                    parag.strip(),
                    self.attrs | {"class": self.classes, "id": self.name}
                ).source(indent=3)
                for parag in _re.split(r'\n\s*\n+', content)
            ]
            return self._wrap(
                content="\n".join(ps), container=self.container, attrs_container=self.attrs_container
            )
        if (self.classes or self.name) and target.attrs_block:
            return attribute(
                content=content,
                block=True,
                classes=self.classes,
                name=self.name,
            ).source(target=target, filters=filters)
        if self.name and target.target_anchor:
            return target_anchor(
                content=content,
                name=self.name,
            ).source(target=target, filters=filters)
        return content


class Rich(Element):

    def __init__(
        self,
        content: RenderableType,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        return

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        return self.content

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        return target.rich_export.export(self.content)


class TabItem(Element):

    def __init__(
        self,
        title: MDContainer,
        content: MDContainer,
        selected: bool = False,
        sync: Stringable | None = None,
        name: Stringable | None = None,
        classes_container: str | list[str] | None = None,
        classes_label: str | list[str] | None = None,
        classes_content: str | list[str] | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.title = title
        self.content = content
        self.selected = selected
        self.sync = sync
        self.name = name
        self.classes_container = classes_container
        self.classes_label = classes_label
        self.classes_content = classes_content
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        title = self.title.source(target=target, filters=filters)
        content = self.content.source(target=target, filters=filters)
        options = {
            "selected": self.selected,
            "sync": self.sync,
            "name": self.name,
            "class-container": self.classes_container,
            "class-label": self.classes_label,
            "class-content": self.classes_content,
        }
        return directive(
            name="tab-item",
            args=title,
            options=options,
            content=content,
        ).source(target=target, filters=filters)

    @property
    def code_fence_count(self):
        return max(self.content.code_fence_count, 2) + 1


class TabSet(Element):

    def __init__(
        self,
        content: MDContainer,
        sync_group: Stringable | None = None,
        classes: list[Stringable] | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.sync_group = sync_group
        self.classes = classes or []
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        options = {
            "sync-group": self.sync_group,
            "class": self.classes,
        }
        return directive(
            name="tab-set",
            options=options,
            content=self.content,
        ).source(target=target, filters=filters)

    def append(
        self,
        *contents: ContainerContentInputType | MDContainer,
        title: ContainerContentInputType | MDContainer | None = None,
        conditions: str | list[str] | None = None,
        key: str | int | None = None,
        selected: bool = False,
        sync: Stringable | None = None,
        name: Stringable | None = None,
        class_container: str | list[str] | None = None,
        class_label: str | list[str] | None = None,
        class_content: str | list[str] | None = None,
        content_separator_title: str = "",
        content_separator_content: str = "\n\n",
    ):
        tab = tab_item(
            *contents,
            title=title,
            selected=selected,
            sync=sync,
            name=name,
            classes_container=class_container,
            classes_label=class_label,
            classes_content=class_content,
            content_separator_title=content_separator_title,
            content_separator_content=content_separator_content,
        )
        self.content.append(tab, conditions=conditions, key=key)
        return


class Table(Element):

    def __init__(
        self,
        rows: list[tuple[list[tuple[MDContainer, HTMLAttrsType]], HTMLAttrsType]],
        caption: Stringable | None = None,
        align_table: Literal["left", "center", "right"] | None = None,
        align_columns: Literal["left", "center", "right"] | list[Literal["left", "center", "right"]] | None = None,
        num_rows_header: int = 0,
        num_rows_footer: int = 0,
        num_cols_stub: int = 0,
        width_table: Stringable | None = None,
        width_columns: list[int] | Literal["auto"] | None = None,
        name: Stringable | None = None,
        classes: list[Stringable] | None = None,
        attrs_figure: HTMLAttrsType = None,
        attrs_caption: HTMLAttrsType = None,
        attrs_table: HTMLAttrsType = None,
        attrs_body: HTMLAttrsType = None,
        attrs_head: HTMLAttrsType = None,
        attrs_foot: HTMLAttrsType = None,
        attrs_tr: HTMLAttrsType = None,
        attrs_th: HTMLAttrsType = None,
        attrs_td: HTMLAttrsType = None,
        attrs_body_tr: HTMLAttrsType = None,
        attrs_body_th: HTMLAttrsType = None,
        attrs_body_td: HTMLAttrsType = None,
        attrs_head_tr: HTMLAttrsType = None,
        attrs_head_th: HTMLAttrsType = None,
        attrs_head_td: HTMLAttrsType = None,
        attrs_foot_tr: HTMLAttrsType = None,
        attrs_foot_th: HTMLAttrsType = None,
        attrs_foot_td: HTMLAttrsType = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.rows = rows
        self.caption = caption
        self.align_table = align_table
        self.align_columns = align_columns
        self.num_rows_header = num_rows_header
        self.num_rows_footer = num_rows_footer
        self.num_cols_stub = num_cols_stub
        self.width_table = width_table
        self.width_columns = width_columns
        self.name = name
        self.classes = classes or []
        self.attrs_figure = attrs_figure or {}
        self.attrs_caption = attrs_caption or {}
        self.attrs_table = attrs_table or {}
        self.attrs_body = attrs_body or {}
        self.attrs_head = attrs_head or {}
        self.attrs_foot = attrs_foot or {}
        self.attrs_tr = attrs_tr or {}
        self.attrs_th = attrs_th or {}
        self.attrs_td = attrs_td or {}
        self.attrs_body_tr = attrs_body_tr or {}
        self.attrs_body_th = attrs_body_th or {}
        self.attrs_body_td = attrs_body_td or {}
        self.attrs_head_tr = attrs_head_tr or {}
        self.attrs_head_th = attrs_head_th or {}
        self.attrs_head_td = attrs_head_td or {}
        self.attrs_foot_tr = attrs_foot_tr or {}
        self.attrs_foot_th = attrs_foot_th or {}
        self.attrs_foot_td = attrs_foot_td or {}
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        if not target.prefer_md:
            rows_str = []
            for row, row_attrs in self.rows:
                row_str = []
                for cell, cell_attrs in row:
                    cell_str = cell.source(target=target, filters=filters)
                    row_str.append((_htmp.elementor.markdown(cell_str), cell_attrs))
                rows_str.append((row_str, row_attrs))
            table_ = _htmp.elementor.table_from_rows(
                rows_head=rows_str[:self.num_rows_header],
                rows_body=rows_str[self.num_rows_header:-self.num_rows_footer],
                rows_foot=rows_str[-self.num_rows_footer:],
                as_figure=True,
                caption=self.caption,
                num_cols_stub=self.num_cols_stub,
                attrs_figure=self.attrs_figure,
                attrs_caption=self.attrs_caption,
                attrs_table=self.attrs_table,
                attrs_body=self.attrs_body,
                attrs_head=self.attrs_head,
                attrs_foot=self.attrs_foot,
                attrs_tr=self.attrs_tr,
                attrs_th=self.attrs_th,
                attrs_td=self.attrs_td,
                attrs_body_tr=self.attrs_body_tr,
                attrs_body_th=self.attrs_body_th,
                attrs_body_td=self.attrs_body_td,
                attrs_head_tr=self.attrs_head_tr,
                attrs_head_th=self.attrs_head_th,
                attrs_head_td=self.attrs_head_td,
                attrs_foot_tr=self.attrs_foot_tr,
                attrs_foot_th=self.attrs_foot_th,
                attrs_foot_td=self.attrs_foot_td,
            ).source(indent=-1)
            return table_
        if target.directive_list_table:
            rows = []
            for row, _ in self.rows:
                cells = [cell for cell, _ in row]
                rows.append(unordered_list(*cells))
            table_content = unordered_list(*rows)
            return directive(
                name="list-table",
                args=self.caption,
                options={
                    "align": self.align_table,
                    "header-rows": self.num_rows_header,
                    "stub-columns": self.num_cols_stub,
                    "width": self.width_table,
                    "widths": self.width_columns,
                    "class": self.classes,
                    "name": self.name,
                },
                content=table_content,
            ).source(target=target, filters=filters)
        rows = []
        for row, _ in self.rows:
            cells = []
            for cell, _ in row:
                cell_str = cell.source(target=target, filters=filters)
                cells.append(cell_str)
            rows.append(f"| {" | ".join(cells)} |")
        num_cols = len(self.rows[0][0])
        delimiter_row = []
        for col_idx in range(num_cols):
            if not self.align_columns:
                delimiter_row.append("-----")
                continue
            align = self.align_columns[col_idx] if isinstance(self.align_columns, list) else self.align_columns
            if align == "left":
                delimiter_row.append(":----")
            elif align == "right":
                delimiter_row.append("----:")
            else:
                delimiter_row.append(":---:")
        delimiter_row_str = f"| {' | '.join(delimiter_row)} |"
        rows.insert(1, delimiter_row_str)
        table_ = "\n".join(rows)
        if target.directive_table:
            return directive(
                name="table",
                args=self.caption,
                options={
                    "align": self.align_table,
                    "width": self.width_table,
                    "widths": self.width_columns,
                },
                content=table_,
            ).source(target=target, filters=filters)
        return table_


class TargetAnchor(Element):

    def __init__(
        self,
        content: _MDITRenderable | Stringable,
        name: Stringable,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.name = name
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(target=target, filters=filters) if isinstance(self.content, _MDITRenderable) else str(self.content)
        name = str(self.name)
        if not (target.target_anchor and name):
            return content
        return f"({name})=\n{content.lstrip()}"


class ThematicBreak(Element):
    def __init__(
        self,
        name: Stringable | None = None,
        classes: list[Stringable] | None = None,
        attrs: dict | None = None,
        container: Stringable | None = "div",
        attrs_container: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.name = name
        self.classes = classes or []
        self.attrs = attrs or {}
        self.container = container
        self.attrs_container = attrs_container or {}
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        hr = _htmp.element.hr(self.attrs | {"class": self.classes, "id": self.name}).source(indent=-1)
        return self._wrap(content=hr, container=self.container, attrs_container=self.attrs_container)


class TocTree(Element):

    def __init__(
        self,
        content: MDContainer,
        glob: Stringable | None = None,
        caption: Stringable | None = None,
        hidden: bool = False,
        include_hidden: bool = False,
        max_depth: int | None = None,
        titles_only: bool = False,
        reversed: bool = False,
        name: Stringable | None = None,
        numbered: bool | int = False,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.glob = glob
        self.caption = caption
        self.hidden = hidden
        self.include_hidden = include_hidden
        self.max_depth = max_depth
        self.titles_only = titles_only
        self.reversed = reversed
        self.name = name
        self.numbered = numbered
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(target=target, filters=filters)
        options = {
            "glob": self.glob,
            "caption": self.caption,
            "hidden": self.hidden,
            "includehidden": self.include_hidden,
            "maxdepth": self.max_depth,
            "titlesonly": self.titles_only,
            "reversed": self.reversed,
            "name": self.name,
            "numbered": self.numbered,
        }
        return directive(
            name="toctree",
            args=None,
            options=options,
            content=content
        ).source(target=target, filters=filters)


class Toggle(Element):

    def __init__(
        self,
        content: MDContainer,
        title: Stringable | None = None,
        opened: bool = False,
        attrs_details: dict | None = None,
        attrs_summary: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.title = title
        self.attrs_details = attrs_details or {}
        self.attrs_summary = attrs_summary or {}
        self.opened = opened
        return

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        if target.directive_toggle:
            return directive(
                name="toggle",
                options={"show": self.opened},
                content=self.content,
            ).source(target=target, filters=filters)
        content= _htmp.elementor.markdown(self.content.source(target=target, filters=filters))
        summary = _htmp.element.summary(self.title, self.attrs_summary)
        return _htmp.element.details([summary, content], self.attrs_details).source(indent=-1)


class OrderedListItem(Element):

    def __init__(
        self,
        content: MDContainer,
        number: int,
        style: Literal["a", "A", "i", "I", "1"] = "1",
        attrs_li: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.number = number
        self.style = style
        self.attrs_li = attrs_li or {}
        return

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        content = self.content.source(target=target, filters=filters)
        return target.ordered_list.make(content, start=self.number)

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(target=target, filters=filters)
        if not target.prefer_md:
            attrs = {
                "type": self.style,
                "value": self.number,
            } | self.attrs_li
            attrs.setdefault("style", {})["list-style-type"] = self.style
            return _htmp.element.li(_htmp.elementor.markdown(content), attrs).source(indent=-1)
        marker = f"{self.number}. "
        marker_len = len(marker)
        indent = marker_len * " "
        content_indented = "\n".join(f"{indent}{line}" for line in content.splitlines())
        return f"{marker}{content_indented.strip()}"


class OrderedList(Element):

    HTML_STYLE_TO_MYST = {
        "a": "lower-alpha",
        "A": "upper-alpha",
        "i": "lower-roman",
        "I": "upper-roman",
        "1": "decimal",
    }

    def __init__(
        self,
        content: MDContainer,
        classes: list[Stringable] | None = None,
        name: Stringable | None = None,
        start: int | None = None,
        style: Literal["a", "A", "i", "I", "1"] = "1",
        attrs_ol: dict | None = None,
        attrs_li: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)

        self.content = content
        self.start = start
        self.style = style
        self.classes = classes or []
        self.name = name
        self.attrs_ol = attrs_ol or {}
        self.attrs_li = attrs_li or {}
        return

    def append(
        self,
        *contents,
        conditions: str | list[str] | None = None,
        key: str | int | None = None,
        style: Literal["a", "A", "i", "I", "1"] = "1",
        attrs_li: dict | None = None,
        content_separator: str = "\n\n",
    ) -> OrderedListItem:
        list_item = ordered_list_item(
            *contents,
            number=len(self.content) + 1,
            style=style,
            attrs_li=attrs_li,
            content_separator=content_separator,
            target_configs=self.target_configs,
            target_default=self.target_default,
        )
        self.content.append(content=list_item, conditions=conditions, key=key)
        return list_item

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        items = [
            item.content.source(filters=filters)
            for item in self.content.elements(target=target, filters=filters)
        ]
        return target.ordered_list.make(*items, start=self.start)

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        items = self.content.elements(target=target, filters=filters, source=True)
        if not items:
            return ""
        if not target.prefer_md:
            attrs_ol = {
               "class": self.classes,
               "id": self.name,
               "style": {"list-style-type": self.style}
            } | self.attrs_ol
            return _htmp.elementor.ordered_list(
                items=[_htmp.elementor.markdown(item) for item in items],
                type=self.style,
                attrs_li=self.attrs_li,
                attrs_ol=attrs_ol,
            ).source(indent=-1)
        list_items = []
        start = self.start if self.start is not None else 1
        for idx, item in enumerate(items):
            marker = f"{idx + start}. "
            marker_len = len(marker)
            item_lines = item.splitlines()
            item_lines = [f"{marker}{item_lines[0]}"] + [
                f"{' ' * marker_len}{line}" for line in item_lines[1:]
            ]
            list_items.extend(item_lines)
        list_str = "\n".join(list_items)
        if (self.classes or self.name or self.style != "1") and target.attrs_block:
            return attribute(
                content=list_str,
                block=True,
                classes=self.classes,
                name=self.name,
                attrs={"style": self.HTML_STYLE_TO_MYST[self.style]} if self.style != "1" else {},
            ).source(target=target, filters=filters)
        if self.name and target.target_anchor:
            return target_anchor(
                content=list_str,
                name=self.name,
            ).source(target=target, filters=filters)
        return list_str


class UnOrderedListItem(Element):

    def __init__(
        self,
        content: MDContainer,
        attrs_li: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.attrs_li = attrs_li or {}
        return

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        content = self.content.source(target=target, filters=filters)
        return target.unordered_list.make(content)

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(target=target, filters=filters)
        if not target.prefer_md:
            return _htmp.element.li(_htmp.elementor.markdown(content), self.attrs_li).source(indent=-1)
        marker = "- "
        marker_len = len(marker)
        indent = marker_len * " "
        content_indented = "\n".join(f"{indent}{line}" for line in content.splitlines())
        return f"{marker}{content_indented.strip()}"


class UnOrderedList(Element):

    def __init__(
        self,
        content: MDContainer,
        classes: list[Stringable] | None = None,
        name: Stringable | None = None,
        style: Literal["circle", "disc", "square"] = "disc",
        attrs_ul: dict | None = None,
        attrs_li: dict | None = None,
        target_configs: TargetConfigs = None,
        target_default: TargetConfigs = "sphinx",
    ):
        super().__init__(target_configs=target_configs, target_default=target_default)
        self.content = content
        self.style = style
        self.classes = classes or []
        self.name = name
        self.attrs_ul = attrs_ul or {}
        self.attrs_li = attrs_li or {}
        return

    def append(
        self,
        *contents,
        conditions: str | list[str] | None = None,
        key: str | int | None = None,
        attrs_li: dict | None = None,
        content_separator: str = "\n\n",
    ) -> UnOrderedListItem:
        list_item = unordered_list_item(
            *contents,
            attrs_li=attrs_li,
            content_separator=content_separator,
            target_configs=self.target_configs,
            target_default=self.target_default,
        )
        self.content.append(content=list_item, conditions=conditions, key=key)
        return list_item

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        items = [
            item.content.source(filters=filters)
            for item in self.content.elements(target=target, filters=filters)
        ]
        return target.unordered_list.make(*items)

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        items = self.content.elements(target=target, filters=filters)
        if not target.prefer_md:
            attrs_ul = {
                "class": self.classes,
                "id": self.name,
                "style": {"list-style-type": self.style}
            } | self.attrs_ul
            return _htmp.elementor.unordered_list(
                items=[_htmp.elementor.markdown(item.content.source(target=target, filters=filters)) for item in items],
                type=self.style,
                attrs_li=self.attrs_li,
                attrs_ul=attrs_ul,
            ).source(indent=-1)
        list_str = "\n".join([item.source(target=target, filters=filters) for item in items])
        if (self.classes or self.name) and target.attrs_block:
            return attribute(
                content=list_str,
                block=True,
                classes=self.classes,
                name=self.name,
            ).source(target=target, filters=filters)
        if self.name and target.target_anchor:
            return target_anchor(
                content=list_str,
                name=self.name,
            ).source(target=target, filters=filters)
        return list_str


def admonition(
    *contents: ContainerContentInputType | MDContainer,
    type: Literal[
        "note",
        "important",
        "hint",
        "seealso",
        "tip",
        "attention",
        "caution",
        "warning",
        "danger",
        "error"
    ],
    title: ContainerContentInputType | MDContainer | None = None,
    dropdown: bool = False,
    opened: bool = False,
    classes: list[Stringable] | None = None,
    add_type_class: bool = True,
    name: Stringable | None = None,
    type_github: Literal["note", "tip", "important", "warning", "caution"] | None = None,
    title_bold: bool = True,
    title_tight: bool = True,
    emoji: str | None = None,
    content_separator_title: str = "",
    content_separator_content: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> Admonition:
    """Create a [MyST admonition](https://myst-parser.readthedocs.io/en/latest/syntax/admonitions.html).

    Parameters
    ----------
    type : {'note', 'important', 'hint', 'seealso', 'tip', 'attention', 'caution', 'warning', 'danger', 'error'}
        Admonition type.
    title : ElementContentType
        Admonition title.
    content : ElementContentInputType
        Admonition content.
    class_ : str | list[str], optional
        CSS class names to add to the admonition. These must conform to the
        [identifier normalization rules](https://docutils.sourceforge.io/docs/ref/rst/directives.html#identifier-normalization).
    name : Stringable, optional
        A reference target name for the admonition
        (for [cross-referencing](https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html#syntax-referencing)).
    fence: {'`', '~', ':'}, default: '`'
        Fence character.
    """
    title = _to_container(
        (title, ),
        content_separator=content_separator_title,
        target_configs=target_configs,
        target_default=target_default,
    )
    content = _to_container(
        contents,
        content_separator=content_separator_content,
        target_configs=target_configs,
        target_default=target_default,
    )
    return Admonition(
        type=type,
        title=title,
        content=content,
        dropdown=dropdown,
        opened=opened,
        classes=classes,
        add_type_class=add_type_class,
        name=name,
        type_github=type_github,
        title_bold=title_bold,
        title_tight=title_tight,
        emoji=emoji,
        target_configs=target_configs,
        target_default=target_default,
    )


def attribute(
    content: _MDITRenderable | Stringable,
    block: bool,
    classes: Stringable | list[Stringable] | None = None,
    name: Stringable | None = None,
    attrs: dict | None = None,
    comment: Stringable | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
):
    return Attribute(
        content=content,
        block=block,
        classes=classes,
        name=name,
        attrs=attrs,
        comment=comment,
        target_configs=target_configs,
        target_default=target_default,
    )


def badge(
    service: str = "generic",
    endpoint: str | None = None,
    args: dict | None = None,
    label: str | None = None,
    style: str | None = None,
    color: str | None = None,
    label_color: str | None = None,
    logo_color: str | None = None,
    logo_width: str | None = None,
    logo_size: str | None = None,
    logo: str | None = None,
    logo_type: str | None = None,
    logo_media_type: str | None = None,
    cache_seconds: int | None = None,
    color_dark: str | None = None,
    label_color_dark: str | None = None,
    logo_color_dark: str | None = None,
    logo_dark: str | None = None,
    logo_type_dark: str | None = None,
    logo_media_type_dark: str | None = None,
    title: Stringable | None = None,
    alt: Stringable | None = None,
    height: Stringable | None = None,
    width: Stringable | None = None,
    align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
    link: Stringable | None = None,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    attrs_img: dict | None = None,
    attrs_source_light: dict | None = None,
    attrs_source_dark: dict | None = None,
    attrs_picture: dict | None = None,
    attrs_a: dict | None = None,
    container: Stringable | None = "span",
    attrs_container: dict | None = None,
    merge_params: bool = True,
    use_defaults: bool = True,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> InlineImage:
    inputs = locals()
    params_light, params_dark = _make_badge_params(inputs)
    bdg = _bdg.create(
        platform="shields",
        service=service,
        endpoint=endpoint,
        args=args,
        params_light=params_light,
        params_dark=params_dark,
        default_light=True,
        merge_params=merge_params,
        use_defaults=use_defaults,
    )
    image = inline_image(
        src=bdg.url(light=True),
        src_dark=bdg.url(light=False) if params_dark else None,
        title=title or bdg.attrs_img.get("title"),
        alt=alt or bdg.attrs_img.get("alt"),
        height=height,
        width=width,
        align=align,
        link=link or bdg.attrs_a.get("href"),
        classes=classes,
        name=name,
        attrs_img=attrs_img,
        attrs_source_light=attrs_source_light,
        attrs_source_dark=attrs_source_dark,
        attrs_picture=attrs_picture,
        attrs_a=attrs_a,
        container=container,
        attrs_container=attrs_container,
        target_configs=target_configs,
        target_default=target_default,
    )
    return image


def badges(
    *items: dict | str,
    separator: int | str = 1,
    service: str = "generic",
    endpoint: str | None = None,
    args: dict | None = None,
    label: str | None = None,
    style: str | None = None,
    color: str | None = None,
    label_color: str | None = None,
    logo_color: str | None = None,
    logo_width: str | None = None,
    logo_size: str | None = None,
    logo: str | None = None,
    logo_type: str | None = None,
    logo_media_type: str | None = None,
    cache_seconds: int | None = None,
    color_dark: str | None = None,
    label_color_dark: str | None = None,
    logo_color_dark: str | None = None,
    logo_dark: str | None = None,
    logo_type_dark: str | None = None,
    logo_media_type_dark: str | None = None,
    title: Stringable | None = None,
    alt: Stringable | None = None,
    height: Stringable | None = None,
    width: Stringable | None = None,
    align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
    link: Stringable | None = None,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    attrs_img: dict | None = None,
    attrs_source_light: dict | None = None,
    attrs_source_dark: dict | None = None,
    attrs_picture: dict | None = None,
    attrs_a: dict | None = None,
    container: Stringable | None = "span",
    attrs_container: dict | None = None,
    container_conditions: str | list[str] | None = None,
    merge_params: bool = True,
    use_defaults: bool = True,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> MDContainer:
    default = locals()
    for top_level_param in ("items", "separator", "container", "attrs_container", "container_conditions"):
        default.pop(top_level_param)
    gradient = _make_badge_gradients(inputs=default, count_items=len(items))
    badge_list = []
    for idx, badge_settings in enumerate(items):
        if isinstance(badge_settings, str):
            badge_settings = {
                "service": "static",
                "args": {
                    "message": badge_settings
                },
            }
        badge_settings = default | badge_settings
        for theme in ("light", "dark"):
            # Set gradient colors if available
            for color in ("color", "label_color", "logo_color"):
                key = color if theme == "light" else f"{color}_dark"
                gradient_colors = gradient.get(key)
                if gradient_colors and key not in badge_settings:
                    # Only set gradient colors if badge doesn't define a corresponding color
                    badge_settings[key] = gradient_colors[idx].css_hex()

        badge_list.append(badge(**badge_settings))
    return _mdit.container(
        *badge_list,
        content_separator="&nbsp;" * separator if isinstance(separator, int) else str(separator),
        html_container=container,
        html_container_attrs=attrs_container,
        html_container_conditions=container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )


def block_image(
    src: Stringable,
    src_dark: Stringable | None = None,
    title: Stringable | None = None,
    alt: Stringable | None = None,
    height: Stringable | None = None,
    width: Stringable | None = None,
    scale: Stringable | None = None,
    align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
    link: Stringable | None = None,
    classes: list[Stringable] | None = None,
    classes_light: list[Stringable] | None = None,
    classes_dark: list[Stringable] | None = None,
    name: Stringable | None = None,
    caption: ContainerContentInputType | MDContainer | None = None,
    figure_width: Stringable | None = None,
    classes_figure: list[Stringable] | None = None,
    attrs_img: dict | None = None,
    attrs_source_light: dict | None = None,
    attrs_source_dark: dict | None = None,
    attrs_picture: dict | None = None,
    attrs_figcaption: dict | None = None,
    attrs_figure: dict | None = None,
    attrs_a: dict | None = None,
    container: Stringable | None = "div",
    attrs_container: dict | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> BlockImage:
    caption = _to_container(
        (caption, ),
        content_separator="\n",
        target_configs=target_configs,
        target_default=target_default,
    )
    return BlockImage(
        src=src,
        src_dark=src_dark,
        title=title,
        alt=alt,
        height=height,
        width=width,
        scale=scale,
        align=align,
        link=link,
        classes=classes,
        name=name,
        caption=caption,
        width_figure=figure_width,
        classes_light=classes_light,
        classes_dark=classes_dark,
        classes_figure=classes_figure,
        attrs_img=attrs_img,
        attrs_source_light=attrs_source_light,
        attrs_source_dark=attrs_source_dark,
        attrs_picture=attrs_picture,
        attrs_figcaption=attrs_figcaption,
        attrs_figure=attrs_figure,
        attrs_a=attrs_a,
        container=container,
        attrs_container=attrs_container,
        target_configs=target_configs,
        target_default=target_default,
    )


def block_quote(
    *contents: ContainerContentInputType | MDContainer,
    cite: ContainerContentInputType | MDContainer = None,
    name: Stringable | None = None,
    classes: list[Stringable] | None = None,
    attrs: dict | None = None,
    attrs_cite: dict | None = None,
    container: Stringable | None = "div",
    attrs_container: dict | None = None,
    content_separator: str = "\n",
    content_separator_cite: str = ", ",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> BlockQuote:
    content = _to_container(
        contents,
        content_separator=content_separator,
        target_configs=target_configs,
        target_default=target_default,
    )
    cite = _to_container(
        (cite, ),
        content_separator=content_separator_cite,
        target_configs=target_configs,
        target_default=target_default,
    )
    return BlockQuote(
        content=content,
        cite=cite,
        name=name,
        classes=classes,
        attrs=attrs,
        attrs_cite=attrs_cite,
        container=container,
        attrs_container=attrs_container,
        target_configs=target_configs,
        target_default=target_default,
    )


def button(
    text: str | None = None,
    style: str | None = None,
    color: str | None = None,
    logo_color: str | None = None,
    logo_width: str | None = None,
    logo_size: str | None = None,
    logo: str | None = None,
    logo_type: str | None = None,
    logo_media_type: str | None = None,
    cache_seconds: int | None = None,
    color_dark: str | None = None,
    logo_color_dark: str | None = None,
    logo_dark: str | None = None,
    logo_type_dark: str | None = None,
    logo_media_type_dark: str | None = None,
    title: Stringable | None = None,
    alt: Stringable | None = None,
    height: Stringable | None = None,
    width: Stringable | None = None,
    align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
    link: Stringable | None = None,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    attrs_img: dict | None = None,
    attrs_source_light: dict | None = None,
    attrs_source_dark: dict | None = None,
    attrs_picture: dict | None = None,
    attrs_a: dict | None = None,
    container: Stringable | None = "span",
    attrs_container: dict | None = None,
    merge_params: bool = True,
    use_defaults: bool = True,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> InlineImage:
    return badge(
        service="static",
        args={"message": text},
        style=style,
        color=color,
        logo_color=logo_color,
        logo_width=logo_width,
        logo_size=logo_size,
        logo=logo,
        logo_type=logo_type,
        logo_media_type=logo_media_type,
        cache_seconds=cache_seconds,
        color_dark=color_dark,
        logo_color_dark=logo_color_dark,
        logo_dark=logo_dark,
        logo_type_dark=logo_type_dark,
        logo_media_type_dark=logo_media_type_dark,
        title=title,
        alt=alt,
        height=height,
        width=width,
        align=align,
        link=link,
        classes=classes,
        name=name,
        attrs_img=attrs_img,
        attrs_source_light=attrs_source_light,
        attrs_source_dark=attrs_source_dark,
        attrs_picture=attrs_picture,
        attrs_a=attrs_a,
        container=container,
        attrs_container=attrs_container,
        merge_params=merge_params,
        use_defaults=use_defaults,
        target_configs=target_configs,
        target_default=target_default,
    )


def buttons(
    *items: dict | str,
    separator: int | str = 1,
    style: str | None = None,
    color: str | None = None,
    logo_color: str | None = None,
    logo_width: str | None = None,
    logo_size: str | None = None,
    logo: str | None = None,
    logo_type: str | None = None,
    logo_media_type: str | None = None,
    cache_seconds: int | None = None,
    color_dark: str | None = None,
    logo_color_dark: str | None = None,
    logo_dark: str | None = None,
    logo_type_dark: str | None = None,
    logo_media_type_dark: str | None = None,
    title: Stringable | None = None,
    alt: Stringable | None = None,
    height: Stringable | None = None,
    width: Stringable | None = None,
    align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
    link: Stringable | None = None,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    attrs_img: dict | None = None,
    attrs_source_light: dict | None = None,
    attrs_source_dark: dict | None = None,
    attrs_picture: dict | None = None,
    attrs_a: dict | None = None,
    container: Stringable | None = "span",
    attrs_container: dict | None = None,
    merge_params: bool = True,
    use_defaults: bool = True,
    container_conditions: str | list[str] | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> MDContainer:
    default = locals()
    for top_level_param in ("items", "separator", "container", "attrs_container", "container_conditions"):
        default.pop(top_level_param)
    gradient = _make_badge_gradients(inputs=default, count_items=len(items))
    badge_list = []
    for idx, badge_settings in enumerate(items):
        if isinstance(badge_settings, str):
            badge_settings = {"text": badge_settings}
        badge_settings = default | badge_settings
        for theme in ("light", "dark"):
            # Set gradient colors if available
            for color in ("color", "label_color", "logo_color"):
                key = color if theme == "light" else f"{color}_dark"
                gradient_colors = gradient.get(key)
                if gradient_colors and key not in badge_settings:
                    # Only set gradient colors if badge doesn't define a corresponding color
                    badge_settings[key] = gradient_colors[idx]
        badge_list.append(button(**badge_settings))
    return _mdit.container(
        *badge_list,
        content_separator="&nbsp;" * separator if isinstance(separator, int) else str(separator),
        html_container=container,
        html_container_attrs=attrs_container,
        html_container_conditions=container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )


def card(
    header: ContainerContentInputType | MDContainer = None,
    title: Stringable | None = None,
    body: ContainerContentInputType | MDContainer = None,
    footer: ContainerContentInputType | MDContainer = None,
    width: Literal["auto"] | int | None = None,
    margin: Literal["auto", 0, 1, 2, 3, 4, 5] | tuple[
        Literal["auto", 0, 1, 2, 3, 4, 5], ...] | None = None,
    text_align: Literal["left", "center", "right", "justify"] | None = None,
    img_background: Stringable | None = None,
    img_top: Stringable | None = None,
    img_bottom: Stringable | None = None,
    img_alt: Stringable | None = None,
    link: Stringable | None = None,
    link_type: Literal["url", "ref", "doc", "any"] | None = None,
    link_alt: Stringable | None = None,
    shadow: Literal["sm", "md", "lg", "none"] | None = None,
    classes_card: list[str] | None = None,
    classes_header: list[str] | None = None,
    classes_body: list[str] | None = None,
    classes_footer: list[str] | None = None,
    classes_title: list[str] | None = None,
    classes_img_top: list[str] | None = None,
    classes_img_bottom: list[str] | None = None,
    content_separator_header: str = "\n\n",
    content_separator_body: str = "\n\n",
    content_separator_footer: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> Card:
    header = _to_container(
        (header, ),
        content_separator=content_separator_header,
        target_configs=target_configs,
        target_default=target_default,
    )
    body = _to_container(
        (body, ),
        content_separator=content_separator_body,
        target_configs=target_configs,
        target_default=target_default,
    )
    footer = _to_container(
        (footer, ),
        content_separator=content_separator_footer,
        target_configs=target_configs,
        target_default=target_default,
    )
    return Card(
        header=header,
        title=title,
        body=body,
        footer=footer,
        width=width,
        margin=margin,
        text_align=text_align,
        img_background=img_background,
        img_top=img_top,
        img_bottom=img_bottom,
        img_alt=img_alt,
        link=link,
        link_type=link_type,
        link_alt=link_alt,
        shadow=shadow,
        classes_card=classes_card,
        classes_header=classes_header,
        classes_body=classes_body,
        classes_footer=classes_footer,
        classes_title=classes_title,
        classes_img_top=classes_img_top,
        classes_img_bottom=classes_img_bottom,
        target_configs=target_configs,
        target_default=target_default,
    )


def code_block(
    content: Stringable | None = None,
    language: Stringable | None = None,
    caption: Stringable | None = None,
    line_num: bool = False,
    line_num_start: int | None = None,
    emphasize_lines: list[int] | None = None,
    force: bool = False,
    name: Stringable | None = None,
    classes: Stringable | list[Stringable] | None = None,
    degrade_to_diff: bool = True,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> CodeBlock:
    """Create a MyST [code block directive](https://myst-parser.readthedocs.io/en/latest/syntax/code_and_apis.html#adding-a-caption).

    Parameters
    ----------
    language : str, optional
        Language of the code, e.g. 'python', 'json', 'bash', 'html'.
    content : ElementContentType
        Code to be included in the code block.
    caption : ElementContentType, optional
        Caption for the code block.
    class_ : list[str], optional
        CSS class names to add to the code block. These must conform to the
        [identifier normalization rules](https://docutils.sourceforge.io/docs/ref/rst/directives.html#identifier-normalization).
    name : Stringable, optional
        A reference target name for the code block
        (for [cross-referencing](https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html#syntax-referencing)).
    lineno_start : int, optional
        Starting line number for the code block.
    emphasize_lines : list[int], optional
        Line numbers to highlight in the code block.
        Note that `lineno-start` must be set for this to work.
    force : bool, default: False
        Allow minor errors on highlighting to be ignored.
    fence: {'`', '~', ':'}, default: '`'
        Fence character.
    """
    return CodeBlock(
        content=content,
        language=language,
        caption=caption,
        line_num=line_num,
        line_num_start=line_num_start,
        emphasize_lines=emphasize_lines,
        force=force,
        name=name,
        classes=classes,
        degrade_to_diff=degrade_to_diff,
        target_configs=target_configs,
        target_default=target_default,
    )


def code_span(
    content: Stringable,
    language: Stringable | None = None,
    attrs: dict | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> CodeSpan:
    return CodeSpan(
        content=content,
        language=language,
        attrs=attrs,
        target_configs=target_configs,
        target_default=target_default,
    )


def directive(
    name: Stringable,
    args: ContainerContentInputType | MDContainer = None,
    options: dict[Stringable, Stringable | list[Stringable] | None] | None = None,
    content: ContainerContentInputType | MDContainer = None,
    content_separator_args: str = " ",
    content_separator_content: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> Directive:
    args = _to_container((args, ), content_separator=content_separator_args)
    content = _to_container((content, ), content_separator=content_separator_content)
    return Directive(
        name=name,
        args=args,
        options=options,
        content=content,
        target_configs=target_configs,
        target_default=target_default,
    )


def dropdown(
    *contents: ContainerContentInputType | MDContainer,
    title: Stringable | None = None,
    footer: Stringable | None = None,
    opened: bool = False,
    color: Literal["primary", "secondary", "success", "danger", "warning", "info", "light", "dark"] | None = None,
    icon: str | None = None,
    octicon: str | None = None,
    chevron: Literal["right-down", "down-up"] | None = None,
    animate: Literal["fade-in", "fade-in-slide-down"] | None = None,
    margin: Literal["auto", 0, 1, 2, 3, 4, 5] | tuple[Literal["auto", 0, 1, 2, 3, 4, 5], ...] | None = None,
    name: Stringable | None = None,
    classes_container: list[Stringable] | None = None,
    classes_title: list[Stringable] | None = None,
    classes_body: list[Stringable] | None = None,
    class_rich: Stringable | None = None,
    content_separator: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> DropDown:
    return DropDown(
        content=_to_container(
            contents,
            content_separator=content_separator,
            target_configs=target_configs,
            target_default=target_default,
        ),
        title=title,
        footer=footer,
        opened=opened,
        color=color,
        icon=icon,
        octicon=octicon,
        chevron=chevron,
        animate=animate,
        margin=margin,
        name=name,
        classes_container=classes_container,
        classes_title=classes_title,
        classes_body=classes_body,
        class_rich=class_rich,
        target_configs=target_configs,
        target_default=target_default,
    )


def field_list_item(
    title: ContainerContentInputType | MDContainer | None = None,
    description: ContainerContentInputType | MDContainer | None = None,
    indent: int = 3,
    content_separator_name: str = "",
    content_separator_body: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> FieldListItem:
    title = _to_container(
        (title, ),
        content_separator=content_separator_name,
        target_configs=target_configs,
        target_default=target_default
    )
    description = _to_container(
        (description, ),
        content_separator=content_separator_body,
        target_configs=target_configs,
        target_default=target_default
    )
    return FieldListItem(
        title=title,
        description=description,
        indent=indent,
        target_configs=target_configs,
        target_default=target_default,
    )


def field_list(
    *contents: ContainerContentInputType | MDContainer,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    content_separator: str = "\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> FieldList:
    content = _to_container(
        contents,
        content_separator=content_separator,
        target_configs=target_configs,
        target_default=target_default,
    )
    for item in content.values():
        if not isinstance(item.content, FieldListItem):
            raise ValueError("Field list must contain only field list items.")
    return FieldList(
        content=content,
        name=name,
        classes=classes,
        target_configs=target_configs,
        target_default=target_default,
    )


def frontmatter(
    content: dict | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> FrontMatter:
    return FrontMatter(
        content=content,
        target_configs=target_configs,
        target_default=target_default,
    )


def heading(
    *contents: ContainerContentInputType | MDContainer,
    level: Literal[1, 2, 3, 4, 5, 6] | Sequence[int] = 1,
    explicit_number: bool = False,
    name: Stringable | None = None,
    classes: list[Stringable] | None = None,
    attrs: dict | None = None,
    container: Stringable | None = "div",
    container_inline: Stringable | None = "span",
    attrs_container: dict | None = None,
    content_separator: str = "",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> Heading:
    content = _to_container(
        contents,
        content_separator=content_separator,
        target_configs=target_configs,
        target_default=target_default,
    )
    return Heading(
        content=content,
        level=level,
        explicit_number=explicit_number,
        name=name,
        classes=classes,
        attrs=attrs,
        container=container,
        container_inline=container_inline,
        attrs_container=attrs_container,
        target_configs=target_configs,
        target_default=target_default,
    )


def highlights(
    *items: dict,
    button: dict,
    attrs_p: dict | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
):
    title_buttons = buttons(
        *[highlight["title"] for highlight in items],
        **button,
    )
    contents = []
    for highlight, title_badge in zip(items, title_buttons.elements()):
        text = paragraph(
            highlight["description"],
            attrs=attrs_p,
        )
        item = _mdit.container(
            {"title": title_badge, "description": text},
            content_separator="",
            target_configs=target_configs,
            target_default=target_default,
        )
        contents.append(item)
    return _mdit.container(
        *contents,
        content_separator="\n\n",
        target_configs=target_configs,
        target_default=target_default,
    )


def html(
    *contents: ContainerContentInputType | MDContainer,
    tag: Stringable,
    attrs: dict | None = None,
    inline: bool = False,
    content_separator: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
):
    content = _to_container(
        contents,
        content_separator=content_separator,
        target_configs=target_configs,
        target_default=target_default,
    )
    return HTML(
        content=content,
        tag=tag,
        attrs=attrs,
        inline=inline,
        target_configs=target_configs,
        target_default=target_default,
    )


def inline_image(
    src: Stringable,
    src_dark: Stringable | None = None,
    title: Stringable | None = None,
    alt: Stringable | None = None,
    height: Stringable | None = None,
    width: Stringable | None = None,
    align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
    link: Stringable | None = None,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    attrs_img: dict | None = None,
    attrs_source_light: dict | None = None,
    attrs_source_dark: dict | None = None,
    attrs_picture: dict | None = None,
    attrs_a: dict | None = None,
    container: Stringable | None = "span",
    attrs_container: dict | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> InlineImage:
    return InlineImage(
        src=src,
        src_dark=src_dark,
        title=title,
        alt=alt,
        height=height,
        width=width,
        align=align,
        link=link,
        classes=classes,
        name=name,
        attrs_img=attrs_img,
        attrs_source_light=attrs_source_light,
        attrs_source_dark=attrs_source_dark,
        attrs_picture=attrs_picture,
        attrs_a=attrs_a,
        container=container,
        attrs_container=attrs_container,
        target_configs=target_configs,
        target_default=target_default,
    )


def menu(
    *items: dict | str,
    line_top: bool = True,
    line_bottom: bool = True,
    line_top_width: str | None = None,
    line_bottom_width: str | None = None,
    separator: int | str = 2,
    style: str | None = None,
    color: str | None = None,
    logo_color: str | None = None,
    logo_width: str | None = None,
    logo_size: str | None = None,
    logo: str | None = None,
    logo_type: str | None = None,
    logo_media_type: str | None = None,
    cache_seconds: int | None = None,
    color_dark: str | None = None,
    logo_color_dark: str | None = None,
    logo_dark: str | None = None,
    logo_type_dark: str | None = None,
    logo_media_type_dark: str | None = None,
    title: Stringable | None = None,
    alt: Stringable | None = None,
    height: Stringable | None = None,
    width: Stringable | None = None,
    align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
    link: Stringable | None = None,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    attrs_img: dict | None = None,
    attrs_source_light: dict | None = None,
    attrs_source_dark: dict | None = None,
    attrs_picture: dict | None = None,
    attrs_a: dict | None = None,
    attrs_hr_top: dict | None = None,
    attrs_hr_bottom: dict | None = None,
    container: Stringable | None = "div",
    attrs_container: dict | None = None,
    merge_params: bool = True,
    use_defaults: bool = True,
    container_conditions: str | list[str] | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
):
    inputs = locals()
    for param_name in (
        "items",
        "line_top_width",
        "line_bottom_width",
        "container",
        "attrs_container",
        "container_conditions",
        "attrs_hr_top",
        "attrs_hr_bottom",
        "line_top",
        "line_bottom",
    ):
        inputs.pop(param_name)
    content = {}
    if line_top:
        content["line_top"] = thematic_break(attrs={"width": line_top_width} | (attrs_hr_top or {}))
    content["buttons"] = buttons(*items, **inputs)
    if line_bottom:
        content["line_bottom"] = thematic_break(attrs={"width": line_bottom_width} | (attrs_hr_bottom or {}))
    return _mdit.container(
        content,
        content_separator="\n\n",
        html_container=container,
        html_container_attrs=attrs_container,
        html_container_conditions=container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )


def paragraph(
    *contents: ContainerContentInputType | MDContainer,
    name: Stringable | None = None,
    classes: list[Stringable] | None = None,
    attrs: dict | None = None,
    container: Stringable | None = "div",
    attrs_container: dict | None = None,
    content_separator: str = "\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> Paragraph:
    content = _to_container(
        contents,
        content_separator=content_separator,
        target_configs=target_configs,
        target_default=target_default,
    )
    return Paragraph(
        content=content,
        name=name,
        classes=classes,
        attrs=attrs,
        container=container,
        attrs_container=attrs_container,
        target_configs=target_configs,
        target_default=target_default,
    )


def rich(
    content: RenderableType,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> Rich:
    return Rich(
        content=content,
        target_configs=target_configs,
        target_default=target_default,
    )


def spacer(
    height: Stringable | None = None,
    width: Stringable | None = None,
    align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
    attrs_img: dict | None = None,
    container: Stringable | None = "span",
    attrs_container: dict | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
):
    return inline_image(
        src="docs/source/_static/img/spacer.svg",  #TODO: Add permanent link to spacer image
        height=height,
        width=width,
        align=align,
        attrs_img=attrs_img,
        container=container,
        attrs_container=attrs_container,
        target_configs=target_configs,
        target_default=target_default,
    )


def tab_item(
    *contents: ContainerContentInputType | MDContainer,
    title: ContainerContentInputType | MDContainer = None,
    selected: bool = False,
    sync: Stringable | None = None,
    name: Stringable | None = None,
    classes_container: str | list[str] | None = None,
    classes_label: str | list[str] | None = None,
    classes_content: str | list[str] | None = None,
    content_separator_title: str = " ",
    content_separator_content: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> TabItem:
    """Create a [Sphinx-Design tab item](https://sphinx-design.readthedocs.io/en/furo-theme/tabs.html).

    Parameters
    ----------
    title : Stringable
        Tab title.
    contents : ElementContentInputType
        Tab content.
    selected : bool, default: False
        Whether the tab item is selected by default.
    name : Stringable, optional
        A reference target name for the tab item
        (for [cross-referencing](https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html#syntax-referencing)).
    sync : Stringable, optional
        A key that is used to sync the selected tab across multiple tab-sets.
    classes_container : str | list[str], optional
        CSS class names to add to the container element. These must conform to the
        [identifier normalization rules](https://docutils.sourceforge.io/docs/ref/rst/directives.html#identifier-normalization).
    classes_label : str | list[str], optional
        CSS class names to add to the label element. These must conform to the
        [identifier normalization rules](https://docutils.sourceforge.io/docs/ref/rst/directives.html#identifier-normalization).
    classes_content : str | list[str], optional
        CSS class names to add to the content element. These must conform to the
        [identifier normalization rules](https://docutils.sourceforge.io/docs/ref/rst/directives.html#identifier-normalization).
    fence: {'`', '~', ':'}, default: '`'
        Fence character.
    """
    title = _to_container(
        (title, ),
        content_separator=content_separator_title,
        target_configs=target_configs,
        target_default=target_default,
    )
    contents = _to_container(
        contents,
        content_separator=content_separator_content,
        target_configs=target_configs,
        target_default=target_default,
    )
    return TabItem(
        title=title,
        content=contents,
        selected=selected,
        sync=sync,
        name=name,
        classes_container=classes_container,
        classes_label=classes_label,
        classes_content=classes_content,
        target_configs=target_configs,
        target_default=target_default,
)


def tab_set(
    *contents: ContainerContentInputType | MDContainer,
    sync_group: Stringable | None = None,
    classes: list[Stringable] | None = None,
    content_separator: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> TabSet:
    """Create a [Sphinx-Design tab set](https://sphinx-design.readthedocs.io/en/furo-theme/tabs.html).

    Parameters
    ----------
    contents : list[Directive]
        Tab items.
    class_ : list[str], optional
        CSS class names to add to the tab set. These must conform to the
        [identifier normalization rules](https://docutils.sourceforge.io/docs/ref/rst/directives.html#identifier-normalization).
    sync_group : Stringable, optional
        Group name for synchronized tab sets.
    fence: {'`', '~', ':'}, default: '`'
        Fence character.
    """
    contents = _to_container(
        contents,
        content_separator=content_separator,
        target_configs=target_configs,
        target_default=target_default,
    )
    for item in contents.values():
        if not isinstance(item.content, TabItem):
            raise ValueError("Tab set must contain only tab items.")
    return TabSet(
        content=contents,
        sync_group=sync_group,
        classes=classes,
        target_configs=target_configs,
        target_default=target_default,
    )


def table(
    *rows: tuple[
        list[ContainerContentInputType | MDContainer | tuple[ContainerContentInputType | MDContainer, HTMLAttrsType]],
        HTMLAttrsType
    ] | list[ContainerContentInputType | MDContainer | tuple[ContainerContentInputType | MDContainer, HTMLAttrsType]],
    caption: Stringable | None = None,
    align_table: Literal["left", "center", "right"] | None = None,
    align_columns: Literal["left", "center", "right"] | list[Literal["left", "center", "right"]] | None = None,
    num_rows_header: int = 0,
    num_rows_footer: int = 0,
    num_cols_stub: int = 0,
    width_table: Stringable | None = None,
    width_columns: list[int] | Literal["auto"] | None = None,
    name: Stringable | None = None,
    classes: list[Stringable] | None = None,
    attrs_figure: HTMLAttrsType = None,
    attrs_caption: HTMLAttrsType = None,
    attrs_table: HTMLAttrsType = None,
    attrs_body: HTMLAttrsType = None,
    attrs_head: HTMLAttrsType = None,
    attrs_foot: HTMLAttrsType = None,
    attrs_tr: HTMLAttrsType = None,
    attrs_th: HTMLAttrsType = None,
    attrs_td: HTMLAttrsType = None,
    attrs_body_tr: HTMLAttrsType = None,
    attrs_body_th: HTMLAttrsType = None,
    attrs_body_td: HTMLAttrsType = None,
    attrs_head_tr: HTMLAttrsType = None,
    attrs_head_th: HTMLAttrsType = None,
    attrs_head_td: HTMLAttrsType = None,
    attrs_foot_tr: HTMLAttrsType = None,
    attrs_foot_th: HTMLAttrsType = None,
    attrs_foot_td: HTMLAttrsType = None,
    content_separator: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
):
    rows_formatted = []
    for row in rows:
        row_formatted = []
        if isinstance(row, tuple):
            row_content, row_attrs = row
        else:
            row_content = row
            row_attrs = {}
        for cell in row_content:
            if isinstance(cell, tuple):
                cell_content, cell_attrs = cell
            else:
                cell_content = cell
                cell_attrs = {}
            cell_content = _to_container((cell_content, ), content_separator=content_separator)
            row_formatted.append((cell_content, cell_attrs))
        rows_formatted.append((row_formatted, row_attrs))
    return Table(
        rows=rows_formatted,
        caption=caption,
        align_table=align_table,
        align_columns=align_columns,
        num_rows_header=num_rows_header,
        num_rows_footer=num_rows_footer,
        num_cols_stub=num_cols_stub,
        width_table=width_table,
        width_columns=width_columns,
        name=name,
        classes=classes,
        attrs_figure=attrs_figure,
        attrs_caption=attrs_caption,
        attrs_table=attrs_table,
        attrs_body=attrs_body,
        attrs_head=attrs_head,
        attrs_foot=attrs_foot,
        attrs_tr=attrs_tr,
        attrs_th=attrs_th,
        attrs_td=attrs_td,
        attrs_body_tr=attrs_body_tr,
        attrs_body_th=attrs_body_th,
        attrs_body_td=attrs_body_td,
        attrs_head_tr=attrs_head_tr,
        attrs_head_th=attrs_head_th,
        attrs_head_td=attrs_head_td,
        attrs_foot_tr=attrs_foot_tr,
        attrs_foot_th=attrs_foot_th,
        attrs_foot_td=attrs_foot_td,
        target_configs=target_configs,
        target_default=target_default,
    )


def target_anchor(
    content: _MDITRenderable | Stringable,
    name: Stringable,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> TargetAnchor:
    return TargetAnchor(
        content=content,
        name=name,
        target_configs=target_configs,
        target_default=target_default,
    )


def thematic_break(
    name: Stringable | None = None,
    classes: list[Stringable] | None = None,
    attrs: dict | None = None,
    container: Stringable | None = "div",
    attrs_container: dict | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> ThematicBreak:
    """Create a [thematic break](https://github.github.com/gfm/#thematic-break).
    """
    return ThematicBreak(
        name=name,
        classes=classes,
        attrs=attrs,
        container=container,
        attrs_container=attrs_container,
        target_configs=target_configs,
        target_default=target_default,
    )


def toctree(
    *contents: ContainerContentInputType | MDContainer,
    glob: Stringable | None = None,
    caption: Stringable | None = None,
    hidden: bool = False,
    include_hidden: bool = False,
    max_depth: int | None = None,
    titles_only: bool = False,
    reversed: bool = False,
    name: Stringable | None = None,
    numbered: bool | int = False,
    content_separator: str = "\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> TocTree:
    contents = _to_container(
        contents,
        content_separator=content_separator,
        target_configs=target_configs,
        target_default=target_default,
    )
    return TocTree(
        content=contents,
        glob=glob,
        caption=caption,
        hidden=hidden,
        include_hidden=include_hidden,
        max_depth=max_depth,
        titles_only=titles_only,
        reversed=reversed,
        name=name,
        numbered=numbered,
        target_configs=target_configs,
        target_default=target_default,
    )

def toggle(
    *contents: ContainerContentInputType | MDContainer,
    title: ContainerContentInputType | MDContainer = None,
    opened: bool = False,
    attrs_details: dict | None = None,
    attrs_summary: dict | None = None,
    content_separator_title: str = "",
    content_separator_content: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> Toggle:
    title = _to_container(
        (title, ),
        content_separator=content_separator_title,
        target_configs=target_configs,
        target_default=target_default,
    )
    content = _to_container(
        contents,
        content_separator=content_separator_content,
        target_configs=target_configs,
        target_default=target_default,
    )
    return Toggle(
        title=title,
        content=content,
        opened=opened,
        attrs_details=attrs_details,
        attrs_summary=attrs_summary,
        target_configs=target_configs,
        target_default=target_default,
    )


def ordered_list(
    *contents: ContainerContentInputType | MDContainer,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    start: int | None = None,
    style: Literal["a", "A", "i", "I", "1"] = "1",
    attrs_ol: dict | None = None,
    attrs_li: dict | None = None,
    content_separator: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> OrderedList:
    content = _to_container(
        contents,
        content_separator=content_separator,
        target_configs=target_configs,
        target_default=target_default,
    )
    return OrderedList(
        content=content,
        classes=classes,
        name=name,
        start=start,
        style=style,
        attrs_ol=attrs_ol,
        attrs_li=attrs_li,
        target_configs=target_configs,
        target_default=target_default,
    )


def ordered_list_item(
    *contents: ContainerContentInputType | MDContainer,
    number: int,
    style: Literal["a", "A", "i", "I", "1"] = "1",
    attrs_li: dict | None = None,
    content_separator: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> OrderedListItem:
    content = _to_container(
        contents,
        content_separator=content_separator,
        target_configs=target_configs,
        target_default=target_default
    )
    return OrderedListItem(
        content=content,
        number=number,
        style=style,
        attrs_li=attrs_li,
        target_configs=target_configs,
        target_default=target_default,
    )


def unordered_list(
    *contents: ContainerContentInputType | MDContainer,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    style: Literal["circle", "disc", "square"] = "disc",
    attrs_ul: dict | None = None,
    attrs_li: dict | None = None,
    content_separator: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> UnOrderedList:
    content = _to_container(
        contents,
        content_separator=content_separator,
        target_configs=target_configs,
        target_default=target_default,
    )
    return UnOrderedList(
        content=content,
        classes=classes,
        name=name,
        style=style,
        attrs_ul=attrs_ul,
        attrs_li=attrs_li,
        target_configs=target_configs,
        target_default=target_default,
    )


def unordered_list_item(
    *contents: ContainerContentInputType | MDContainer,
    attrs_li: dict | None = None,
    content_separator: str = "\n\n",
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
):
    return UnOrderedListItem(
        content=_to_container(
            contents,
            content_separator=content_separator,
            target_configs=target_configs,
            target_default=target_default,
        ),
        attrs_li=attrs_li,
        target_configs=target_configs,
        target_default=target_default,
    )


def _make_badge_params(inputs: dict):
    params_light = {}
    params_dark = {}
    for param_name in (
        "label",
        "style",
        "color",
        "label_color",
        "logo_color",
        "logo_width",
        "logo_size",
        "logo",
        "logo_type",
        "logo_media_type",
        "cache_seconds",
    ):
        param_light = inputs.get(param_name)
        param_dark = inputs.get(f"{param_name}_dark")
        if param_light:
            params_light[param_name] = param_light
        if param_dark:
            params_dark[param_name] = param_dark
    return params_light, params_dark


def _make_badge_gradients(inputs: dict, count_items: int):
    gradient = {}
    for theme in ("light", "dark"):
        # Create gradient colors if given
        for color_type in ("color", "label_color", "logo_color"):
            color_key = color_type if theme == "light" else f"{color_type}_dark"
            color = inputs.get(color_key)
            if not color or not isinstance(color, dict):
                continue
            grad_def = inputs.pop(color_key)
            grad_gen = getattr(_pcit.gradient, grad_def.pop("gradient", "interpolate"))
            grad_def["count"] = count_items
            hex_colors = [color.css_hex() for color in grad_gen(**grad_def)]
            gradient[color_key] = hex_colors
    return gradient


def _to_container(
    contents: tuple[ContainerContentInputType, ...],
    content_separator: str,
    html_container: Stringable | None = None,
    html_container_attrs: dict | None = None,
    html_container_conditions: list[str] | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> MDContainer:
    if len(contents) == 1 and isinstance(contents[0], _mdit.MDContainer):
        return contents[0]
    return _mdit.container(
        *contents,
        content_separator=content_separator,
        html_container=html_container,
        html_container_attrs=html_container_attrs,
        html_container_conditions=html_container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )



# def continuous_integration(self, data):
#     def github(filename, **kwargs):
#         badge = self._github_badges.workflow_status(filename=filename, **kwargs)
#         return badge
#
#     def readthedocs(rtd_name, rtd_version=None, **kwargs):
#         badge = bdg.shields.build_read_the_docs(project=rtd_name, version=rtd_version, **kwargs)
#         return badge
#
#     def codecov(**kwargs):
#         badge = bdg.shields.coverage_codecov(
#             user=self.github["user"],
#             repo=self.github["repo"],
#             branch=self.github["branch"],
#             **kwargs,
#         )
#         return badge
#
#     func_map = {"github": github, "readthedocs": readthedocs, "codecov": codecov}
#
#     badges = []
#     for test in copy.deepcopy(data["args"]["tests"]):
#         func = test.pop("type")
#         if "style" in test:
#             style = test.pop("style")
#             test = style | test
#         badges.append(func_map[func](**test))
#
#     div = html.DIV(
#         align=data.get("align") or "center",
#         content=[
#             self._marker(start="Continuous Integration"),
#             self.heading(data=data["heading"]),
#             *badges,
#             self._marker(end="Continuous Integration"),
#         ],
#     )
#     return div
#
#
# def activity(self, data):
#     pr_button = bdg.shields.static(text="Pull Requests", style="for-the-badge", color="444")
#
#     prs = []
#     issues = []
#     for label in (None, "bug", "enhancement", "documentation"):
#         prs.append(self._github_badges.pr_issue(label=label, raw=True, logo=None))
#         issues.append(self._github_badges.pr_issue(label=label, raw=True, pr=False, logo=None))
#
#     prs_div = html.DIV(align="right", content=html.ElementCollection(prs, "\n<br>\n"))
#     iss_div = html.DIV(align="right", content=html.ElementCollection(issues, "\n<br>\n"))
#
#     table = html.TABLE(
#         content=[
#             html.TR(
#                 content=[
#                     html.TD(
#                         content=html.ElementCollection([pr_button, *prs], separator="<br>"),
#                         align="center",
#                         valign="top",
#                     ),
#                     html.TD(
#                         content=html.ElementCollection(
#                             [
#                                 bdg.shields.static(
#                                     text="Milestones",
#                                     style="for-the-badge",
#                                     color="444",
#                                 ),
#                                 self._github_badges.milestones(
#                                     state="both",
#                                     style="flat-square",
#                                     logo=None,
#                                     text="Total",
#                                 ),
#                                 "<br>",
#                                 bdg.shields.static(
#                                     text="Commits",
#                                     style="for-the-badge",
#                                     color="444",
#                                 ),
#                                 self._github_badges.last_commit(logo=None),
#                                 self._github_badges.commits_since(logo=None),
#                                 self._github_badges.commit_activity(),
#                             ],
#                             separator="<br>",
#                         ),
#                         align="center",
#                         valign="top",
#                     ),
#                     html.TD(
#                         content=html.ElementCollection(
#                             [
#                                 bdg.shields.static(
#                                     text="Issues",
#                                     style="for-the-badge",
#                                     logo="github",
#                                     color="444",
#                                 ),
#                                 *issues,
#                             ],
#                             separator="<br>",
#                         ),
#                         align="center",
#                         valign="top",
#                     ),
#                 ]
#             )
#         ]
#     )
#
#     div = html.DIV(
#         align=data.get("align") or "center",
#         content=[
#             self._marker(start="Activity"),
#             self.heading(data=data["heading"]),
#             table,
#             self._marker(end="Activity"),
#         ],
#     )
#     return div
#
#
# def pr_issue_badge(
#     self,
#     pr: bool = True,
#     status: Literal["open", "closed", "both"] = "both",
#     label: str | None = None,
#     raw: bool = False,
#     **kwargs,
# ) -> bdg.Badge:
#     """Number of pull requests or issues on GitHub.
#
#     Parameters
#     ----------
#     pr : bool, default: True
#         Whether to query pull requests (True, default) or issues (False).
#     closed : bool, default: False
#         Whether to query closed (True) or open (False, default) issues/pull requests.
#     label : str, optional
#         A specific GitHub label to query.
#     raw : bool, default: False
#         Display 'open'/'close' after the number (False) or only display the number (True).
#     """
#
#     def get_path_link(closed):
#         path = self._url / (
#             f"issues{'-pr' if pr else ''}{'-closed' if closed else ''}"
#             f"{'-raw' if raw else ''}/{self._address}{f'/{label}' if label else ''}"
#         )
#         link = self._repo_link.pr_issues(pr=pr, closed=closed, label=label)
#         return path, link
#
#     def half_badge(closed: bool):
#         path, link = get_path_link(closed=closed)
#         if "link" not in args:
#             args["link"] = link
#         badge = ShieldsBadge(path=path, **args)
#         badge.html_syntax = ""
#         if closed:
#             badge.color = {"right": "00802b"}
#             badge.text = ""
#             badge.logo = None
#         else:
#             badge.color = {"right": "AF1F10"}
#         return badge
#
#     desc = {
#         None: {True: "pull requests in total", False: "issues in total"},
#         "bug": {True: "pull requests related to a bug-fix", False: "bug-related issues"},
#         "enhancement": {
#             True: "pull requests related to new features and enhancements",
#             False: "feature and enhancement requests",
#         },
#         "documentation": {
#             True: "pull requests related to the documentation",
#             False: "issues related to the documentation",
#         },
#     }
#     text = {
#         None: {True: "Total", False: "Total"},
#         "bug": {True: "Bug Fix", False: "Bug Report"},
#         "enhancement": {True: "Enhancement", False: "Feature Request"},
#         "documentation": {True: "Docs", False: "Docs"},
#     }
#
#     args = self.args | kwargs
#     if "text" not in args:
#         args["text"] = text[label][pr]
#     if "title" not in args:
#         args["title"] = (
#             f"Number of {status if status != 'both' else 'open (red) and closed (green)'} "
#             f"{desc[label][pr]}. "
#             f"Click {'on the red and green tags' if status == 'both' else ''} to see the details of "
#             f"the respective {'pull requests' if pr else 'issues'} in the "
#             f"'{'Pull requests' if pr else 'Issues'}' section of the repository."
#         )
#     if "style" not in args and status == "both":
#         args["style"] = "flat-square"
#     if status not in ("open", "closed", "both"):
#         raise ValueError()
#     if status != "both":
#         path, link = get_path_link(closed=status == "closed")
#         if "link" not in args:
#             args["link"] = link
#         return ShieldsBadge(path=path, **args)
#     return html.element.ElementCollection(
#         [half_badge(closed) for closed in (False, True)], separator=""
#     )
#
#
