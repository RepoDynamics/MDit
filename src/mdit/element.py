from __future__ import annotations
from typing import TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from typing import Literal


class Element:
    def __init__(
        self,
        block: bool,
        leaf: bool = True,
        contents: _ElementContentInputType = None,
        newlines_before: int | None = None,
        newlines_after: int | None = None,
    ):
        super().__init__(contents=contents)
        self._block = block
        self._leaf = leaf
        self.newlines_before = newlines_before
        self.newlines_after = newlines_after
        return

    def __str__(self):
        if not self._block:
            if any(not isinstance(elem, str) for elem in self._content.values()):
                raise ValueError("Inline elements must have string content.")
        elif self._leaf:
            if any(isinstance(elem, Element) and elem.is_block for elem in self._content.values()):
                raise ValueError("Leaf block elements cannot contain block content.")
        content = "".join(str(elem) for elem in self._content.values())
        md = self._md.replace("${{content}}", content)
        newlines_before, newlines_after = [
            newlines_count if isinstance(newlines_count, int) else (1 if self._block else 0)
            for newlines_count in (self.newlines_before, self.newlines_after)
        ]
        return f"{newlines_before * '\n'}{md}{newlines_after * '\n'}"

    @property
    def _md(self) -> str:
        return "${{content}}"

    @property
    def is_block(self) -> bool:
        return self._block

    @property
    def is_leaf(self) -> bool:
        return self._leaf

    def display(self, ipython: bool = True, as_md: bool = True) -> None:
        """Display the element in an IPython notebook."""
        super().display(ipython=ipython, as_md=as_md)
        return


class ThematicBreak(Element):
    def __init__(self, char: Literal["-", "_", "*"] = "-"):
        super().__init__(block=True)
        self.char = char
        return

    @property
    def char(self):
        return self._char

    @char.setter
    def char(self, value: _Literal["-", "_", "*"]):
        if value not in ("-", "_", "*"):
            raise ValueError("Invalid thematic break character.")
        self._char = value
        return

    @property
    def _md(self) -> str:
        return self.char * 3


class ATXHeading(Element):
    def __init__(self, level: _Literal[1, 2, 3, 4, 5, 6], contents: _ElementContentInputType = ""):
        super().__init__(block=True, leaf=True, contents=contents)
        self._level = level
        return

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value: _Literal[1, 2, 3, 4, 5, 6]):
        if value not in (1, 2, 3, 4, 5, 6):
            raise ValueError("Invalid heading level.")
        self._level = value
        return

    @property
    def _md(self) -> str:
        return f"{'#' * self.level} ${{content}}"


class FieldListElement(Element):
    def __init__(self, name: _ElementContentType, body: _ElementContentInputType = "", indent_size: int = 4):
        super().__init__(block=True, leaf=False, contents=body)
        self.name = name
        self.indent_size = indent_size
        return

    @property
    def _md(self) -> str:
        body = "".join(str(elem) for elem in self._content.values())
        first_line, *lines = body.strip().split("\n")
        body = "\n".join([first_line] + [f"{' ' * self.indent_size}{line}" for line in lines])
        return f":{self.name}: {body}".strip()


class FieldList(Element):
    def __init__(self, elements: list[FieldListElement], indent_size: int = 4):
        super().__init__(block=True, leaf=False)
        self.indent_size = indent_size
        self.elements = elements
        return

    @property
    def _md(self) -> str:
        elements_md = []
        for elem in self.elements:
            indent_orig = elem.indent_size
            elem.indent_size = self.indent_size
            elements_md.append(elem._md)
            elem.indent_size = indent_orig
        return "\n".join(elements_md)


class HTMLBlock(Element):

    def __init__(self, contents: _ElementContentInputType = None):
        super().__init__(block=True, leaf=True, contents=contents, newlines_after=2)
        return

    @property
    def _md(self) -> str:
        return "${{content}}"


class CodeFence(Element):

    def __init__(
        self,
        contents: _ElementContentInputType = None,
        info: _Stringable = "",
        fence: _Literal["`", "~", ":"] = "`",
    ):
        super().__init__(block=True, leaf=False, contents=contents)
        self._info = info
        self.fence = fence
        return

    @property
    def info(self) -> _Stringable:
        return self._info

    @info.setter
    def info(self, value: _Stringable):
        if "\n" in str(value):
            raise ValueError("Info string cannot contain newlines.")
        self._info = value
        return

    @property
    def fence(self):
        return self._fence

    @fence.setter
    def fence(self, value: _Literal["`", "~", ":"]):
        if value not in ("`", "~", ":"):
            raise ValueError("Invalid code fence character.")
        self._fence = value
        return

    @property
    def _md(self) -> str:
        return f"{self._start_line}\n${{content}}\n{self._end_line}"

    @property
    def fence_count(self):
        return max(
            [child.fence_count for child in self.content.values() if isinstance(child, CodeFence)],
            default=3
        )

    @property
    def _start_line(self) -> str:
        return f"{self.fence * self.fence_count}{self.info}"

    @property
    def _end_line(self) -> str:
        return self.fence * self.fence_count


