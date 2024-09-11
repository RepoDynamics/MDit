from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING
from types import FunctionType as _FunctionType
from contextlib import contextmanager as _contextmanager
import re as _re

import htmp as _htmp
import pyserials as _ps
import pybadger as _bdg
import pycolorit as _pcit
import ansi_sgr as _sgr

import mdit as _mdit
from mdit.protocol import MDCode as _MDCode, TargetConfig as _TargetConfig, \
    ANSITargetConfig as _ANSITargetConfig
from mdit import display as _display, target as _target

if _TYPE_CHECKING:
    from typing import Literal, Sequence
    from mdit import MDContainer, BlockMDContainer, InlineMDContainer
    from mdit.protocol import Stringable, ContainerInputType, TargetConfigType, ANSIInlineStyle, ANSIBlockStyle


class Element:

    _IS_MD_CODE = True
    _TARGET_CONFIG = {
        "sphinx": _target.sphinx(),
        "github": _target.github(),
        "pypi": _target.pypi(),
        "ansi": _target.ansi(),
    }

    def __init__(
        self,
        default_output_target: TargetConfigType = "sphinx",
    ):
        self.default_output_target = default_output_target

    def source(self, target: TargetConfigType | None = None, filters: str | list[str] | None = None) -> str:
        target = self._resolve_target(target)
        if isinstance(target, _ANSITargetConfig):
            return self._str_ansi(target=target, filters=filters)
        return self._str_md(target=target, filters=filters)

    def display(self, target: TargetConfigType | None = None, filters: str | list[str] | None = None) -> None:
        """Display the element in an IPython notebook."""
        target = self._resolve_target(target)
        output_str = self.source(target=target, filters=filters)
        if isinstance(target, _ANSITargetConfig):
            print(output_str)
        else:
            _display.ipython(output_str)
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

    @property
    def code_fence_count(self) -> int:
        return 0

    def __str__(self):
        return self.source()

    def _resolve_target(self, target: TargetConfigType | None = None) -> _TargetConfig:
        target = target or self.default_output_target
        if isinstance(target, (_TargetConfig, _ANSITargetConfig)):
            return target
        return self._TARGET_CONFIG[target]

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

    def _str_ansi(self, target: _ANSITargetConfig, filters: str | list[str] | None = None) -> str:
        raise NotImplementedError

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
        raise NotImplementedError

    def _format_inline_ansi(self, text: str, style: ANSIInlineStyle):
        text_full = f"{style.char_left}{text}{style.char_right}"



class Admonition(Element):

    MYST_TO_GH_TYPE = {
        "note": "note",
        "important": "importnant",
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
        title: Stringable,
        content: MDContainer,
        dropdown: bool = False,
        opened: bool = True,
        classes: list[Stringable] | None = None,
        add_type_class: bool = True,
        name: Stringable | None = None,
        type_github: Literal["note", "tip", "important", "warning", "caution"] | None = None,
        title_bold: bool = True,
        title_tight: bool = True,
        emoji: str | None = None,
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.type = type
        self.title = title
        self.content = content
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

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
        if target.directive_admo:
            return self._str_admo(target=target, filters=filters)
        if target.alerts:
            return self._str_alert(target=target, filters=filters)
        return self._str_blockquoute(target=target, filters=filters)

    def _str_ansi(self, target: _ANSITargetConfig, filters: str | list[str] | None = None) -> str:
        title = str(self.title)
        content = self.content.source(target=target, filters=filters)
        config = getattr(target, f"admonition_{self.type}")
        return _sgr.element.admonition(title=title, text=content, **config.dict)


    @property
    def code_fence_count(self) -> int:
        return max(self.content.code_fence_count, 2) + 1

    def _str_admo(self, target: TargetConfigType, filters: str | list[str] | None = None):
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
            content=self.content,
        ).source(target=target, filters=filters)

    def _str_alert(self, target: TargetConfigType, filters: str | list[str] | None = None):
        lines = [f"[!{self.type_github.upper()}]"]
        new_target = target.copy()
        new_target.alerts = False  # Alerts cannot contain other alerts
        content = self.content.source(target=new_target, filters=filters)
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

    def _str_blockquoute(self, target: TargetConfigType, filters: str | list[str] | None = None):
        lines = []
        content = self.content.source(target=target, filters=filters)
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


