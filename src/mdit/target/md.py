from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING
import textwrap as _textwrap

import pydantic as _pydantic
import rich as _rich

if _TYPE_CHECKING:
    from typing import Literal, Callable
    from rich.terminal_theme import TerminalTheme
    from mdit.target.rich import ConsoleConfig as RichConsoleConfig
    from rich.console import RenderableType


RICH_SVG_TEMPLATE = _textwrap.dedent(
    """<svg class="rich-terminal" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <style>
    @font-face {{
        font-family: "Fira Code";
        src: local("FiraCode-Regular"),
            url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Regular.woff2") format("woff2"),
            url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff/FiraCode-Regular.woff") format("woff");
        font-style: normal;
        font-weight: 400;
    }}
    @font-face {{
        font-family: "Fira Code";
        src: local("FiraCode-Bold"),
            url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Bold.woff2") format("woff2"),
            url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff/FiraCode-Bold.woff") format("woff");
        font-style: bold;
        font-weight: 700;
    }}
    .{unique_id}-matrix {{
        font-family: Fira Code, monospace;
        font-size: {char_height}px;
        line-height: {line_height}px;
        font-variant-east-asian: full-width;
    }}
    .{unique_id}-title {{
        font-size: 18px;
        font-weight: bold;
        font-family: arial;
    }}
    {styles}
    </style>
    <defs>
    <clipPath id="{unique_id}-clip-terminal">
      <rect x="0" y="0" width="{terminal_width}" height="{terminal_height}" />
    </clipPath>
    {lines}
    </defs>
    {chrome}
    <g transform="translate({terminal_x}, {terminal_y})" clip-path="url(#{unique_id}-clip-terminal)">
    {backgrounds}
    <g class="{unique_id}-matrix">
    {matrix}
    </g>
    </g>
    </svg>"""
)


class RichExportConfig(_pydantic.BaseModel):
    console: RichConsoleConfig | None = None

    def make_console(self):
        return self.console.make(quiet=True, record=True) if self.console else _rich.console.Console(
            quiet=True, record=True
        )


class RichExportHTMLConfig(RichExportConfig):
    """Rich export HTML configurations.

    References
    ----------
    - [Rich API Reference](https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.export_html)
    """
    theme: TerminalTheme | None = None
    inline_styles: bool = True
    code_format: str = """<pre style="font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><code style="font-family:inherit">{code}</code></pre>"""

    def export(self, content: RenderableType):
        console = self.make_console()
        console.print(content)
        return console.export_html(theme=self.theme, inline_styles=self.inline_styles, code_format=self.code_format)


class RichExportSVGConfig(RichExportConfig):
    """Rich export SVG configurations.

    References
    ----------
    - [Rich API Reference](https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.export_svg)
    """
    title: str | None = ""
    theme: TerminalTheme | None = None
    code_format: str = RICH_SVG_TEMPLATE
    font_aspect_ratio: float = 0.61
    unique_id: str | None = None

    def export(self, content: RenderableType):
        console = self.make_console()
        console.print(content)
        return console.export_svg(
            title=self.title,
            theme=self.theme,
            code_format=self.code_format,
            font_aspect_ratio=self.font_aspect_ratio,
            unique_id=self.unique_id,
        )


class RichExportTextConfig(RichExportConfig):
    """Rich export text configurations.

    References
    ----------
    - [Rich API Reference](https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.export_text)
    """
    styles: bool = False

    def export(self, content: RenderableType):
        console = self.make_console()
        console.print(content)
        return console.export_text(styles=self.styles)


class Config(_pydantic.BaseModel):
    prefer_md: bool
    attrs_block: bool
    attrs_inline: bool
    target_anchor: bool
    field_list: bool
    directive_admo: bool
    directive_code: bool
    directive_image: bool
    directive_figure: bool
    directive_table: bool
    directive_list_table: bool
    directive_toctree: bool
    directive_toggle: bool
    alerts: bool
    picture_theme: bool
    fence: Literal["`", ":", "~"]
    renderer: Callable[[dict | str], str]
    rich_export: RichExportHTMLConfig | RichExportSVGConfig | RichExportTextConfig