class Directive(CodeFence):
    def __init__(
        self,
        name: _Stringable,
        contents: _ElementContentInputType = None,
        arg: _Stringable = "",
        options: dict[_Stringable, _Stringable] | None = None,
        fence: _Literal["`", "~", ":"] = "`",
    ):
        super().__init__(contents=contents, fence=fence)
        self.name = name
        self.arg = arg
        self.options = options or {}
        return

    @property
    def info(self) -> str:
        return f"{{{self.name}}} {self.arg}"

    @property
    def _md(self) -> str:
        options = []
        for key, value in self.options.items():
            val_str = str(value) if value is not None else ""
            if "\n" in val_str:
                val_content = "\n".join(f"{' ' * 4}{line}" for line in val_str.split("\n"))
                val_str = f"|\n{val_content}"
            options.append(f":{key}: {val_str}")
        options = "\n".join(options)
        options_section = f"{options}\n\n" if options else ""
        return f"{self._start_line}\n{options_section}${{content}}\n{self._end_line}"


def thematic_break(char: _Literal["-", "_", "*"] = "-") -> ThematicBreak:
    """Create a [thematic break](https://github.github.com/gfm/#thematic-break).

    Parameters
    ----------
    char : {'*', '_', '-'}, default: '-'
        Thematic break character.
    """
    return ThematicBreak(char=char)


def heading(level: _Literal[1, 2, 3, 4, 5, 6], content: _ElementContentInputType = "") -> ATXHeading:
    """Create an ATX heading.

    Parameters
    ----------
    level : {1, 2, 3, 4, 5, 6}
        Heading level.
    content : str
        Heading content.
    """
    return ATXHeading(level=level, contents=content)


def field_list_element(
    name: _ElementContentType,
    body: _ElementContentInputType = "",
    indent_size: int = 4,
) -> FieldListElement:
    """Create a field list element.

    Parameters
    ----------
    name : ElementContentType
        Field name.
    body : ElementContentInputType, optional
        Field body.
    indent_size : int, default: 4
        Indent size.
    """
    return FieldListElement(name=name, body=body, indent_size=indent_size)


def field_list(
    elements: list[FieldListElement | tuple[_ElementContentType, _ElementContentInputType]],
    indent_size: int = 4,
) -> FieldList:
    """Create a field list.

    Parameters
    ----------
    elements : list[FieldListElement]
        Field list elements.
    indent_size : int, default: 4
        Indent size.
    """
    elements = [
        elem if isinstance(elem, FieldListElement) else field_list_element(name=elem[0], body=elem[1])
        for elem in elements
    ]
    return FieldList(elements=elements, indent_size=indent_size)


def html_block(content: _ElementContentInputType = None) -> HTMLBlock:
    """Create an [HTML block](https://github.github.com/gfm/#html-block).

    Parameters
    ----------
    content : ElementContentInputType, optional
        HTML content.
    """
    return HTMLBlock(contents=content)

def code_fence(
    content: _ElementContentInputType = None,
    info: _Stringable = "",
    fence: _Literal["`", "~", ":"] = "`",
) -> CodeFence:
    """Create a [fenced code block](https://github.github.com/gfm/#fenced-code-block).

    Parameters
    ----------
    content : ElementContentInputType, optional
        Code block content.
    info : Stringable, optional
        Code block [info string](https://github.github.com/gfm/#info-string).
    fence: {'`', '~', ':'}, default: '`'
        Fence character.
    """
    return CodeFence(contents=content, info=info, fence=fence)


def directive(
    name: _Stringable,
    content: _ElementContentInputType = None,
    arg: _Stringable = "",
    options: dict[_Stringable, _Stringable] | None = None,
    fence: _Literal["`", "~", ":"] = "`",
) -> Directive:
    """Create a directive.

    Parameters
    ----------
    name : Stringable
        Directive name.
    content : ElementContentInputType, optional
        Directive content.
    arg : Stringable, optional
        Directive argument.
    options : dict[Stringable, Stringable], optional
        Directive options.
    fence: {'`', '~', ':'}, default: '`'
        Fence character.
    """
    return Directive(name=name, contents=content, arg=arg, options=options, fence=fence)


