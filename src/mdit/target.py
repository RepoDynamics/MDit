from mdit.protocol import TargetConfig


def custom(
    prefer_md: bool,
    attrs_block: bool,
    attrs_inline: bool,
    target_anchor: bool,
    fence: str,
    directive_admo: bool,
    directive_code: bool,
    directive_image: bool,
    directive_figure: bool,
    directive_toctree: bool,
    alerts: bool,
    picture_theme: bool,
):
    return TargetConfig(
        prefer_md=prefer_md,
        attrs_block=attrs_block,
        attrs_inline=attrs_inline,
        target_anchor=target_anchor,
        fence=fence,
        directive_admo=directive_admo,
        directive_code=directive_code,
        directive_image=directive_image,
        directive_figure=directive_figure,
        directive_toctree=directive_toctree,
        alerts=alerts,
        picture_theme=picture_theme,
    )


def github(
    prefer_md: bool = False,
    attrs_block: bool = False,
    attrs_inline: bool = False,
    target_anchor: bool = False,
    fence: str = "`",
    directive_admo: bool = False,
    directive_code: bool = False,
    directive_image: bool = False,
    directive_figure: bool = False,
    directive_toctree: bool = False,
    alerts: bool = True,
    picture_theme: bool = True,
):
    return TargetConfig(
        prefer_md=prefer_md,
        attrs_block=attrs_block,
        attrs_inline=attrs_inline,
        target_anchor=target_anchor,
        fence=fence,
        directive_admo=directive_admo,
        directive_code=directive_code,
        directive_image=directive_image,
        directive_figure=directive_figure,
        directive_toctree=directive_toctree,
        alerts=alerts,
        picture_theme=picture_theme,
    )


def pypi(
    prefer_md: bool = False,
    attrs_block: bool = False,
    attrs_inline: bool = False,
    target_anchor: bool = False,
    fence: str = "`",
    directive_admo: bool = False,
    directive_code: bool = False,
    directive_image: bool = False,
    directive_figure: bool = False,
    directive_toctree: bool = False,
    alerts: bool = False,
    picture_theme: bool = False,
):
    return TargetConfig(
        prefer_md=prefer_md,
        attrs_block=attrs_block,
        attrs_inline=attrs_inline,
        target_anchor=target_anchor,
        fence=fence,
        directive_admo=directive_admo,
        directive_code=directive_code,
        directive_image=directive_image,
        directive_figure=directive_figure,
        directive_toctree=directive_toctree,
        alerts=alerts,
        picture_theme=picture_theme,
    )


def sphinx(
    prefer_md: bool = True,
    attrs_block: bool = True,
    attrs_inline: bool = True,
    target_anchor: bool = True,
    fence: str = "`",
    directive_admo: bool = True,
    directive_code: bool = True,
    directive_image: bool = True,
    directive_figure: bool = True,
    directive_toctree: bool = True,
    alerts: bool = False,
    picture_theme: bool = True,
):
    return TargetConfig(
        prefer_md=prefer_md,
        attrs_block=attrs_block,
        attrs_inline=attrs_inline,
        target_anchor=target_anchor,
        fence=fence,
        directive_admo=directive_admo,
        directive_code=directive_code,
        directive_image=directive_image,
        directive_figure=directive_figure,
        directive_toctree=directive_toctree,
        alerts=alerts,
        picture_theme=picture_theme,
    )
