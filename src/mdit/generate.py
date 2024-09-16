from typing import Literal, get_type_hints as _get_type_hints
from types import FunctionType as _FunctionType
import copy

import htmp as _htmp

from mdit import element as _elem
import mdit as _mdit


class DocumentGenerator:

    def __init__(self):
        self.nested_keys = {
            "admonition": ["title", "content"],
            "attribute": ["content"],
            "block_quote": ["content", "cite"],
            "card": ["header", "body", "footer"],
            "code_block": ["content"],
            "directive": ["args", "content"],
            "field_list_item": ["title", "description"],
            "field_list": ["content"],
            "heading": ["content"],
            "html": ["content"],
            "paragraph": ["content"],
            "tab_item": ["title", "content"],
            "tab_set": ["content"],
            "target_anchor": ["content"],
            "ordered_list": ["content"],
            "unordered_list": ["content"],
        }
        return

    def generate(self, config: dict | list, base: bool = True):
        config = copy.deepcopy(config)
        if isinstance(config, list):
            return self.generate_container(config)
        if base and "class" in config:
            return self.generate_template(config)
        heading = self.elem_heading(config["heading"]) if "heading" in config else None
        body = self.generate_container(config["body"]) if "body" in config else None
        sections = []
        for section in config.get("section", []):
            sections.append(self.generate(section, base=False))
        footer = self.generate_container(config["footer"]) if "footer" in config else None
        frontmatter = self.elem_frontmatter(config["frontmatter"]) if "frontmatter" in config else None
        return _mdit.document(
            heading=heading,
            body=body,
            section=sections,
            footer=footer,
            frontmatter=frontmatter,
            frontmatter_conditions=config.get("frontmatter_conditions"),
            separate_sections=config.get("separate_sections", False),
            toctree_args=config.get("toctree_args"),
            toctree_dirhtml=config.get("toctree_dirhtml", True),
            target_default=config.get("default_output_target", "sphinx"),
        )

    def generate_template(self, config: dict):
        template_name = config.pop("class")
        generator = self._get_elem_generator(_mdit.template, template_name, "template")
        return generator(**config)


    def generate_container(self, container: str | list[str | dict, list[str | dict]]):
        if isinstance(container, str):
            return container
        elements = []
        for block_element in container:
            if isinstance(block_element, str):
                elements.append(block_element)
            elif isinstance(block_element, dict):
                conditions = block_element.pop("conditions", None)
                elements.append((self.generate_element(block_element), conditions))
            else:
                inline_elements = []
                for inline_element in block_element:
                    if isinstance(inline_element, str):
                        inline_elements.append(inline_element)
                    else:
                        conditions = inline_element.pop("conditions", None)
                        inline_elements.append(
                            (self.generate_element(inline_element), conditions)
                        )
                inline_container = _mdit.container(*inline_elements, content_separator="")
                elements.append(inline_container)
        return _mdit.container(*elements, content_separator="\n\n")

    def generate_element(self, element: dict):
        elem_class = element.pop("class")
        if elem_class.startswith("html."):
            self.generate_html_element(elem_id=elem_class.removeprefix("html."), element=element)
        return self.generate_md_element(elem_id=elem_class, element=element)

    def generate_html_element(self, elem_id: str, element: dict):
        generator = self._get_elem_generator(_htmp.element, elem_id, "HTML")
        if _htmp.spec.element_is_void(elem_id):
            return generator(element.get("attrs", None))
        content = element.get("content")
        if not content:
            return generator(None, element.get("attrs", None))
        content = self.generate_container(content)
        return _elem.html(
            content=content,
            tag=elem_id,
            attrs=element.get("attrs", None),
            inline=element.get("inline", False),
        )

    def generate_md_element(self, elem_id: str, element: dict):
        generator = self._get_elem_generator(_elem, elem_id, "MD")
        if elem_id in self.nested_keys:
            return self.elem_nested(generator, element, self.nested_keys[elem_id])
        return generator(**element)

    def elem_nested(self, generator, config: dict, nested_keys: list[str]):
        for key in nested_keys:
            config[key] = self.generate_container(config.pop(key)) if config.get(key) else None
        return generator(**config)

    def elem_admonition(self, config: dict):
        title = self.generate_container(config.pop("title"))
        content = self.generate_container(config.pop("content"))
        return _elem.admonition(content, title=title, **config)

    def elem_attribute(self, config: dict):
        content = self.generate_container(config.pop("content"))
        return _elem.attribute(content=content, **config)

    def elem_heading(self, config: str | list | dict):
        if isinstance(config, str):
            content = config
            config = {}
        elif isinstance(config, dict):
            content = self.generate_container(config.pop("content"))
        else:
            content = self.generate_container(config)
            config = {}
        return _elem.heading(content, level=1, **config)

    @staticmethod
    def _get_elem_generator(module, elem_id, class_name):
        error_msg = f"Element '{elem_id}' is not a valid {class_name} element."
        try:
            func = getattr(module, elem_id)
        except AttributeError:
            raise AttributeError(error_msg)
        if not isinstance(func, _FunctionType):
            raise AttributeError(error_msg)
        return func