def admonition(
    title: _ElementContentType,
    content: _ElementContentInputType,
    class_: str | list[str] | None = None,
    name: _Stringable | None = None,
    fence: _Literal["`", "~", ":"] = "`",
) -> Directive:
    """Create a [MyST admonition](https://myst-parser.readthedocs.io/en/latest/syntax/admonitions.html).

    Parameters
    ----------
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
    options = process_directive_options({"class": class_, "name": name})
    return Directive(name="admonition", contents=content, arg=title, options=options, fence=fence)


def code_block(
    language: str | None,
    content: _ElementContentType,
    caption: _ElementContentType | None = None,
    class_: str | list[str] | None = None,
    name: _Stringable | None = None,
    lineno_start: int | None = None,
    emphasize_lines: list[int] | None = None,
    force: bool = False,
    fence: _Literal["`", "~", ":"] = "`",
):
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
    options = process_directive_options(
        {k: v for k, v in locals() if k not in ("language", "content", "fence")}
    )
    return Directive(name="code-block", contents=content, arg=language, options=options, fence=fence)


def tab_item(
    title: _Stringable,
    content: _ElementContentInputType,
    selected: bool = False,
    name: _Stringable | None = None,
    sync: _Stringable | None = None,
    class_container: str | list[str] | None = None,
    class_label: str | list[str] | None = None,
    class_content: str | list[str] | None = None,
    fence: _Literal["`", "~", ":"] = "`",
) -> Directive:
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
    class_container : str | list[str], optional
        CSS class names to add to the container element. These must conform to the
        [identifier normalization rules](https://docutils.sourceforge.io/docs/ref/rst/directives.html#identifier-normalization).
    class_label : str | list[str], optional
        CSS class names to add to the label element. These must conform to the
        [identifier normalization rules](https://docutils.sourceforge.io/docs/ref/rst/directives.html#identifier-normalization).
    class_content : str | list[str], optional
        CSS class names to add to the content element. These must conform to the
        [identifier normalization rules](https://docutils.sourceforge.io/docs/ref/rst/directives.html#identifier-normalization).
    fence: {'`', '~', ':'}, default: '`'
        Fence character.
    """
    options = process_directive_options(
        {k: v for k, v in locals() if k not in ("title", "content", "fence")}
    )
    return Directive(name="tab-item", contents=content, arg=title, options=options, fence=fence)


def tab_set(
    content: list[Directive],
    class_: list[str] | None = None,
    sync_group: _Stringable | None = None,
    fence: _Literal["`", "~", ":"] = "`",
) -> Directive:
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
    options = process_directive_options(
        {k: v for k, v in locals() if k not in ("content", "fence")}
    )
    return Directive(name="tab-set", contents=content, options=options, fence=fence)


def card(
    header_content: _ElementContentInputType = None,
    body_content: _ElementContentInputType = None,
    footer_content: _ElementContentInputType = None,
    body_title: _Stringable = "",
    width: _Literal["auto"] | int | None = None,
    margin: _Literal["auto", 0, 1, 2, 3, 4, 5] | tuple[_Literal["auto", 0, 1, 2, 3, 4, 5], ...] | None = None,
    text_align: _Literal["left", "center", "right", "justify"] | None = None,
    img_background: _Stringable | None = None,
    img_top: _Stringable | None = None,
    img_bottom: _Stringable | None = None,
    img_alt: _Stringable | None = None,
    link: _Stringable | None = None,
    link_type: _Literal["url", "ref", "doc", "any"] | None = None,
    link_alt: _Stringable | None = None,
    shadow: _Literal["sm", "md", "lg", "none"] | None = None,
    class_card: list[str] | None = None,
    class_header: list[str] | None = None,
    class_body: list[str] | None = None,
    class_footer: list[str] | None = None,
    class_title: list[str] | None = None,
    class_img_top: list[str] | None = None,
    class_img_bottom: list[str] | None = None,
    fence: _Literal["`", "~", ":"] = "`",
) -> Directive:

    def process_content(content, key_prefix: str):
        if isinstance(content, (list, tuple)):
            return {f"{key_prefix}_{idx}": elem for idx, elem in enumerate(content)}
        if not isinstance(content, dict):
            return {key_prefix: content}
        return content

    options = process_directive_options(
        {
            k: v for k, v in locals() if k not in (
                "header_content", "body_content", "footer_content", "body_title", "fence"
            )
        }
    )
    content = {}
    if header_content:
        for header_id, header in process_content(header_content, "header"):
            content[header_id] = header
        content["header_body_separator"] = "^^^"
    if body_content:
        for body_id, body in process_content(body_content, "body"):
            content[body_id] = body
    if footer_content:
        content["body_footer_separator"] = "+++"
        for footer_id, footer in process_content(footer_content, "footer"):
            content[footer_id] = footer
    return Directive(name="card", contents=content, arg=body_title, options=options, fence=fence)


def process_directive_options(options: dict) -> dict:
    final_options = {}
    for key, val in options.items():
        if val is None or val is False:
            continue
        if isinstance(val, (list, tuple)):
            val = " ".join([str(e) for e in val])
        elif isinstance(val, bool):
            val = ""
        key_name = str(key).removesuffix("_").replace("_", "-")
        final_options[key_name] = val
    return final_options

