from typing import Type as _Type

from pyprotocol import Stringable as _Stringable


ContentType = _Stringable
ContentInputType = (
    dict[str | int, ContentType]
    | list[ContentType]
    | tuple[ContentType]
    | None
)


class Container(_Stringable):

    def __init__(self, *unlabeled_contents: ContentType, **labeled_contents: ContentType):
        self._data = {}
        self.add(*unlabeled_contents, **labeled_contents)
        return

    def add(self, *unlabeled_contents: ContentType, **labeled_contents: ContentType) -> list[int] | None:
        if labeled_contents:
            for key, value in labeled_contents.items():
                if key in self._data:
                    raise ValueError("Key already exists in content.")
                self._data[key] = value
        if unlabeled_contents:
            first_available_int_key = max(key for key in self._data.keys() if isinstance(key, int)) + 1
            for idx, elem in enumerate(unlabeled_contents):
                self._data[first_available_int_key + idx] = elem
            return list(range(first_available_int_key, first_available_int_key + len(unlabeled_contents)))
        return

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


def create(
    content: ContentInputType,
    container_class: _Type[Container] = Container
) -> Container:
    if not content:
        return container_class()
    if isinstance(content, dict):
        return container_class(**content)
    if isinstance(content, (list, tuple)):
        return container_class(*content)
    return container_class(content)
