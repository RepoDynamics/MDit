from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING
from functools import partial as _partial


from mdit import render as _render

from mdit.target import rich, md

if _TYPE_CHECKING:
    from typing import Callable, Sequence


def github(
    prefer_md: bool = False,
    attrs_block: bool = False,
    attrs_inline: bool = False,
    target_anchor: bool = False,
    field_list: bool = False,
    fence: str = "`",
    directive_admo: bool = False,
    directive_code: bool = False,
    directive_image: bool = False,
    directive_figure: bool = False,
    directive_table: bool = False,
    directive_list_table: bool = False,
    directive_toctree: bool = False,
    directive_toggle: bool = True,
    directive_dropdown: bool = False,
    alerts: bool = True,
    picture_theme: bool = True,
    renderer: Callable[[dict | str], str] = _partial(_render.cmarkgfm, unsafe=False),
    rich_export: dict
        | md.RichExportHTMLConfig
        | md.RichExportSVGConfig
        | md.RichExportTextConfig = md.RichExportHTMLConfig()
) -> md.Config:
    #TODO: add exact allowed HTML tags
    # Refs:
    # - https://github.com/github/markup/issues/245
    # - https://gist.github.com/seanh/13a93686bf4c2cb16e658b3cf96807f2
    # - https://gist.github.com/coolaj86/89821fe046623d5503ce5c4133e70506
    # - https://github.com/github/markup
    return md.Config(
        prefer_md=prefer_md,
        attrs_block=attrs_block,
        attrs_inline=attrs_inline,
        target_anchor=target_anchor,
        field_list=field_list,
        directive_admo=directive_admo,
        directive_code=directive_code,
        directive_image=directive_image,
        directive_figure=directive_figure,
        directive_table=directive_table,
        directive_list_table=directive_list_table,
        directive_toctree=directive_toctree,
        directive_toggle=directive_toggle,
        directive_dropdown=directive_dropdown,
        alerts=alerts,
        picture_theme=picture_theme,
        fence=fence,
        renderer=renderer,
        rich_export=rich_export
    )


def pypi(
    prefer_md: bool = False,
    attrs_block: bool = False,
    attrs_inline: bool = False,
    target_anchor: bool = False,
    field_list: bool = False,
    fence: str = "`",
    directive_admo: bool = False,
    directive_code: bool = False,
    directive_image: bool = False,
    directive_figure: bool = False,
    directive_table: bool = False,
    directive_list_table: bool = False,
    directive_toctree: bool = False,
    directive_toggle: bool = True,
    directive_dropdown: bool = False,
    alerts: bool = False,
    picture_theme: bool = False,
    renderer: Callable[[dict | str], str] = _render.readme_renderer,
    rich_export: dict
        | md.RichExportHTMLConfig
        | md.RichExportSVGConfig
        | md.RichExportTextConfig = md.RichExportHTMLConfig()
):
    return md.Config(
        prefer_md=prefer_md,
        attrs_block=attrs_block,
        attrs_inline=attrs_inline,
        target_anchor=target_anchor,
        field_list=field_list,
        fence=fence,
        directive_admo=directive_admo,
        directive_code=directive_code,
        directive_image=directive_image,
        directive_figure=directive_figure,
        directive_table=directive_table,
        directive_list_table=directive_list_table,
        directive_toctree=directive_toctree,
        directive_toggle=directive_toggle,
        directive_dropdown=directive_dropdown,
        alerts=alerts,
        picture_theme=picture_theme,
        renderer=renderer,
        rich_export=rich_export,
    )


def sphinx(
    prefer_md: bool = True,
    attrs_block: bool = True,
    attrs_inline: bool = True,
    target_anchor: bool = True,
    field_list: bool = True,
    fence: str = ":",
    directive_admo: bool = True,
    directive_code: bool = True,
    directive_image: bool = True,
    directive_figure: bool = True,
    directive_table: bool = True,
    directive_list_table: bool = True,
    directive_toctree: bool = True,
    directive_toggle: bool = True,
    directive_dropdown: bool = True,
    alerts: bool = False,
    picture_theme: bool = True,
    renderer: Callable[[dict | str], str] = _render.sphinx,
    rich_export: dict
        | md.RichExportHTMLConfig
        | md.RichExportSVGConfig
        | md.RichExportTextConfig = md.RichExportSVGConfig()
):
    return md.Config(
        prefer_md=prefer_md,
        attrs_block=attrs_block,
        attrs_inline=attrs_inline,
        target_anchor=target_anchor,
        field_list=field_list,
        directive_admo=directive_admo,
        directive_code=directive_code,
        directive_image=directive_image,
        directive_figure=directive_figure,
        directive_table=directive_table,
        directive_list_table=directive_list_table,
        directive_toctree=directive_toctree,
        directive_toggle=directive_toggle,
        directive_dropdown=directive_dropdown,
        alerts=alerts,
        picture_theme=picture_theme,
        fence=fence,
        renderer=renderer,
        rich_export=rich_export,
    )


