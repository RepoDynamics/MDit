from __future__ import annotations

import sys as _sys
import tempfile as _tempfile
from typing import TYPE_CHECKING as _TYPE_CHECKING
from pathlib import Path as _Path
import logging as _logging
import io as _io
import copy as _copy
import warnings as _warnings
from functools import partial as _partial

import cmarkgfm as _gfm_pypi
from readme_renderer import markdown as _readme_renderer_md, clean as _readme_renderer_clean
from sphinx.application import Sphinx as _Sphinx
import markdown_it as _mdit
import markdown_it.utils as _mdit_utils
from mdit_py_plugins.amsmath import amsmath_plugin as _mdit_plugin_amsmath
from mdit_py_plugins.anchors import anchors_plugin as _mdit_plugin_anchors
from mdit_py_plugins.attrs import attrs_block_plugin as _mdit_plugin_attrs_block, attrs_plugin as _mdit_plugin_attrs
from mdit_py_plugins.colon_fence import colon_fence_plugin as _mdit_plugin_colon_fence
from mdit_py_plugins.deflist import deflist_plugin as _mdit_plugin_deflist
from mdit_py_plugins.dollarmath import dollarmath_plugin as _mdit_plugin_dollarmath
from mdit_py_plugins.field_list import fieldlist_plugin as _mdit_plugin_fieldlist
from mdit_py_plugins.footnote import footnote_plugin as _mdit_plugin_footnote
from mdit_py_plugins.front_matter import front_matter_plugin as _mdit_plugin_front_matter
from mdit_py_plugins.myst_blocks import myst_block_plugin as _mdit_plugin_myst_block
from mdit_py_plugins.myst_role import myst_role_plugin as _mdit_plugin_myst_role
from mdit_py_plugins.substitution import substitution_plugin as _mdit_plugin_substitution
from mdit_py_plugins.tasklists import tasklists_plugin as _mdit_plugin_tasklists
from mdit_py_plugins.wordcount import wordcount_plugin as _mdit_plugin_wordcount
import pyserials as _ps

if _TYPE_CHECKING:
    from typing import IO, Literal, Callable


def get_sphinx_config(
    config: dict | None = None,
    append_list: bool = True,
    append_dict: bool = True,
):
    config_default = {
        "extensions": [
            'myst_nb',
            'sphinx_design',
            'sphinx_togglebutton',
            'sphinx_copybutton',
            'sphinxcontrib.mermaid',
            'sphinx_tippy',
        ],
        "myst_enable_extensions": [
            "amsmath",
            "attrs_inline",
            "colon_fence",
            "deflist",
            "dollarmath",
            "fieldlist",
            "html_admonition",
            "html_image",
            "linkify",
            "replacements",
            "smartquotes",
            "strikethrough",
            "substitution",
            "tasklist",
        ],
        "html_theme": "pydata_sphinx_theme",
        "html_theme_options": {
            "pygments_light_style": "default",
            "pygments_dark_style": "monokai",
        },
        "html_title": "",
    }
    config_final = _copy.deepcopy(config) or {}
    _ps.update.dict_from_addon(
        data=config_final,
        addon=config_default,
        append_list=append_list,
        append_dict=append_dict,
        raise_duplicates=False,
        raise_type_mismatch=False,
    )
    return config_final


def sphinx(
    content: str | dict[str, str],
    config: dict | None = None,
    status: IO[str] | None = None,
    warning: IO[str] | None = None,
    warnings_are_errors: bool = False,
    fresh_env: bool = True,
    tags: list[str] = (),
    verbosity: int = 0,
    parallel: int = 0,
    keep_going: bool = True,
    pdb: bool = False,
):
    if isinstance(content, str):
        content = {"index": content}
    if config is None:
        config = get_sphinx_config()
    with _tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = _Path(temp_dir)
        src_dir = temp_dir / "source"
        for rel_path, text in content.items():
            filepath = (src_dir / rel_path).with_suffix(".md")
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                f.write(text)
        out_dir = temp_dir / "build"
        _Sphinx(
            srcdir=src_dir,
            confdir=None,
            outdir=out_dir,
            doctreedir=temp_dir / "doctrees",
            buildername="zundler",
            confoverrides=config,
            status=status or _io.StringIO(),
            warning=warning or _io.StringIO(),
            freshenv=fresh_env,
            warningiserror=warnings_are_errors,
            tags=tags,
            verbosity=verbosity,
            parallel=parallel,
            keep_going=keep_going,
            pdb=pdb,
        ).build(force_all=True)
        return (out_dir / "index.html").read_text()


