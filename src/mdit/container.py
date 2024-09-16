from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING, NamedTuple as _NamedTuple

import htmp as _htmp
import rich
import rich.text
import rich.markdown

from mdit.protocol import MDITRenderable as _MDCode
from mdit.renderable import Renderable as _Renderable

if _TYPE_CHECKING:
    from rich.console import RenderableType
    from mdit.protocol import ContainerContentType, ContainerContentConditionType, ContainerContentInputType, TargetConfigs, Stringable, MDTargetConfig, RichTargetConfig


class ContainerContent(_NamedTuple):
    content: ContainerContentType
    conditions: list[str]


class Container:

    def __init__(
        self,
        data: dict[str | int, ContainerContent] | None = None,
        *args,
        **kwargs
    ):
        self._data = data or {}
        super().__init__(*args, **kwargs)
        return

    def append(
        self,
        content: ContainerContentType,
        conditions: ContainerContentConditionType = None,
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

    def extend(self, *unlabeled_contents: ContainerContentInputType, **labeled_contents: ContainerContentInputType) -> list[str | int]:

        def resolve_value(input_values):
            if not input_values:
                return
            if isinstance(input_values, list):
                for input_value in input_values:
                    yield from resolve_value(input_value)
            elif isinstance(input_values, tuple):
                val = input_values[0]
                cond = input_values[1] if len(input_values) > 1 else None
                key = input_values[2] if len(input_values) > 2 else None
                yield val, cond, key
            elif isinstance(input_values, dict):
                for k, v in input_values.items():
                    key = k
                    if isinstance(v, (list, tuple)):
                        val = v[0]
                        cond = v[1] if len(v) > 1 else None
                    else:
                        val = v
                        cond = None
                    yield val, cond, key
            else:
                yield input_values, None, None

        added_keys = []
        if unlabeled_contents:
            first_available_key = max(
                (key for key in self._data.keys() if isinstance(key, int)), default=-1
            ) + 1
            for idx, value in enumerate(unlabeled_contents):
                for content, conditions, key in resolve_value(value):
                    added_keys.append(self.append(content, conditions, key or first_available_key + idx))
        if labeled_contents:
            for key, value in labeled_contents.items():
                for content, conditions, sub_key in resolve_value(value):
                    final_key = key if sub_key is None else f"{key}.{sub_key}"
                    added_keys.append(self.append(content, conditions, final_key))
        return added_keys

    def elements(
        self,
        target: TargetConfigs | None = None,
        filters: str | list[str] | None = None,
        source: bool = False,
    ) -> list:
        elements = []
        if isinstance(filters, str):
            filters = [filters]
        for content, conditions in self.values():
            if not filters or not conditions or any(filter in conditions for filter in filters):
                if not source:
                    elements.append(content)
                elif isinstance(content, _MDCode):
                    elements.append(content.source(target=target, filters=filters))
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

    def __len__(self):
        return len(self._data)


class MDContainer(Container, _Renderable):
    # Multiple inheritance: https://stackoverflow.com/questions/9575409/calling-parent-class-init-with-multiple-inheritance-whats-the-right-way
    def __init__(
        self,
        content: dict[str | int, ContainerContent] | None = None,
        content_separator: str = "\n\n",
        html_container: Stringable | None = None,
        html_container_attrs: dict | None = None,
        html_container_conditions: list[str] | None = None,
        target_configs: TargetConfigs = None,
        target_default: str = "sphinx"
    ):
        super().__init__(
            data=content,
            target_configs=target_configs,
            target_default=target_default
        )
        self.content_separator = content_separator
        self.html_container = html_container
        self.html_container_attrs = html_container_attrs or {}
        self.html_container_conditions = html_container_conditions or []
        return

    @property
    def code_fence_count(self) -> int:
        return max(
            (
                content.code_fence_count if isinstance(content, _MDCode)
                else self._count_code_fence(str(content))
                for content, _ in self._data.values()
            ),
            default=0,
        )

    def _source_rich(self, target: RichTargetConfig, filters: str | list[str] | None = None) -> RenderableType:
        block_container = "\n" in self.content_separator
        elements = self.elements(target=target, filters=filters, source=True)
        if not elements:
            return ""
        if block_container:
            group = [
                rich.markdown.Markdown(element) if isinstance(element, str) else element
                for element in elements
            ]
            return rich.console.Group(*group) if len(group) > 1 else group[0]
        text = rich.text.Text()
        for element in elements[:-1]:
            text.append(element)
            text.append(self.content_separator)
        text.append(elements[-1])
        return text

    def _source_md(self, target: MDTargetConfig, filters: str | list[str] | None = None) -> str:
        elements = self.elements(target=target, filters=filters, source=True)
        elements_str = self.content_separator.join(elements)
        if self.html_container and self.html_container_attrs and (
            not filters
            or not self.html_container_conditions
            or any(filter in self.html_container_conditions for filter in filters)
        ):
            container_func = getattr(_htmp.element, str(self.html_container))
            return container_func(_htmp.elementor.markdown(elements_str), self.html_container_attrs).source(
                indent=-1)
        return elements_str

    def __str__(self) -> str:
        return self.source()
