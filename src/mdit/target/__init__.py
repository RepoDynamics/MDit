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
    alerts: bool = True,
    picture_theme: bool = True,
    renderer: Callable[[dict | str], str] = _partial(_render.cmarkgfm, unsafe=False),
    rich_export: dict
        | md.RichExportHTMLConfig
        | md.RichExportSVGConfig
        | md.RichExportTextConfig = md.RichExportHTMLConfig()
) -> md.Config:
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
    alerts: bool = False,
    picture_theme: bool = True,
    renderer: Callable[[dict | str], str] = _partial(
        _render.sphinx,
        config={
            "extensions": [
                'myst_parser',
                'sphinx_design',
                'sphinx_togglebutton'
            ],
            "myst_enable_extensions": ["colon_fence"],
            "html_theme": "pydata_sphinx_theme",
            "html_title": "",
        }
    ),
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
        fence=fence,
        directive_admo=directive_admo,
        directive_code=directive_code,
        directive_image=directive_image,
        directive_figure=directive_figure,
        directive_table=directive_table,
        directive_list_table=directive_list_table,
        directive_toctree=directive_toctree,
        directive_toggle=directive_toggle,
        alerts=alerts,
        picture_theme=picture_theme,
        renderer=renderer,
        rich_export=rich_export,
    )


def console(
    admonition: dict | rich.AdmonitionConfig = rich.AdmonitionConfig(),
    code_block: dict | rich.CodeBlockConfig = rich.CodeBlockConfig(),
    field_list: dict | rich.FieldListConfig = rich.FieldListConfig(),
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
    code_span: dict | rich.TextConfig = rich.TextConfig(
        style=rich.StyleConfig(color=(255, 255, 255), bgcolor=(70, 70, 70), prefix=" ", suffix=" ")
    ),
) -> rich.Config:
    return rich.Config(
        admonition=admonition,
        code_block=code_block,
        field_list=field_list,
        heading=heading,
        code_span=code_span,
    )
