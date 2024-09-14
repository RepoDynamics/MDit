from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING
from dataclasses import dataclass as _dataclass, asdict as _asdict

import pydantic as _pydantic
from rich import (
    box as _box,
    style as _style,
    color as _color,
    highlighter as _highlighter,
    rule as _rule,
    console as _console,
    panel as _panel,
    table as _table,
    text as _text,
    syntax as _syntax,
)
import pycolorit as _pcit

if _TYPE_CHECKING:
    from typing import Literal, IO, Callable, Sequence, Iterable
    from datetime import datetime
    from rich.box import Box
    from rich.style import Style, StyleType
    from rich.align import AlignMethod
    from rich.padding import PaddingDimensions
    from rich.color import Color
    from rich.theme import Theme
    from rich.emoji import EmojiVariant
    from rich._log_render import FormatTimeCallable
    from rich.console import HighlighterType, Console, RenderableType, JustifyMethod, OverflowMethod, Group
    from rich.rule import Rule
    from rich.table import Column, Table, VerticalAlignMethod
    from rich.text import Text
    from rich.panel import Panel
    from rich.syntax import Syntax
    from pygments.lexer import Lexer

BoxName = Literal[
    "ascii",
    "ascii2",
    "ascii_double_head",
    "square",
    "square_double_head",
    "minimal",
    "minimal_heavy_head",
    "minimal_double_head",
    "simple",
    "simple_head",
    "simple_heavy",
    "horizontals",
    "rounded",
    "heavy",
    "heavy_edge",
    "heavy_head",
    "double",
    "double_edge",
    "markdown",
]


class StyleConfig(_pydantic.BaseModel):
    """Rich terminal style configurations.

    References
    ----------
    - [Rich API Reference](https://rich.readthedocs.io/en/stable/reference/style.html)
    - [Rich Styles Documentation](https://rich.readthedocs.io/en/stable/style.html)
    """
    color: tuple[int, int, int] | str | Color | None = None
    bgcolor: tuple[int, int, int] | str | Color | None = None
    bold: bool | None = None
    italic: bool | None = None
    dim: bool | None = None
    underline: bool | None = None
    underline2: bool | None = None
    strike: bool | None = None
    overline: bool | None = None
    blink: bool | None = None
    blink2: bool | None = None
    reverse: bool | None = None
    conceal: bool | None = None
    frame: bool | None = None
    encircle: bool | None = None

    def make(self, link: str | None = None, **overrides) -> Style:
        kwargs = self.model_dump() | {"link": link} | overrides
        for key in ("color", "bgcolor"):
            if isinstance(kwargs[key], tuple):
                kwargs[key] = _color.Color.from_rgb(*kwargs[key])
            elif isinstance(kwargs[key], str):
                kwargs[key] = _color.Color.from_rgb(*_pcit.color.css(kwargs[key]).rgb(ubyte=True)[:3])
        return _style.Style(**kwargs)

    @_pydantic.field_validator('color', 'bgcolor')
    @classmethod
    def _validate_colors(cls, color: tuple[int, int, int] | str | Color | None) -> Color | None:
        if isinstance(color, tuple):
            assert all(0 <= c <= 255 for c in color), "Color values must be between 0 and 255."
        if isinstance(color, str):
            try:
                _pcit.color.css(color)
            except _pcit.exception.PyColorITException:
                raise ValueError(f"Invalid CSS color: {color}")
        return color


class ConsoleConfig(_pydantic.BaseModel):
    color_system: Literal["standard", "256", "truecolor", "auto"] = "auto"
    force_terminal: bool | None = None
    force_jupyter: bool | None = None
    force_interactive: bool | None = None
    soft_wrap: bool = False
    theme: Theme | None = None
    stderr: bool = False
    file: IO[str] | None = None
    quiet: bool = False
    width: int | None = None
    height: int | None = None
    style: StyleConfig | StyleType = None
    no_color: bool | None = None
    tab_size: int = 8
    record: bool = False
    markup: bool = True
    emoji: bool = True
    emoji_variant: EmojiVariant | None = "emoji"
    highlight: bool = True
    log_time: bool = True
    log_path: bool = True
    log_time_format: str | FormatTimeCallable | None = "[%X]"
    highlighter: HighlighterType | None = _highlighter.ReprHighlighter()
    legacy_windows: bool | None = None
    safe_box: bool = True
    get_datetime: Callable[[], datetime] | None = None
    get_time: Callable[[], float] = None

    def make(self, **overrides) -> Console:
        kwargs = self.model_dump() | overrides
        if isinstance(kwargs["style"], StyleConfig):
            kwargs["style"] = kwargs["style"].make()
        return _console.Console(**kwargs)