def markdownit(
    source: str | dict[str, str],
    components_core: set[
        Literal['block', 'inline', 'linkify', 'normalize', 'replacements', 'smartquotes', 'text_join']
    ] = ('block', 'inline', 'linkify', 'normalize', 'replacements', 'smartquotes', 'text_join'),
    components_block: set[
        Literal[
            'blockquote',
            'code',
            'fence',
            'heading',
            'hr',
            'html_block',
            'lheading',
            'list',
            'paragraph',
            'reference',
            'table',
        ]
    ] = (
        'blockquote',
        'code',
        'fence',
        'heading',
        'hr',
        'html_block',
        'lheading',
        'list',
        'paragraph',
        'reference',
        'table',
    ),
    components_inline: set[
        Literal[
            'autolink',
            'backticks',
            'balance_pairs',
            'emphasis',
            'entity',
            'escape',
            'fragments_join',
            'html_inline',
            'image',
            'link',
            'linkify',
            'newline',
            'strikethrough',
            'text'
        ]
    ] = (
            'autolink',
            'backticks',
            'balance_pairs',
            'emphasis',
            'entity',
            'escape',
            'fragments_join',
            'html_inline',
            'image',
            'link',
            'linkify',
            'newline',
            'strikethrough',
            'text'
    ),
    plugins: set[Callable | tuple[Callable, dict]] = (
        _partial(_mdit_plugin_amsmath, renderer=None),
        _partial(
            _mdit_plugin_anchors,
            min_level=1,
            max_level=6,
            slug_func=None,
            permalink=True,
            permalinkSymbol='¶',
            permalinkBefore=False,
            permalinkSpace=True,
        ),
        _partial(
            _mdit_plugin_attrs,
            after=('image', 'code_inline', 'link_close', 'span_close'),
            spans=True,
            span_after='link',
        ),
        _mdit_plugin_attrs_block,
        _mdit_plugin_colon_fence,
        _mdit_plugin_deflist,
        _partial(
            _mdit_plugin_dollarmath,
            allow_labels=True,
            allow_space=True,
            allow_digits=True,
            allow_blank_lines=True,
            double_inline=False,
        ),
        _mdit_plugin_fieldlist,
        _partial(_mdit_plugin_footnote, inline=True, move_to_end=True, always_match_refs=True),
        _mdit_plugin_front_matter,
        _mdit_plugin_myst_block,
        _mdit_plugin_myst_role,
        _partial(_mdit_plugin_substitution, start_delimiter='{', end_delimiter='}'),
        _partial(_mdit_plugin_tasklists, enabled=False, label=False, label_after=False),
        _partial(_mdit_plugin_wordcount, per_minute=200, store_text=False),
    ),
    env: dict | None = None,
    html: bool = True,
    linkify: bool = True,
    linkify_fuzzy_links: bool = True,
    typographer: bool = True,
    quotes: str = '“”‘’',
    xhtml_out: bool = True,
    breaks: bool = True,
    lang_prefix: str = 'language-',
    highlight: Callable[[str, str, str], str] = None,
):
    """Convert Markdown to HTML using the [`markdown-it-py`](https://markdown-it-py.readthedocs.io/) library.
    
    Parameters
    ----------
    source : str
        Markdown source text to convert to HTML.
    components_core : set of {'block', 'inline', 'linkify', 'normalize', 'replacements', 'smartquotes', 'text_join'}
        Enabled core components
        (cf. [`markdown-it-py` source code](https://github.com/executablebooks/markdown-it-py/tree/c10312e2e475a22edb92abede15d3dcabd0cac0c/markdown_it/rules_core)).
    components_block : set of {'blockquote', 'code', 'fence', 'heading', 'hr', 'html_block', 'lheading', 'list', 'paragraph', 'reference', 'table'}
        Enabled block components
        (cf. [`markdown-it-py` source code](https://github.com/executablebooks/markdown-it-py/tree/c10312e2e475a22edb92abede15d3dcabd0cac0c/markdown_it/rules_block)).
    components_inline : set of {'autolink', 'backticks', 'emphasis', 'entity', 'escape', 'html_inline', 'image', 'link', 'linkify', 'newline', 'strikethrough', 'text'}
        Enabled inline components
        (cf. [`markdown-it-py` source code](https://github.com/executablebooks/markdown-it-py/tree/c10312e2e475a22edb92abede15d3dcabd0cac0c/markdown_it/rules_inline)).
    plugins : set of Callable[[MarkdownIt], None] or tuple[Callable[[MarkdownIt], None], dict], default: (front_matter_plugin,)
        List of plugins to apply to the parser.
        Each entry can either be a callable, or a tuple of a callable and a dictionary of keyword arguments.
        The callable should take as its first argument the `MarkdownIt` parser instance,
        followed by any additional arguments.
        By default, all plugins from the [`mdit_py_plugins` library](https://mdit-py-plugins.readthedocs.io)
        (cf. [source code](https://github.com/executablebooks/mdit-py-plugins/tree/d11bdaf0979e6fae01c35db5a4d1f6a4b4dd8843/mdit_py_plugins))
        except for `admon_plugin`, `container_plugin`, and `texmath_plugin`
        are enabled with their default configurations.
    env : dict, optional
        Environment variables to pass to the parser.
        It is used to pass data between “distributed” rules and return additional metadata
        like reference info, needed for the renderer.
        It can also be used to inject data, e.g., when using the `substitution_plugin`.
    html : bool, default: True
        Allow raw HTML tags in the source text.
    linkify : bool, default: True
        Automatically convert URL-like text to links using the
        [`linkify-it-py`](https://github.com/tsutsu3/linkify-it-py) library.
    linkify_fuzzy_links : bool, default: True
        Enable fuzzy link detection for `linkify`.
        This allows URLs without a protocol schema (e.g., `repodynamics.com`) to be detected as links.
    typographer : bool, default: True
        Enable smartquotes and replacements.
        This will automatically add the `smartquotes` and `replacements` core components as well.
    quotes : str, default: '“”‘’'
        Quote characters.
    xhtml_out : bool, default: True
        Use '/' to close single tags (e.g., `<br />`).
    breaks : bool, default: True
        Convert newlines in paragraphs into `<br>` tags.
    lang_prefix : str, default: 'language-'
        CSS language prefix for fenced blocks.
    highlight: Callable[[str, str, str], str] or None, default: None
        An optional highlighter function `f(content, language, attributes) -> str`
        to apply syntax highlighting to code blocks.

    References
    ----------
    - [`markdown-it` Parser options](https://markdown-it-py.readthedocs.io/en/latest/api/markdown_it.utils.html#markdown_it.utils.OptionsType)
    """
    options = _mdit_utils.OptionsType(
        maxNesting=50,
        html=html,
        linkify=linkify,
        typographer=typographer,
        quotes=quotes,
        xhtmlOut=xhtml_out,
        breaks=breaks,
        langPrefix=lang_prefix,
        highlight=highlight,
    )
    inline_rules = []
    inline_rules2 = []
    # For some reason (?!), `markdown-it-py` has 'inline' and 'inline2' rules.
    # Enabling 'emphasis' and 'strikethrough' adds them to both 'inline' and 'inline2',
    # while enabling 'balance_pairs' and 'fragments_join' only adds them to 'inline2'.
    # All other components are only added to 'inline'.
    # See: https://markdown-it-py.readthedocs.io/en/latest/using.html#the-parser
    # Code: https://github.com/executablebooks/markdown-it-py/blob/c10312e2e475a22edb92abede15d3dcabd0cac0c/markdown_it/parser_inline.py#L38-L51
    # For simplicity we have merged 'inline' and 'inline2' inputs into the 'components_inline' parameter.
    # Now we need to separate them again.
    for rule in components_inline:
        if rule in ("emphasis", "strikethrough"):
            inline_rules.append(rule)
            inline_rules2.append(rule)
        elif rule in ("balance_pairs", "fragments_join"):
            inline_rules2.append(rule)
        else:
            inline_rules.append(rule)
    components = {
        "core": {"rules": list(components_core)},
        "block": {"rules": list(components_block)},
        "inline": {"rules": inline_rules, "rules2": inline_rules2},
    }
    config = _mdit_utils.PresetType(options=options, components=components)
    parser = _mdit.MarkdownIt(config=config)
    if typographer:
        parser.enable(["replacements", "smartquotes"])
    if parser.linkify is not None:
        parser.linkify.set({"fuzzy_link": linkify_fuzzy_links})
    for plugin in plugins:
        if isinstance(plugin, (list, tuple)):
            plugin_func, plugin_config = plugin
        else:
            plugin_func = plugin
            plugin_config = {}
        parser.use(plugin_func, **plugin_config)
    if isinstance(source, str):
        return parser.render(src=source, env=env)
    return {key: parser.render(src=value, env=env) for key, value in source.items()}