def console(
    code_block: dict | rich.CodeBlockConfig = rich.CodeBlockConfig(),
    ordered_list: dict | rich.OrderedListConfig = rich.OrderedListConfig(
        table=rich.TableConfig(box=rich.NamedBox(name="simple"), show_header=False, padding=(0,1,0,0), show_edge=False),
        marker_column=rich.ColumnConfig(style="rgb(0,150,0) bold", justify="right"),
        item_column=rich.ColumnConfig(justify="left"),
    ),
    unordered_list: dict | rich.UnorderedListConfig = rich.UnorderedListConfig(
        table=rich.TableConfig(box=rich.NamedBox(name="simple"), show_header=False, padding=(0,1,0,0), show_edge=False),
        marker_column=rich.ColumnConfig(style="rgb(0,150,0)"),
        item_column=rich.ColumnConfig(),
        marker="•",
    ),
    field_list: dict | rich.FieldListConfig = rich.FieldListConfig(
        table=rich.TableConfig(box=rich.NamedBox(name="simple"), show_header=False, padding=(0,1,0,0), show_edge=False),
        title_column=rich.ColumnConfig(style="bold"),
        description_column=rich.ColumnConfig(),
        colon_column=rich.ColumnConfig(style="rgb(0,150,0)"),
    ),
    code_span: dict | rich.TextConfig = rich.TextConfig(
        style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(70, 70, 70), prefix=" ", suffix=" ")
    ),
    dropdown: dict | rich.PanelConfig = rich.PanelConfig(
        border_style=rich.StyleConfig(bold=True),
    ),
    dropdown_class: dict[str, rich.PanelConfig | dict] | None = None,
    heading: Sequence[dict | rich.HeadingConfig] = (
        rich.HeadingConfig(
            inline=rich.InlineHeadingConfig(style=rich.StyleConfig(color=(150, 0, 170), bold=True)),
            block=rich.PanelConfig(style_border=rich.StyleConfig(color=(150, 0, 170), bold=True)),
        ),
        rich.HeadingConfig(
            inline=rich.InlineHeadingConfig(style=rich.StyleConfig(color=(25, 100, 175), bold=True)),
            block=rich.PanelConfig(style_border=rich.StyleConfig(color=(25, 100, 175), bold=True)),
        ),
        rich.HeadingConfig(
            inline=rich.InlineHeadingConfig(style=rich.StyleConfig(color=(100, 160, 0), bold=True)),
            block=rich.PanelConfig(style_border=rich.StyleConfig(color=(100, 160, 0), bold=True)),
        ),
        rich.HeadingConfig(
            inline=rich.InlineHeadingConfig(style=rich.StyleConfig(color=(200, 150, 0), bold=True)),
            block=rich.PanelConfig(style_border=rich.StyleConfig(color=(200, 150, 0), bold=True)),
        ),
        rich.HeadingConfig(
            inline=rich.InlineHeadingConfig(style=rich.StyleConfig(color=(240, 100, 0), bold=True)),
            block=rich.PanelConfig(style_border=rich.StyleConfig(color=(240, 100, 0), bold=True)),
        ),
        rich.HeadingConfig(
            inline=rich.InlineHeadingConfig(style=rich.StyleConfig(color=(220, 0, 35), bold=True)),
            block=rich.PanelConfig(style_border=rich.StyleConfig(color=(220, 0, 35), bold=True)),
        ),
    ),
    admonition_note: rich.PanelConfig = rich.PanelConfig(
        title_style=rich.TextConfig(
            prefix="ℹ️ ",
            style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(6, 36, 93), bold=True)
        ),
    ),
    admonition_important: rich.PanelConfig = rich.PanelConfig(
        title_style = rich.TextConfig(
            prefix="📢 ",
            style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(101, 42, 2), bold=True)
        ),
    ),
    admonition_hint: rich.PanelConfig = rich.PanelConfig(
        title_style=rich.TextConfig(
            prefix="🔎 ",
            style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(0, 47, 23), bold=True)
        ),
    ),
    admonition_seealso: rich.PanelConfig = rich.PanelConfig(
        title_style=rich.TextConfig(
            prefix="↪️ ",
            style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(0, 47, 23), bold=True)
        ),
    ),
    admonition_tip: rich.PanelConfig = rich.PanelConfig(
        title_style=rich.TextConfig(
            prefix="💡 ",
            style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(0, 47, 23), bold=True)
        ),
    ),
    admonition_attention: rich.PanelConfig = rich.PanelConfig(
        title_style=rich.TextConfig(
            prefix="⚠️ ",
            style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(101, 42, 2), bold=True)
        ),
    ),
    admonition_caution: rich.PanelConfig = rich.PanelConfig(
        title_style=rich.TextConfig(
            prefix="❗ ",
            style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(101, 42, 2), bold=True)
        ),
    ),
    admonition_warning: rich.PanelConfig = rich.PanelConfig(
        title_style=rich.TextConfig(
            prefix="🚨 ",
            style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(101, 42, 2), bold=True)
        ),
    ),
    admonition_danger: rich.PanelConfig = rich.PanelConfig(
        title_style=rich.TextConfig(
            prefix="🚩 ",
            style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(78, 17, 27), bold=True)
        ),
    ),
    admonition_error: rich.PanelConfig = rich.PanelConfig(
        title_style=rich.TextConfig(
            prefix="❌ ",
            style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(78, 17, 27), bold=True)
        ),
    ),
) -> rich.Config:
    return rich.Config(
        code_block=code_block,
        ordered_list=ordered_list,
        unordered_list=unordered_list,
        field_list=field_list,
        heading=heading,
        code_span=code_span,
        dropdown=dropdown,
        dropdown_class=dropdown_class or {},
        admonition_note=admonition_note,
        admonition_important=admonition_important,
        admonition_hint=admonition_hint,
        admonition_seealso=admonition_seealso,
        admonition_tip=admonition_tip,
        admonition_attention=admonition_attention,
        admonition_caution=admonition_caution,
        admonition_warning=admonition_warning,
        admonition_danger=admonition_danger,
        admonition_error=admonition_error,
    )