class TextConfig(_pydantic.BaseModel):
    """Rich Text configurations.

    References
    ----------
    - [Rich Text API Reference](https://rich.readthedocs.io/en/stable/reference/text.html#rich.text.Text)
    """
    prefix: str = ""
    suffix: str = ""
    style: StyleConfig | StyleType = "none"
    justify: AlignMethod = "left"
    overflow: Literal["crop", "fold", "ellipsis"] | None = None
    no_wrap: bool | None = None
    end: str = "\n"
    tab_size: int | None = None

    def make(self, text: str | Text, **overrides) -> Text:
        kwargs = self.model_dump(exclude={"prefix", "suffix"}) | overrides
        if isinstance(kwargs["style"], StyleConfig):
            kwargs["style"] = kwargs["style"].make()
        if isinstance(text, str):
            return _text.Text(f"{self.prefix}{text}{self.suffix}", style=kwargs["style"])
        return _text.Text.assemble(self.prefix, text, self.suffix, style=kwargs["style"])


class SyntaxConfig(_pydantic.BaseModel):
    theme: str = "monokai"
    dedent: bool = False
    tab_size: int = 4
    word_wrap: bool = False
    background_color: str | None = None
    indent_guides: bool = False
    padding: PaddingDimensions = 1

    def make(
        self,
        code: str,
        lexer: str | Lexer,
        line_numbers: bool = False,
        start_line: int = 1,
        line_range: tuple[int | None, int | None] | None = None,
        highlight_lines: Sequence[int] | None = None,
        code_width: int | None = None,
    ) -> Syntax:
        return _syntax.Syntax(
            code,
            lexer=lexer,
            theme=self.theme,
            dedent=self.dedent,
            line_numbers=line_numbers,
            start_line=start_line,
            line_range=line_range,
            highlight_lines=highlight_lines,
            code_width=code_width,
            tab_size=self.tab_size,
            word_wrap=self.word_wrap,
            background_color=self.background_color,
            indent_guides=self.indent_guides,
            padding=self.padding,
        )


class RuleConfig(_pydantic.BaseModel):
    """Rich Rule configurations.

    References
    ----------
    - [Rich Rule API Reference](https://rich.readthedocs.io/en/stable/reference/rule.html)
    """
    characters: str = "─"
    style: StyleConfig | StyleType = "rule.line"
    align: AlignMethod = "center"
    end: str = "\n"

    def make(self, title: str | Text = "", **overrides) -> Rule:
        kwargs = self.model_dump() | {"title": title} | overrides
        if isinstance(kwargs["style"], StyleConfig):
            kwargs["style"] = kwargs["style"].make()
        return _rule.Rule(**kwargs)


class PanelConfig(_pydantic.BaseModel):
    """Rich Panel configurations.

    References
    ----------
    - [Rich Panel API Reference](https://rich.readthedocs.io/en/stable/reference/panel.html)
    - [Rich Boxes Docs](https://rich.readthedocs.io/en/stable/appendix/box.html)
    - [Rich Boxes Code](https://github.com/Textualize/rich/blob/fd981823644ccf50d685ac9c0cfe8e1e56c9dd35/rich/box.py)
    """
    box: BoxName | Box = "rounded"
    style: StyleConfig | StyleType = "none"
    border_style: StyleConfig | StyleType = "none"
    title_style: StyleConfig | TextConfig | StyleType = "none"
    subtitle_style: StyleConfig | TextConfig | StyleType = "none"
    title_align: AlignMethod = "left"
    subtitle_align: AlignMethod = "right"
    padding: PaddingDimensions = 1
    expand: bool = True
    width: int | None = None
    height: int | None = None
    highlight: bool = False
    safe_box: bool = False

    def make(self, content: RenderableType, title: str | Text = None, subtitle: str | Text = None, **overrides) -> Panel:
        kwargs = self.model_dump(
            exclude={
                "title_style",
                "subtitle_style",
                "title_prefix",
                "title_suffix",
                "subtitle_prefix",
                "subtitle_suffix"
            }
        ) | overrides
        if isinstance(kwargs["box"], str):
            kwargs["box"] = getattr(_box, self.box.upper())
        for key in ("style", "border_style"):
            if isinstance(kwargs[key], StyleConfig):
                kwargs[key] = kwargs[key].make()
        for text, text_type in ((title, "title"), (subtitle, "subtitle")):
            if not text:
                continue
            text_style = getattr(self, f"{text_type}_style")
            if isinstance(text_style, TextConfig):
                text = text_style.make(text)
            else:
                text = TextConfig(style=text_style).make(text)
            kwargs[text_type] = text
        return _panel.Panel(content, **kwargs)