def cmarkgfm(
    source: str | dict[str, str],
    extensions: tuple[str, ...] = ('autolink', 'strikethrough', 'table', 'tagfilter', 'tasklist'),
    unsafe: bool = True,
    smart: bool = False,
    normalize: bool = False,
    hard_breaks: bool = False,
    no_breaks: bool = False,
    source_pos: bool = False,
    footnotes: bool = True,
    validate_utf8: bool = False,
    github_pre_lang: bool = True,
    liberal_html_tag: bool = False,
    strikethrough_double_tilde: bool = True,
    table_prefer_style_attributes: bool = False,
):
    """Convert CommonMark or GitHub Flavored Markdown to HTML
    using the [CMarkGFM](https://github.com/theacodes/cmarkgfm) library.

    CMarkGFM is the Markdown to HTML converter
    used by the Python Packaging Authority (PyPA)'s
    [`readme_renderer`](https://github.com/pypa/readme_renderer) library to render
    [package READMEs on PYPI](https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme).
    Using this function with the default arguments will exactly replicate the rendering
    used by PyPI.

    Parameters
    ----------
    source : str
        GitHub Flavored Markdown source text to convert to HTML.
    extensions : Sequence[str], default: ('autolink', 'strikethrough', 'table', 'tagfilter', 'tasklist')
        List of extensions to enable on top of the CommonMark specifications.
        The default value enables all GitHub Flavored Markdown extensions,
        which are currently the only [available extensions in CMarkGFM](https://github.com/theacodes/cmarkgfm/blob/66b131cee950ad30cad9dfbf7f2360270ed105b8/src/cmarkgfm/cmark.py#L118C13-L118C74).
    unsafe: bool, default: True
        Allow rendering unsafe HTML (e.g., `<script>` elements)
        and URLs (e.g., those starting with `javascript:`, `vbscript:`, `file:`, or `data:` (except for `image/png`, `image/gif`, `image/jpeg`, or `image/webp` media types)).
        If set to False, raw HTML is replaced by a placeholder comment and
        potentially dangerous URLs are replaced by an empty string.
    smart: bool, default: False
        Render smart punctuation.
        This is roughly equivalent to the `smartquotes` and `replacements` typographic components
        in [`markdown-it`](https://markdown-it-py.readthedocs.io/en/latest/using.html#typographic-components),
        e.g., converting basic quote marks to their opening and closing variants, and `--` and `---`
        to en-dash `–` and em-dash `—`, respectively.
    normalize: bool, default: False
        Consolidate adjacent text nodes.
    hard_breaks: bool, default: False
        Render line breaks within paragraphs as `<br>` tags.
    no_breaks: bool, default: False
        Render soft line breaks as spaces.
    source_pos: bool, default: False
        Add attribute `data-sourcepos` to HTML tags
        indicating the corresponding line/column ranges in the input.
    footnotes: bool, default: False
        Parse footnotes.
    validate_utf8: bool, default: False
        Validate UTF-8 in the input before parsing,
        replacing illegal sequences with the replacement character `U+FFFD`.
    github_pre_lang: bool, default: True
        Use GitHub style for indicating the language of code blocks.
        If True (default), the code block's language defined in its info string will be used
        as the value of the `lang` attribute of the `<pre>` element
        (e.g., `<pre lang="python"><code>...</code></pre>`),
        otherwise it will be used as the value of the `class` attribute of the `<code>` element
        according to [highlight.js](https://highlightjs.org/) style
        (e.g., `<pre><code class="language-python">...</code></pre>`).
    liberal_html_tag: bool, default: False
        Be liberal in interpreting inline HTML tags.
    strikethrough_double_tilde: bool, default: False
        Only parse strikethroughs if surrounded by exactly 2 tildes.
        Gives some compatibility with redcarpet.
    table_prefer_style_attributes: bool, default: False
        Use style attributes to align table cells instead of align attributes.
    highlight_code : bool, default: True
        Apply syntax highlighting to code blocks using the [`Pygments`](https://pygments.org/) library.
        This exactly replicates the rendering used in PyPI.
        However, notice that `readme_renderer` uses a naive RegEx to detect `<pre>` HTML elements.
        Thus, this may not work on custom-written `<pre>` elements
        (i.e., those not generated from Markdown by CMarkGFM in the previous step).
    sanitize : bool, default: True
        Sanitize the HTML output using the [`nh3`](https://nh3.readthedocs.io/en/latest/)
        library to remove potentially dangerous content.
        PyPI uses this to prevent XSS attacks by allowing only a
        [subset of HTML tags](https://github.com/pypa/readme_renderer/blob/1d0497c37a6033d791c74e800590dcd0d34f6e08/readme_renderer/clean.py#L20-L31)
        and [attributes](https://github.com/pypa/readme_renderer/blob/1d0497c37a6033d791c74e800590dcd0d34f6e08/readme_renderer/clean.py#L33-L65).

    Notes
    -----
    - [`twine check`](https://twine.readthedocs.io/en/stable/#twine-check) only works for
      reStructuredText (reST) READMEs; it always passes for Markdown content
      (cf. [`twine.commands.check._RENDERERS`](https://github.com/pypa/twine/blob/4f7cd66fa1ceba7f8de5230d3d4ebea0787f17e5/twine/commands/check.py#L32-L37))
      and thus cannot be used to validate Markdown.

    References
    ----------
    - [`cmarkgfm.cmark` module](https://github.com/theacodes/cmarkgfm/blob/66b131cee950ad30cad9dfbf7f2360270ed105b8/src/cmarkgfm/cmark.py)
    - [`readme_renderer.markdown` module](https://github.com/pypa/readme_renderer/blob/1d0497c37a6033d791c74e800590dcd0d34f6e08/readme_renderer/markdown.py)
    """
    options = 0
    for arg, cmark_arg in (
        (unsafe, _gfm_pypi.Options.CMARK_OPT_UNSAFE),
        (smart, _gfm_pypi.Options.CMARK_OPT_SMART),
        (normalize, _gfm_pypi.Options.CMARK_OPT_NORMALIZE),
        (hard_breaks, _gfm_pypi.Options.CMARK_OPT_HARDBREAKS),
        (no_breaks, _gfm_pypi.Options.CMARK_OPT_NOBREAKS),
        (source_pos, _gfm_pypi.Options.CMARK_OPT_SOURCEPOS),
        (footnotes, _gfm_pypi.Options.CMARK_OPT_FOOTNOTES),
        (validate_utf8, _gfm_pypi.Options.CMARK_OPT_VALIDATE_UTF8),
        (github_pre_lang, _gfm_pypi.Options.CMARK_OPT_GITHUB_PRE_LANG),
        (liberal_html_tag, _gfm_pypi.Options.CMARK_OPT_LIBERAL_HTML_TAG),
        (strikethrough_double_tilde, _gfm_pypi.Options.CMARK_OPT_STRIKETHROUGH_DOUBLE_TILDE),
        (table_prefer_style_attributes, _gfm_pypi.Options.CMARK_OPT_TABLE_PREFER_STYLE_ATTRIBUTES),
    ):
        if arg:
            options |= cmark_arg
    if isinstance(source, str):
        return _gfm_pypi.markdown_to_html_with_extensions(
            text=source,
            options=options,
            extensions=extensions,
        )
    return {
        key: _gfm_pypi.markdown_to_html_with_extensions(
            text=source,
            options=options,
            extensions=extensions,
        ) for key, source in source.items()
    }


def readme_renderer(
    source: str | dict[str, str],
):
    if isinstance(source, str):
        return _readme_renderer_md.render(source)
    return {key: _readme_renderer_md.render(value) for key, value in source.items()}