class Attribute(Element):

    def __init__(
        self,
        content: _MDCode | Stringable,
        block: bool,
        classes: list[Stringable] | Stringable | None = None,
        name: Stringable | None = None,
        attrs: dict | None = None,
        comment: Stringable | None = None,
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content
        self.block = block
        self.classes = classes
        self.name = name
        self.attrs = attrs or {}
        self.comment = comment
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(target=target, filters=filters) if isinstance(self.content, _MDCode) else str(self.content)
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
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

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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

    def _str_directive(self, target: TargetConfigType, filters: str | list[str] | None = None):
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content
        self.cite = cite
        self.name = name
        self.classes = classes or []
        self.attrs = attrs or {}
        self.attrs_cite = attrs_cite if attrs_cite is not None else {"align": "right", "style": {"text-align": "right"}}
        self.container = container
        self.attrs_container = attrs_container or {}
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:

        def make_md_blockquote(lines: list[str]) -> str:
            return "\n".join(f"> {line}" for line in lines)

        target = self._resolve_target(target)
        content = self.content.source(target=target, filters=filters)
        cite = self.cite.source(target=target, filters=filters) if self.cite else None
        cite_line = f"&mdash;{cite}"
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
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

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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
        content: MDContainer,
        language: Stringable | None = None,
        caption: Stringable | None = None,
        line_num: bool = False,
        line_num_start: int | None = None,
        emphasize_lines: list[int] | None = None,
        force: bool = False,
        name: Stringable | None = None,
        classes: Stringable | list[Stringable] | None = None,
        degrade_to_diff: bool = True,
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
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

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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
        content = self.content.source(target=target, filters=filters)
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

    def _str_ansi(self, target: _ANSITargetConfig, filters: str | list[str] | None = None) -> str:
        code = self.content.source(target=target, filters=filters)
        return _sgr.element.code_block(
            title=self.caption or "Code",
            code=code,
            line_num=self.line_num,
            line_num_start=self.line_num_start or 1,
            emphasize_lines=self.emphasize_lines,
            **target.code_block.dict
        )

    @property
    def code_fence_count(self):
        return max(self.content.code_fence_count, 2) + 1


class CodeSpan(Element):

    def __init__(
        self,
        content: Stringable,
        language: Stringable | None = None,
        attrs: dict | None = None,
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content
        self.language = language
        self.attrs = attrs or {}
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
        if not target.prefer_md:
            return _htmp.element.code(self.content, self.attrs).source(indent=-1)
        return f"`{self.content}`"

    def _str_ansi(self, target: _ANSITargetConfig, filters: str | list[str] | None = None) -> str:
        return _sgr.element.inline(text=self.content, **target.code_span.dict)


class Directive(Element):

    def __init__(
        self,
        name: Stringable,
        args: MDContainer | None = None,
        options: dict[Stringable, Stringable | list[Stringable] | None] | None = None,
        content: MDContainer | None = None,
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.name = name
        self.args = args
        self.options = options or {}
        self.content = content
        return

    @property
    def code_fence_count(self) -> int:
        return max(self.content.code_fence_count, 2) + 1

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:

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


class FieldListItem(Element):
    def __init__(
        self,
        title: MDContainer,
        description: MDContainer | None = None,
        indent: int = 3,
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.title = title
        self.description = description
        self.indent = indent
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
        title = self.title.source(target=target, filters=filters)
        description = self.description.source(target=target, filters=filters) if self.description else ""
        indent = " " * (self.indent if target.field_list else 2)  # 2 for normal list
        description_indented = "\n".join(f"{indent}{line}" for line in description.splitlines()).strip()
        if target.field_list:
            return f":{title}: {description}".strip()
        return f"- **{title}**{f": {description_indented}" if description_indented else ''}"

    def _str_ansi(self, target: _ANSITargetConfig, filters: str | list[str] | None = None) -> str:
        title = self.title.source(target=target, filters=filters)
        description = self.description.source(target=target, filters=filters) if self.description else ""
        title_sgr = _sgr.element.inline(text=title, **target.field_list_title.dict)
        if not description:
            return title_sgr
        description_sgr = _sgr.element.block(text=description, **target.field_list_description.dict)
        indent = len(_sgr.remove_sequence(title_sgr)) + 2
        description_indented = "\n".join(f"{' ' * indent}{line}" for line in description_sgr.splitlines()).strip()
        return f"{title_sgr}: {description_indented}"




class FieldList(Element):

    def __init__(
        self,
        content: MDContainer,
        name: Stringable | None = None,
        classes: list[Stringable] | None = None,
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content
        self.name = name
        self.classes = classes or []
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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

    def _str_ansi(self, target: _ANSITargetConfig, filters: str | list[str] | None = None) -> str:
        return self.content.source(target=target, filters=filters)

    def append(
        self,
        name: ContainerInputType | MDContainer | None = None,
        body: ContainerInputType | MDContainer | None = None,
        conditions: str | list[str] | None = None,
        key: str | int | None = None,
        indent: int = 4,
        content_seperator_name: str = "",
        content_seperator_body: str = "\n\n",
    ):
        list_item = field_list_item(
            title=name,
            description=body,
            indent=indent,
            content_seperator_name=content_seperator_name,
            content_seperator_body=content_seperator_body,
        )
        self.content.append(list_item, conditions=conditions, key=key)
        return


class FrontMatter(Element):

    def __init__(
        self,
        content: dict | None = None,
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content or {}
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.level = list(level) if isinstance(level, Sequence) else [1] * level
        self.content = content
        self.name = name
        self.classes = classes or []
        self.attrs = attrs or {}
        self.container = container
        self.container_inline = container_inline
        self.attrs_container = attrs_container or {}
        self.explicit_number = explicit_number
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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

    def _str_ansi(self, target: _ANSITargetConfig, filters: str | list[str] | None = None) -> str:
        content = self._make_content(self.content.source(target=target, filters=filters))
        style = target.heading[min(len(self.level), len(target.heading)) - 1]
        return _sgr.element.block(text=content, **style.dict)

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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content
        self.tag = tag
        self.attrs = attrs or {}
        self.inline = inline
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
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

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content
        self.name = name
        self.classes = classes or []
        self.attrs = attrs or {}
        self.container = container
        self.attrs_container = attrs_container or {}
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.title = title
        self.content = content
        self.selected = selected
        self.sync = sync
        self.name = name
        self.classes_container = classes_container
        self.classes_label = classes_label
        self.classes_content = classes_content
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content
        self.sync_group = sync_group
        self.classes = classes or []
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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
        title: ContainerInputType | MDContainer | None = None,
        content: ContainerInputType | MDContainer | None = None,
        conditions: str | list[str] | None = None,
        key: str | int | None = None,
        selected: bool = False,
        sync: Stringable | None = None,
        name: Stringable | None = None,
        class_container: str | list[str] | None = None,
        class_label: str | list[str] | None = None,
        class_content: str | list[str] | None = None,
        fence: Literal["`", "~", ":"] = ":",
        content_seperator_title: str = "",
        content_seperator_content: str = "\n\n",
    ):
        tab = tab_item(
            title=title,
            content=content,
            selected=selected,
            sync=sync,
            name=name,
            classes_container=class_container,
            classes_label=class_label,
            classes_content=class_content,
            fence=fence,
            content_seperator_title=content_seperator_title,
            content_seperator_content=content_seperator_content,
        )
        self.content.append(tab, conditions=conditions, key=key)
        return


class TargetAnchor(Element):

    def __init__(
        self,
        content: _MDCode | Stringable,
        name: Stringable,
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content
        self.name = name
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
        content = self.content.source(target=target, filters=filters) if isinstance(self.content, _MDCode) else str(self.content)
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.name = name
        self.classes = classes or []
        self.attrs = attrs or {}
        self.container = container
        self.attrs_container = attrs_container or {}
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
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

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content
        self.title = title
        self.attrs_details = attrs_details or {}
        self.attrs_summary = attrs_summary or {}
        self.opened = opened
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
        if target.directive_toggle:
            return directive(
                name="toggle",
                options={"show": self.opened},
                content=self.content,
            ).source(target=target, filters=filters)
        content= _htmp.elementor.markdown(self.content.source(target=target, filters=filters))
        summary = _htmp.element.summary(self.title, self.attrs_summary)
        return _htmp.element.details([summary, content], self.attrs_details).source(indent=-1)


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
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)

        self.content = content
        self.start = start
        self.style = style
        self.classes = classes or []
        self.name = name
        self.attrs_ol = attrs_ol or {}
        self.attrs_li = attrs_li or {}
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
        items = self.content.elements(target=target, filters=filters, string=True)
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


class UnOrderedList(Element):

    def __init__(
        self,
        content: MDContainer,
        classes: list[Stringable] | None = None,
        name: Stringable | None = None,
        style: Literal["circle", "disc", "square"] = "disc",
        attrs_ul: dict | None = None,
        attrs_li: dict | None = None,
        default_output_target: TargetConfigType = "sphinx",
    ):
        super().__init__(default_output_target=default_output_target)
        self.content = content
        self.style = style
        self.classes = classes or []
        self.name = name
        self.attrs_ul = attrs_ul or {}
        self.attrs_li = attrs_li or {}
        return

    def _str_md(self, target: _TargetConfig, filters: str | list[str] | None = None) -> str:
        items = self.content.elements(target=target, filters=filters, string=True)
        if not target.prefer_md:
            attrs_ul = {
                "class": self.classes,
                "id": self.name,
                "style": {"list-style-type": self.style}
            } | self.attrs_ul
            return _htmp.elementor.unordered_list(
                items=[_htmp.elementor.markdown(item) for item in items],
                type=self.style,
                attrs_li=self.attrs_li,
                attrs_ul=attrs_ul,
            ).source(indent=-1)

        list_items = []
        for item in items:
            item_lines = item.splitlines()
            item_lines = [f"- {item_lines[0]}"] + [
                f"  {line}" for line in item_lines[1:]
            ]
            list_items.extend(item_lines)
        list_str = "\n".join(list_items)

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
    title: ContainerInputType | MDContainer | None = None,
    content: ContainerInputType | MDContainer | None = None,
    dropdown: bool = False,
    opened: bool = False,
    classes: list[Stringable] | None = None,
    add_type_class: bool = True,
    name: Stringable | None = None,
    type_github: Literal["note", "tip", "important", "warning", "caution"] | None = None,
    title_bold: bool = True,
    title_tight: bool = True,
    emoji: str | None = None,
    content_seperator_title: str = "",
    content_seperator_content: str = "\n\n",
    default_output_target: TargetConfigType = "sphinx",
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
    title = _mdit.container(title, content_seperator=content_seperator_title)
    content = _mdit.container(content, content_seperator=content_seperator_content)
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
        default_output_target=default_output_target,
    )


def attribute(
    content: _MDCode | Stringable,
    block: bool,
    classes: Stringable | list[Stringable] | None = None,
    name: Stringable | None = None,
    attrs: dict | None = None,
    comment: Stringable | None = None,
    default_output_target: TargetConfigType = "sphinx",
):
    return Attribute(
        content=content,
        block=block,
        classes=classes,
        name=name,
        attrs=attrs,
        comment=comment,
        default_output_target=default_output_target,
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
    default_output_target: TargetConfigType = "sphinx",
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
        default_output_target=default_output_target,
    )
    return image


def badges(
    items: list[dict | str],
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
    default_output_target: TargetConfigType = "sphinx",
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
    spacer = "&nbsp;" * separator if isinstance(separator, int) else str(separator)
    return _mdit.container(
        content=badge_list,
        content_seperator=spacer,
        html_container=container,
        html_container_attrs=attrs_container,
        html_container_conditions=container_conditions,
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
    caption: ContainerInputType | MDContainer | None = None,
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
    default_output_target: TargetConfigType = "sphinx",
) -> BlockImage:
    caption = _mdit.container(caption, content_seperator="\n")
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
        default_output_target=default_output_target,
    )


def block_quote(
    content: ContainerInputType | MDContainer | None = None,
    cite: ContainerInputType | MDContainer | None = None,
    name: Stringable | None = None,
    classes: list[Stringable] | None = None,
    attrs: dict | None = None,
    attrs_cite: dict | None = None,
    container: Stringable | None = "div",
    attrs_container: dict | None = None,
    content_seperator: str = "\n",
    content_separator_cite: str = ", ",
    default_output_target: TargetConfigType = "sphinx",
) -> BlockQuote:
    content = _mdit.container(content, content_seperator=content_seperator)
    cite = _mdit.container(cite, content_seperator=content_separator_cite)
    return BlockQuote(
        content=content,
        cite=cite,
        name=name,
        classes=classes,
        attrs=attrs,
        attrs_cite=attrs_cite,
        container=container,
        attrs_container=attrs_container,
        default_output_target=default_output_target,
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
    default_output_target: TargetConfigType = "sphinx",
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
        default_output_target=default_output_target,
    )


def buttons(
    items: list[dict | str],
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
    default_output_target: TargetConfigType = "sphinx",
    container_conditions: str | list[str] | None = None,
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
    spacer = "&nbsp;" * separator if isinstance(separator, int) else str(separator)
    return _mdit.container(
        content=badge_list,
        content_seperator=spacer,
        html_container=container,
        html_container_attrs=attrs_container,
        html_container_conditions=container_conditions,
    )


def card(
    header: ContainerInputType | MDContainer | None = None,
    title: Stringable | None = None,
    body: ContainerInputType | MDContainer | None = None,
    footer: ContainerInputType | MDContainer | None = None,
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
    default_output_target: TargetConfigType = "sphinx",
    content_separator_header: str = "\n\n",
    content_separator_body: str = "\n\n",
    content_separator_footer: str = "\n\n",
) -> Card:
    header = _mdit.container(header, content_seperator=content_separator_header)
    body = _mdit.container(body, content_seperator=content_separator_body)
    footer = _mdit.container(footer, content_seperator=content_separator_footer)
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
        default_output_target=default_output_target,
    )


def code_block(
    content: ContainerInputType | MDContainer | None = None,
    language: Stringable | None = None,
    caption: Stringable | None = None,
    line_num: bool = False,
    line_num_start: int | None = None,
    emphasize_lines: list[int] | None = None,
    force: bool = False,
    name: Stringable | None = None,
    classes: Stringable | list[Stringable] | None = None,
    degrade_to_diff: bool = True,
    content_seperator: str = "\n",
    default_output_target: TargetConfigType = "sphinx",
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
    content = _mdit.container(content, content_seperator=content_seperator)
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
        default_output_target=default_output_target,
    )


def code_span(
    content: Stringable,
    language: Stringable | None = None,
    attrs: dict | None = None,
    default_output_target: TargetConfigType = "sphinx",
) -> CodeSpan:
    return CodeSpan(
        content=content, language=language, attrs=attrs, default_output_target=default_output_target
    )



def directive(
    name: Stringable,
    args: ContainerInputType | MDContainer | None = None,
    options: dict[Stringable, Stringable | list[Stringable] | None] | None = None,
    content: ContainerInputType | MDContainer | None = None,
    content_seperator_args: str = " ",
    content_seperator_content: str = "\n\n",
    default_output_target: TargetConfigType = "sphinx",
) -> Directive:
    args = _mdit.container(args, content_seperator=content_seperator_args)
    content = _mdit.container(content, content_seperator=content_seperator_content)
    return Directive(
        name=name, args=args, options=options, content=content, default_output_target=default_output_target)


def field_list_item(
    title: ContainerInputType | MDContainer | None = None,
    description: ContainerInputType | MDContainer | None = None,
    indent: int = 3,
    content_seperator_name: str = "",
    content_seperator_body: str = "\n\n",
    default_output_target: TargetConfigType = "sphinx",
) -> FieldListItem:
    title = _mdit.container(title, content_seperator=content_seperator_name)
    description = _mdit.container(description, content_seperator=content_seperator_body)
    return FieldListItem(title=title, description=description, indent=indent, default_output_target=default_output_target)


def field_list(
    content: ContainerInputType | MDContainer | None = None,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    content_seperator: str = "\n",
    default_output_target: TargetConfigType = "sphinx",
) -> FieldList:
    content = _mdit.container(content, content_seperator=content_seperator)
    for item in content.values():
        if not isinstance(item.content, FieldListItem):
            raise ValueError("Field list must contain only field list items.")
    return FieldList(content=content, name=name, classes=classes, default_output_target=default_output_target)


def frontmatter(
    content: dict | None = None,
    default_output_target: TargetConfigType = "sphinx",
) -> FrontMatter:
    return FrontMatter(content=content, default_output_target=default_output_target)


def heading(
    content: ContainerInputType | MDContainer | None = None,
    level: Literal[1, 2, 3, 4, 5, 6] | Sequence[int] = 1,
    explicit_number: bool = False,
    name: Stringable | None = None,
    classes: list[Stringable] | None = None,
    attrs: dict | None = None,
    container: Stringable | None = "div",
    container_inline: Stringable | None = "span",
    attrs_container: dict | None = None,
    content_seperator: str = "",
    default_output_target: TargetConfigType = "sphinx",
) -> Heading:
    content = _mdit.container(content, content_seperator=content_seperator)
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
        default_output_target=default_output_target,
    )


def highlights(
    items: list[dict],
    button: dict,
    attrs_p: dict | None = None,
):
    title_buttons = buttons(
        items=[highlight["title"] for highlight in items],
        **button,
    )
    contents = []
    for highlight, title_badge in zip(items, title_buttons.elements()):
        text = paragraph(
            content=highlight["description"],
            attrs=attrs_p,
        )
        item = _mdit.container(
            content={"title": title_badge, "description": text},
            content_seperator="",
        )
        contents.append(item)
    return _mdit.container(
        content=contents,
        content_seperator="\n\n",
    )


def html(
    content: ContainerInputType | MDContainer,
    tag: Stringable,
    attrs: dict | None = None,
    inline: bool = False,
    content_seperator: str = "\n\n",
    default_output_target: TargetConfigType = "sphinx",
):
    content = _mdit.container(content=content, content_seperator=content_seperator)
    return HTML(
        content=content,
        tag=tag,
        attrs=attrs,
        inline=inline,
        default_output_target=default_output_target,
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
    default_output_target: TargetConfigType = "sphinx",
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
        default_output_target=default_output_target,
    )


def menu(
    items: list[dict | str],
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
    default_output_target: TargetConfigType = "sphinx",
    container_conditions: str | list[str] | None = None,
):
    inputs = locals()
    for param_name in (
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
    content["buttons"] = buttons(**inputs)
    if line_bottom:
        content["line_bottom"] = thematic_break(attrs={"width": line_bottom_width} | (attrs_hr_bottom or {}))
    return _mdit.container(
        content=content,
        content_seperator="\n\n",
        html_container=container,
        html_container_attrs=attrs_container,
        html_container_conditions=container_conditions,
    )


def paragraph(
    content: ContainerInputType | MDContainer | None = None,
    name: Stringable | None = None,
    classes: list[Stringable] | None = None,
    attrs: dict | None = None,
    container: Stringable | None = "div",
    attrs_container: dict | None = None,
    content_seperator: str = "\n",
    default_output_target: TargetConfigType = "sphinx",
) -> Paragraph:
    content = _mdit.container(content, content_seperator=content_seperator)
    return Paragraph(
        content=content,
        name=name,
        classes=classes,
        attrs=attrs,
        container=container,
        attrs_container=attrs_container,
        default_output_target=default_output_target,
    )



def spacer(
    height: Stringable | None = None,
    width: Stringable | None = None,
    align: Literal["left", "center", "right", "top", "middle", "bottom"] | None = None,
    attrs_img: dict | None = None,
    container: Stringable | None = "span",
    attrs_container: dict | None = None,
    default_output_target: TargetConfigType = "github",
):
    return inline_image(
        src="docs/source/_static/img/spacer.svg",  #TODO: Add permanent link to spacer image
        height=height,
        width=width,
        align=align,
        attrs_img=attrs_img,
        container=container,
        attrs_container=attrs_container,
        default_output_target=default_output_target,
    )


def tab_item(
    title: ContainerInputType | MDContainer | None = None,
    content: ContainerInputType | MDContainer | None = None,
    selected: bool = False,
    sync: Stringable | None = None,
    name: Stringable | None = None,
    classes_container: str | list[str] | None = None,
    classes_label: str | list[str] | None = None,
    classes_content: str | list[str] | None = None,
    content_seperator_title: str = " ",
    content_seperator_content: str = "\n\n",
    default_output_target: TargetConfigType = "sphinx",
) -> TabItem:
    """Create a [Sphinx-Design tab item](https://sphinx-design.readthedocs.io/en/furo-theme/tabs.html).

    Parameters
    ----------
    title : Stringable
        Tab title.
    content : ElementContentInputType
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
    title = _mdit.container(title, content_seperator=content_seperator_title)
    content = _mdit.container(content, content_seperator=content_seperator_content)
    return TabItem(
        title=title,
        content=content,
        selected=selected,
        sync=sync,
        name=name,
        classes_container=classes_container,
        classes_label=classes_label,
        classes_content=classes_content,
        default_output_target=default_output_target,
)


def tab_set(
    content: ContainerInputType | MDContainer | None = None,
    sync_group: Stringable | None = None,
    classes: list[Stringable] | None = None,
    content_seperator: str = "\n\n",
    default_output_target: TargetConfigType = "sphinx",
) -> TabSet:
    """Create a [Sphinx-Design tab set](https://sphinx-design.readthedocs.io/en/furo-theme/tabs.html).

    Parameters
    ----------
    content : list[Directive]
        Tab items.
    class_ : list[str], optional
        CSS class names to add to the tab set. These must conform to the
        [identifier normalization rules](https://docutils.sourceforge.io/docs/ref/rst/directives.html#identifier-normalization).
    sync_group : Stringable, optional
        Group name for synchronized tab sets.
    fence: {'`', '~', ':'}, default: '`'
        Fence character.
    """
    content = _mdit.container(content, content_seperator=content_seperator)
    for item in content.values():
        if not isinstance(item.content, TabItem):
            raise ValueError("Tab set must contain only tab items.")
    return TabSet(content=content, sync_group=sync_group, classes=classes, default_output_target=default_output_target)


def target_anchor(
    content: _MDCode | Stringable,
    name: Stringable,
    default_output_target: TargetConfigType = "sphinx",
) -> TargetAnchor:
    return TargetAnchor(content=content, name=name, default_output_target=default_output_target)


def thematic_break(
    name: Stringable | None = None,
    classes: list[Stringable] | None = None,
    attrs: dict | None = None,
    container: Stringable | None = "div",
    attrs_container: dict | None = None,
    default_output_target: TargetConfigType = "sphinx",
) -> ThematicBreak:
    """Create a [thematic break](https://github.github.com/gfm/#thematic-break).
    """
    return ThematicBreak(
        name=name,
        classes=classes,
        attrs=attrs,
        container=container,
        attrs_container=attrs_container,
        default_output_target=default_output_target,
    )


def toctree(
    content: ContainerInputType | MDContainer | None = None,
    glob: Stringable | None = None,
    caption: Stringable | None = None,
    hidden: bool = False,
    include_hidden: bool = False,
    max_depth: int | None = None,
    titles_only: bool = False,
    reversed: bool = False,
    name: Stringable | None = None,
    numbered: bool | int = False,
    content_seperator: str = "\n",
    default_output_target: TargetConfigType = "sphinx",
) -> TocTree:
    content = _mdit.container(content, content_seperator=content_seperator)
    return TocTree(
        content=content,
        glob=glob,
        caption=caption,
        hidden=hidden,
        include_hidden=include_hidden,
        max_depth=max_depth,
        titles_only=titles_only,
        reversed=reversed,
        name=name,
        numbered=numbered,
        default_output_target=default_output_target,
    )

def toggle(
    title: ContainerInputType | MDContainer | None = None,
    content: ContainerInputType | MDContainer | None = None,
    opened: bool = False,
    attrs_details: dict | None = None,
    attrs_summary: dict | None = None,
    content_seperator_title: str = "",
    content_seperator_content: str = "\n\n",
    default_output_target: TargetConfigType = "sphinx",
) -> Toggle:
    title = _mdit.container(title, content_seperator=content_seperator_title)
    content = _mdit.container(content, content_seperator=content_seperator_content)
    return Toggle(
        title=title,
        content=content,
        opened=opened,
        attrs_details=attrs_details,
        attrs_summary=attrs_summary,
        default_output_target=default_output_target,
    )


def ordered_list(
    content: ContainerInputType | MDContainer | None = None,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    start: int | None = None,
    style: Literal["a", "A", "i", "I", "1"] = "1",
    attrs_ol: dict | None = None,
    attrs_li: dict | None = None,
    content_seperator: str = "\n\n",
    default_output_target: TargetConfigType = "sphinx",
) -> OrderedList:
    content = _mdit.container(content, content_seperator=content_seperator)
    return OrderedList(
        content=content,
        classes=classes,
        name=name,
        start=start,
        style=style,
        attrs_ol=attrs_ol,
        attrs_li=attrs_li,
        default_output_target=default_output_target,
    )


def unordered_list(
    content: ContainerInputType | MDContainer | None = None,
    classes: list[Stringable] | None = None,
    name: Stringable | None = None,
    style: Literal["circle", "disc", "square"] = "disc",
    attrs_ul: dict | None = None,
    attrs_li: dict | None = None,
    content_seperator: str = "\n\n",
    default_output_target: TargetConfigType = "sphinx",
) -> UnOrderedList:
    content = _mdit.container(content, content_seperator=content_seperator)
    return UnOrderedList(
        content=content,
        classes=classes,
        name=name,
        style=style,
        attrs_ul=attrs_ul,
        attrs_li=attrs_li,
        default_output_target=default_output_target,
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
#                         content=html.ElementCollection([pr_button, *prs], seperator="<br>"),
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
#                             seperator="<br>",
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
#                             seperator="<br>",
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
#         [half_badge(closed) for closed in (False, True)], seperator=""
#     )
#
#