class AdmonitionConfig(_pydantic.BaseModel):
    note: PanelConfig = PanelConfig(title_prefix=" ℹ️", border_style=StyleConfig(color=(6, 36, 93), bold=True), title_style=StyleConfig(color=(255, 255, 255), bgcolor=(6, 36, 93), bold=True)),
    important: PanelConfig = PanelConfig(title_prefix=" ❗", border_style=StyleConfig(color=(101, 42, 2), bold=True), title_style=StyleConfig(color=(255, 255, 255), bgcolor=(101, 42, 2), bold=True)),
    hint: PanelConfig = PanelConfig(title_prefix=" 💡", border_style=StyleConfig(color=(0, 47, 23), bold=True), title_style=StyleConfig(color=(255, 255, 255), bgcolor=(0, 47, 23), bold=True)),
    seealso: PanelConfig = PanelConfig(title_prefix=" ↪️", border_style=StyleConfig(color=(0, 47, 23), bold=True), title_style=StyleConfig(color=(255, 255, 255), bgcolor=(0, 47, 23), bold=True)),
    tip: PanelConfig = PanelConfig(title_prefix=" 💡", border_style=StyleConfig(color=(0, 47, 23), bold=True), title_style=StyleConfig(color=(255, 255, 255), bgcolor=(0, 47, 23), bold=True)),
    attention: PanelConfig = PanelConfig(title_prefix=" ⚠️", border_style=StyleConfig(color=(101, 42, 2), bold=True), title_style=StyleConfig(color=(255, 255, 255), bgcolor=(101, 42, 2), bold=True)),
    caution: PanelConfig = PanelConfig(title_prefix=" ⚠️", border_style=StyleConfig(color=(101, 42, 2), bold=True), title_style=StyleConfig(color=(255, 255, 255), bgcolor=(101, 42, 2), bold=True)),
    warning: PanelConfig = PanelConfig(title_prefix=" ⚠️", border_style=StyleConfig(color=(101, 42, 2), bold=True), title_style=StyleConfig(color=(255, 255, 255), bgcolor=(101, 42, 2), bold=True)),
    danger: PanelConfig = PanelConfig(title_prefix=" 🚨", border_style=StyleConfig(color=(78, 17, 27), bold=True), title_style=StyleConfig(color=(255, 255, 255), bgcolor=(78, 17, 27), bold=True)),
    error: PanelConfig = PanelConfig(title_prefix=" ❌", border_style=StyleConfig(color=(78, 17, 27), bold=True), title_style=StyleConfig(color=(255, 255, 255), bgcolor=(78, 17, 27), bold=True)),


class InlineHeadingConfig(_pydantic.BaseModel):
    style: StyleConfig | TextConfig | StyleType = "bold"
    rule: RuleConfig = RuleConfig()

    def make(self, title: str | Text) -> Rule:
        if isinstance(self.style, TextConfig):
            title = self.style.make(title)
        else:
            title = TextConfig(style=self.style).make(title)
        return self.rule.make(title)


class HeadingConfig(_pydantic.BaseModel):
    inline: InlineHeadingConfig = InlineHeadingConfig()
    block: PanelConfig = PanelConfig(),
    force_block: bool = False

    def make(self, content: Group | RenderableType) -> Panel | Rule:
        if self.force_block or isinstance(content, _console.Group):
            return self.block.make(content)
        return self.inline.make(content)


class CodeBlockConfig(_pydantic.BaseModel):
    syntax: SyntaxConfig = SyntaxConfig()
    panel: PanelConfig = PanelConfig()

    def make(
        self,
        code: str,
        lexer: str | Lexer | None = None,
        title: str | Text = None,
        subtitle: str | Text = None,
        line_numbers: bool = False,
        start_line: int = 1,
        line_range: tuple[int | None, int | None] | None = None,
        highlight_lines: set[int] | None = None,
        code_width: int | None = None,
    ):
        syntax = self.syntax.make(
            code,
            lexer=lexer,
            line_numbers=line_numbers,
            start_line=start_line,
            line_range=line_range,
            highlight_lines=highlight_lines,
            code_width=code_width,
        )
        if title or subtitle:
            return self.panel.make(content=syntax, title=title, subtitle=subtitle)
        return syntax


class ColumnConfig(_pydantic.BaseModel):
    header_style: StyleConfig | StyleType = ""
    footer_style: StyleConfig | StyleType = ""
    style: StyleConfig | StyleType = ""
    justify: JustifyMethod = "left"
    vertical: VerticalAlignMethod = "top"
    overflow: OverflowMethod = "ellipsis"
    width: int | None = None
    min_width: int | None = None
    max_width: int | None = None
    ratio: int | None = None
    no_wrap: bool = False

    def make(
        self,
        header: RenderableType = "",
        footer: RenderableType = "",
    ) -> Column:
        kwargs = self.model_dump() | {"header": header, "footer": footer}
        for key in ("header_style", "footer_style", "style"):
            if isinstance(kwargs[key], StyleConfig):
                kwargs[key] = kwargs[key].make()
        return _table.Column(**kwargs)


