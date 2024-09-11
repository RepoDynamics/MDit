from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING
from functools import partial as _partial

from mdit.protocol import TargetConfig, ANSITargetConfig, ANSIInlineStyle, ANSIBlockStyle, ANSIAdmonitionStyle, ANSICodeBlockStyle
from mdit import render as _render

if _TYPE_CHECKING:
    from typing import Callable


def custom(
    prefer_md: bool,
    attrs_block: bool,
    attrs_inline: bool,
    target_anchor: bool,
    field_list: bool,
    fence: str,
    directive_admo: bool,
    directive_code: bool,
    directive_image: bool,
    directive_figure: bool,
    directive_toctree: bool,
    directive_toggle: bool,
    alerts: bool,
    picture_theme: bool,
):
    return TargetConfig(
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
        directive_toctree=directive_toctree,
        directive_toggle=directive_toggle,
        alerts=alerts,
        picture_theme=picture_theme,
    )


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
    directive_toctree: bool = False,
    directive_toggle: bool = True,
    alerts: bool = True,
    picture_theme: bool = True,
):
    return TargetConfig(
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
        directive_toctree=directive_toctree,
        directive_toggle=directive_toggle,
        alerts=alerts,
        picture_theme=picture_theme,
        renderer=None
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
    directive_toctree: bool = False,
    directive_toggle: bool = True,
    alerts: bool = False,
    picture_theme: bool = False,
):
    return TargetConfig(
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
        directive_toctree=directive_toctree,
        directive_toggle=directive_toggle,
        alerts=alerts,
        picture_theme=picture_theme,
        renderer=None
    )


def sphinx(
    prefer_md: bool = True,
    attrs_block: bool = True,
    attrs_inline: bool = True,
    target_anchor: bool = True,
    field_list: bool = True,
    fence: str = "`",
    directive_admo: bool = True,
    directive_code: bool = True,
    directive_image: bool = True,
    directive_figure: bool = True,
    directive_toctree: bool = True,
    directive_toggle: bool = True,
    alerts: bool = False,
    picture_theme: bool = True,
    renderer: Callable[[dict], str] = _partial(
        _render.sphinx,
        config={
            "extensions": ['myst_parser', 'sphinx_togglebutton'],
            "myst_enable_extensions": ["colon_fence"],
            "html_theme": "pydata_sphinx_theme",
            "html_title": "",
        }
    ),
):
    return TargetConfig(
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
        directive_toctree=directive_toctree,
        directive_toggle=directive_toggle,
        alerts=alerts,
        picture_theme=picture_theme,
        renderer=renderer,
    )


def ansi(
    code_span: dict | ANSIInlineStyle = ANSIInlineStyle(text_color=(255, 255, 255), bg_color=(70, 70, 70), margin_left=1, margin_right=1),
    heading: list[ANSIBlockStyle | dict] = (
        ANSIBlockStyle(text_styles="bold", text_color=(150, 0, 170)),
        ANSIBlockStyle(text_styles="bold", text_color=(25, 100, 175)),
        ANSIBlockStyle(text_styles="bold", text_color=(100, 160, 0)),
        ANSIBlockStyle(text_styles="bold", text_color=(200, 150, 0)),
        ANSIBlockStyle(text_styles="bold", text_color=(240, 100, 0)),
        ANSIBlockStyle(text_styles="bold", text_color=(220, 0, 35)),
    ),
    field_list_title: ANSIInlineStyle | dict = ANSIInlineStyle(text_styles="bold"),
    field_list_description: ANSIBlockStyle | dict = ANSIBlockStyle(),
    admonition_note: ANSIAdmonitionStyle | dict = ANSIAdmonitionStyle(emoji="ℹ️", title_bg_color=(6, 36, 93)),
    admonition_important: ANSIAdmonitionStyle | dict = ANSIAdmonitionStyle(emoji="❗", title_bg_color=(101, 42, 2)),
    admonition_hint: ANSIAdmonitionStyle | dict = ANSIAdmonitionStyle(emoji="💡", title_bg_color=(0, 47, 23)),
    admonition_seealso: ANSIAdmonitionStyle | dict = ANSIAdmonitionStyle(emoji="↪️", title_bg_color=(0, 47, 23)),
    admonition_tip: ANSIAdmonitionStyle | dict = ANSIAdmonitionStyle(emoji="💡", title_bg_color=(0, 47, 23)),
    admonition_attention: ANSIAdmonitionStyle | dict = ANSIAdmonitionStyle(emoji="⚠️", title_bg_color=(101, 42, 2)),
    admonition_caution: ANSIAdmonitionStyle | dict = ANSIAdmonitionStyle(emoji="⚠️", title_bg_color=(101, 42, 2)),
    admonition_warning: ANSIAdmonitionStyle | dict = ANSIAdmonitionStyle(emoji="⚠️", title_bg_color=(101, 42, 2)),
    admonition_danger: ANSIAdmonitionStyle | dict = ANSIAdmonitionStyle(emoji="🚨", title_bg_color=(78, 17, 27)),
    admonition_error: ANSIAdmonitionStyle | dict = ANSIAdmonitionStyle(emoji="❌", title_bg_color=(78, 17, 27)),
    code_block: dict | ANSICodeBlockStyle = ANSICodeBlockStyle(),
) -> ANSITargetConfig:
    return ANSITargetConfig(
        code_span=ANSIInlineStyle(**code_span) if isinstance(code_span, dict) else code_span,
        heading=[ANSIBlockStyle(**style) if isinstance(style, dict) else style for style in heading],
        field_list_title=ANSIInlineStyle(**field_list_title) if isinstance(field_list_title, dict) else field_list_title,
        field_list_description=ANSIBlockStyle(**field_list_description) if isinstance(field_list_description, dict) else field_list_description,
        admonition_note=ANSIAdmonitionStyle(**admonition_note) if isinstance(admonition_note, dict) else admonition_note,
        admonition_important=ANSIAdmonitionStyle(**admonition_important) if isinstance(admonition_important, dict) else admonition_important,
        admonition_hint=ANSIAdmonitionStyle(**admonition_hint) if isinstance(admonition_hint, dict) else admonition_hint,
        admonition_seealso=ANSIAdmonitionStyle(**admonition_seealso) if isinstance(admonition_seealso, dict) else admonition_seealso,
        admonition_tip=ANSIAdmonitionStyle(**admonition_tip) if isinstance(admonition_tip, dict) else admonition_tip,
        admonition_attention=ANSIAdmonitionStyle(**admonition_attention) if isinstance(admonition_attention, dict) else admonition_attention,
        admonition_caution=ANSIAdmonitionStyle(**admonition_caution) if isinstance(admonition_caution, dict) else admonition_caution,
        admonition_warning=ANSIAdmonitionStyle(**admonition_warning) if isinstance(admonition_warning, dict) else admonition_warning,
        admonition_danger=ANSIAdmonitionStyle(**admonition_danger) if isinstance(admonition_danger, dict) else admonition_danger,
        admonition_error=ANSIAdmonitionStyle(**admonition_error) if isinstance(admonition_error, dict) else admonition_error,
        code_block=ANSICodeBlockStyle(**code_block) if isinstance(code_block, dict) else code_block,

    )