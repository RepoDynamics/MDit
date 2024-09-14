"""Generate and process Markdown content.

References
----------
- [GitHub Flavored Markdown Spec](https://github.github.com/gfm/)
"""

from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING

from mdit import display
from mdit.container import Container, MDContainer
from mdit.document import Document
from mdit.generate import DocumentGenerator
from mdit import render, target, element, parse, protocol, template

if _TYPE_CHECKING:
    from typing import Callable
    from mdit.protocol import ContainerContentType, ContainerInputType, Stringable, TargetConfig, TargetConfigs


def generate(config: dict | list):
    return DocumentGenerator().generate(config)


def document(
    heading: element.Heading | ContainerInputType | None = None,
    body: ContainerInputType = None,
    section: Container | None = None,
    footer: ContainerInputType = None,
    frontmatter: dict | element.FrontMatter | None = None,
    frontmatter_conditions: list[str] | None = None,
    separate_sections: bool = False,
    toctree_args: dict[str, str] | None = None,
    toctree_dirhtml: bool = True,
    target_config_md: dict[str, TargetConfig | dict] | None = None,
    target_config_ansi: dict[str, ANSITargetConfig | dict] | None = None,
    default_output_target: str = "sphinx",
    deep_section_generator: Callable[[Document], str] | None = None,
):
    if heading and not isinstance(heading, element.Heading):
        heading = element.heading(content=heading, level=1)
    body = container(body, "\n\n")
    if isinstance(section, Container):
        pass
    elif not section:
        section = section_container()
    elif isinstance(section, dict):
        section = section_container(**section)
    elif isinstance(section, (list, tuple)):
        section = section_container(*section)
    else:
        section = section_container(section)
    footer = container(footer, "\n\n")
    if isinstance(frontmatter, dict):
        frontmatter = element.frontmatter(frontmatter)
    target_config = {}
    for key, config in (target_config_md or {}).items():
        config_obj = config if isinstance(config, protocol.TargetConfig) else target.custom(**config)
        target_config[key] = config_obj
    for key, config in (target_config_ansi or {}).items():
        config_obj = config if isinstance(config, protocol.ANSITargetConfig) else target.console(**config)
        if key in target_config:
            raise ValueError(f"Target config key '{key}' already exists.")
        target_config[key] = config_obj
    return Document(
        heading=heading,
        body=body,
        section=section,
        footer=footer,
        frontmatter=frontmatter,
        frontmatter_conditions=frontmatter_conditions,
        separate_sections=separate_sections,
        toctree_args=toctree_args,
        toctree_dirhtml=toctree_dirhtml,
        target_configs=target_config,
        target_default=default_output_target,
        deep_section_generator=deep_section_generator,
    )


def container(
    *contents: ContainerInputType | MDContainer,
    content_seperator: str = "\n\n",
    html_container: Stringable | None = None,
    html_container_attrs: dict | None = None,
    html_container_conditions: list[str] | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> MDContainer:
    if len(contents) == 1 and isinstance(contents[0], MDContainer):
        return contents[0]
    container_ = MDContainer(
        content_separator=content_seperator,
        html_container=html_container,
        html_container_attrs=html_container_attrs,
        html_container_conditions=html_container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )
    if not contents:
        return container_
    for content in contents:
        if isinstance(content, dict):
            container_.extend(**content)
        elif isinstance(content, (list, tuple)):
            container_.append(*content)
        else:
            container_.append(content)
    return container_


def section_container(
    *unlabeled_contents: ContainerContentType,
    **labeled_contents: ContainerContentType,
) -> Container:
    container_ = Container()
    container_.extend(*unlabeled_contents, **labeled_contents)
    return container_