class TableConfig(_pydantic.BaseModel):
    width: int | None = None
    min_width: int | None = None
    box: BoxName | Box = "heavy_head"
    safe_box: bool = False
    padding: PaddingDimensions = (0, 1)
    collapse_padding: bool = False
    pad_edge: bool = True
    expand: bool = False
    show_header: bool = True
    show_footer: bool = False
    show_edge: bool = True
    show_lines: bool = False
    leading: int = 0
    style: StyleConfig | StyleType = "none"
    row_styles: Iterable[StyleConfig | StyleType] = None
    header_style: StyleConfig | StyleType = "table.header"
    footer_style: StyleConfig | StyleType = "table.footer"
    border_style: StyleConfig | StyleType = None
    title_style: TextConfig | StyleConfig | StyleType = None
    caption_style: TextConfig | StyleConfig | StyleType = None
    title_justify: JustifyMethod = "center"
    caption_justify: JustifyMethod = "center"
    highlight: bool = False

    def make(
        self,
        *headers: str | Column,
        title: str | Text | None = None,
        caption: str | Text | None = None,
        **overrides,
    ) -> Table:
        kwargs = self.model_dump() | overrides
        if isinstance(kwargs["box"], str):
            kwargs["box"] = getattr(_box, self.box.upper())
        for style_key in (
            "style",
            "header_style",
            "footer_style",
            "border_style",
        ):
            if isinstance(kwargs[style_key], StyleConfig):
                kwargs[style_key] = kwargs[style_key].make()
        for text, text_key, text_style_key in (
            (title, "title", "title_style"),
            (caption, "caption", "caption_style")
        ):
            style = kwargs[text_style_key]
            if isinstance(style, TextConfig):
                kwargs[text_style_key] = style.style.make()
            elif isinstance(style, StyleConfig):
                kwargs[text_style_key] = style.make()
            if text:
                if isinstance(style, TextConfig):
                    text = style.make(text)
                else:
                    text = TextConfig(style=style).make(text)
                kwargs[text_key] = text
        if kwargs["row_styles"]:
            kwargs["row_styles"] = [
                style.make() if isinstance(style, StyleConfig) else style for style in kwargs["row_styles"]
            ]
        return _table.Table(*headers, **kwargs)


class FieldListConfig(_pydantic.BaseModel):
    table: TableConfig = TableConfig(box="simple", show_header=False, padding=(0,1,1,0), show_edge=False)
    title_column: ColumnConfig = ColumnConfig(style="bold")
    description_column: ColumnConfig = ColumnConfig()
    colon_column: ColumnConfig = ColumnConfig(style="rgb(0,150,0)")

    def make(self, items: Sequence[tuple[RenderableType, RenderableType]]) -> Table:
        headers = [self.title_column.make(), self.colon_column.make(), self.description_column.make()]
        table = self.table.make(*headers, rows=items)
        for item in items:
            table.add_row(item[0], item[1])
        return table


class Config(_pydantic.BaseModel):
    admonition: AdmonitionConfig = AdmonitionConfig()
    code_block: CodeBlockConfig = CodeBlockConfig()
    field_list: FieldListConfig = FieldListConfig()
    heading: Sequence[HeadingConfig] = (
        HeadingConfig(
            inline=InlineHeadingConfig(style=StyleConfig(color=(150, 0, 170), bold=True)),
            block=PanelConfig(style_border=StyleConfig(color=(150, 0, 170), bold=True)),
        ),
        HeadingConfig(
            inline=InlineHeadingConfig(style=StyleConfig(color=(25, 100, 175), bold=True)),
            block=PanelConfig(style_border=StyleConfig(color=(25, 100, 175), bold=True)),
        ),
        HeadingConfig(
            inline=InlineHeadingConfig(style=StyleConfig(color=(100, 160, 0), bold=True)),
            block=PanelConfig(style_border=StyleConfig(color=(100, 160, 0), bold=True)),
        ),
        HeadingConfig(
            inline=InlineHeadingConfig(style=StyleConfig(color=(200, 150, 0), bold=True)),
            block=PanelConfig(style_border=StyleConfig(color=(200, 150, 0), bold=True)),
        ),
        HeadingConfig(
            inline=InlineHeadingConfig(style=StyleConfig(color=(240, 100, 0), bold=True)),
            block=PanelConfig(style_border=StyleConfig(color=(240, 100, 0), bold=True)),
        ),
        HeadingConfig(
            inline=InlineHeadingConfig(style=StyleConfig(color=(220, 0, 35), bold=True)),
            block=PanelConfig(style_border=StyleConfig(color=(220, 0, 35), bold=True)),
        ),
    )
    code_span: TextConfig = TextConfig(
        style=StyleConfig(color=(255, 255, 255), bgcolor=(70, 70, 70), prefix=" ", suffix=" ")
    )
