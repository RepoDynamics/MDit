from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING, NamedTuple as _NamedTuple
import re as _re

import htmp as _htmp

from mdit.protocol import MDCode as _MDCode
from mdit import display as _display


if _TYPE_CHECKING:
    from typing import Literal
    from mdit.protocol import ContainerInputType, ContainerContentType, ContainerContentType, TargetConfigType, Stringable


class ContainerContent(_NamedTuple):
    content: ContainerContentType
    conditions: list[str]


class Container:

    def __init__(self, data: dict[str | int, ContainerContent] | None = None):
        self._data = data or {}
        return

    def append(
        self,
        content,
        conditions: str | list[str] | None = None,
        key: str | int | None = None
    ) -> str | int:
        if not key:
            key = max((key for key in self._data.keys() if isinstance(key, int)), default=-1) + 1
        if key in self._data:
            raise ValueError("Key already exists in content.")
        if not conditions:
            conditions = []
        elif isinstance(conditions, str):
            conditions = [conditions]
        else:
            conditions = list(conditions)
        self._data[key] = ContainerContent(content=content, conditions=conditions)
        return key

    def extend(self, *unlabeled_contents, **labeled_contents) -> list[str | int]:

        def resolve_value(v):
            if isinstance(v, (list, tuple)):
                val = v[0]
                cond = v[1] if len(v) > 1 else None
                return val, cond
            return v, None

        added_keys = []
        if unlabeled_contents:
            first_available_key = max(
                (key for key in self._data.keys() if isinstance(key, int)), default=-1
            ) + 1
            for idx, value in enumerate(unlabeled_contents):
                content, conditions = resolve_value(value)
                added_keys.append(self.append(content, conditions, first_available_key + idx))
        if labeled_contents:
            for key, value in labeled_contents.items():
                content, conditions = resolve_value(value)
                added_keys.append(self.append(content, conditions, key))
        return added_keys

    def elements(
        self,
        target: TargetConfigType | None = None,
        filters: str | list[str] | None = None,
        string: bool = False,
    ) -> list:
        elements = []
        for content, conditions in self.values():
            if not filters or not conditions or any(filter in conditions for filter in filters):
                if not string:
                    elements.append(content)
                elif isinstance(content, _MDCode):
                    elements.append(content.str(target=target, filters=filters))
                else:
                    elements.append(str(content))
        return elements

    def get(self, key: str | int, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value
        return

    def __contains__(self, item):
        return item in self._data

    def __bool__(self):
        return bool(self._data)


class MDContainer(Container):

    _IS_MD_CODE = True

    def __init__(
        self,
        content: dict[str | int, ContainerContent] | None = None,
        content_separator: str = "\n\n",
        html_container: Stringable | None = None,
        html_container_attrs: dict | None = None,
        html_container_conditions: list[str] | None = None,
    ):
        super().__init__(content)
        self.content_separator = content_separator
        self.html_container = html_container
        self.html_container_attrs = html_container_attrs or {}
        self.html_container_conditions = html_container_conditions or []
        return

    def str(self, target: TargetConfigType | None = None, filters: str | list[str] | None = None) -> str:
        elements = self.elements(target=target, filters=filters, string=True)
        elements_str = self.content_separator.join(elements)
        if self.html_container and self.html_container_attrs and (
            not filters
            or not self.html_container_conditions
            or any(filter in self.html_container_conditions for filter in filters)
        ):
            container_func = getattr(_htmp.element, str(self.html_container))
            return container_func(_htmp.elementor.markdown(elements_str), self.html_container_attrs).str(indent=-1)
        return elements_str

    def display(self, target: TargetConfigType | None = None, filters: str | list[str] | None = None) -> None:
        """Display the element in an IPython notebook."""
        _display.ipython(self.str(target=target, filters=filters))
        return

    @property
    def code_fence_count(self) -> int:
        pattern = _re.compile(r'^\s{0, 3}(`{3,}|~{3,}|:{3,})', _re.MULTILINE)
        counts = []
        for content, _ in self._data.values():
            if isinstance(content, _MDCode):
                counts.append(content.code_fence_count)
            else:
                matches = pattern.findall(str(content))
                if matches:
                    counts.append(max(len(match) for match in matches))
        return max(counts, default=0)


    # def __str__(self):
    #     if not self._block:
    #         if any(not isinstance(elem, str) for elem in self._content.values()):
    #             raise ValueError("Inline elements must have string content.")
    #     elif self._leaf:
    #         if any(isinstance(elem, Element) and elem.is_block for elem in self._content.values()):
    #             raise ValueError("Leaf block elements cannot contain block content.")
    #     content = "".join(str(elem) for elem in self._content.values())
    #     md = self._md.replace("${{content}}", content)
    #     newlines_before, newlines_after = [
    #         newlines_count if isinstance(newlines_count, int) else (1 if self._block else 0)
    #         for newlines_count in (self.newlines_before, self.newlines_after)
    #     ]
    #     return f"{newlines_before * '\n'}{md}{newlines_after * '\n'}"

    def __str__(self) -> str:
        return self.str()


class BlockMDContainer(MDContainer):

    def __init__(self, content: dict[str | int, ContainerContent] | None = None):
        super().__init__(content, content_separator="\n\n")
        return


class InlineMDContainer(MDContainer):

    def __init__(self, content: dict[str | int, ContainerContent] | None = None):
        super().__init__(content, content_separator="")
        return