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
    from mdit.protocol import ContainerContentType, ContainerContentInputType, ContainerContentSingleInputType, Stringable, TargetConfig, TargetConfigs, MDTargetConfig, RichTargetConfig, ContainerContentInputType


def generate(config: dict | list):
    return DocumentGenerator().generate(config)


def document(
    heading: element.Heading | MDContainer | ContainerContentInputType = None,
    body: MDContainer | ContainerContentInputType = None,
    section: Container | None = None,
    footer: MDContainer | ContainerContentInputType = None,
    frontmatter: dict | element.FrontMatter | None = None,
    frontmatter_conditions: list[str] | None = None,
    separate_sections: bool = False,
    current_section_key: list[str | int] | None = None,
    toctree_args: dict[str, str] | None = None,
    toctree_dirhtml: bool = True,
    target_configs_md: dict[str, MDTargetConfig | dict] | None = None,
    target_configs_rich: dict[str, RichTargetConfig | dict] | None = None,
    target_default: str = "sphinx",
    deep_section_generator: Callable[[Document], str] | None = None,
    content_separator_heading: str = "",
):
    # Process target configs
    target_configs = {}
    for key, config in (target_configs_md or {}).items():
        config_obj = config if isinstance(config, protocol.MDTargetConfig) else target.md.Config(**config)
        target_configs[key] = config_obj
    for key, config in (target_configs_rich or {}).items():
        config_obj = config if isinstance(config, protocol.RichTargetConfig) else target.rich.Config(**config)
        if key in target_configs:
            raise ValueError(f"Target config key '{key}' already exists.")
        target_configs[key] = config_obj
    # Process heading
    if heading and not isinstance(heading, element.Heading):
        heading = element.heading(
            content=heading,
            target_configs=target_configs,
            target_default=target_default,
        )
    body = to_block_container(body)
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
    footer = to_block_container(footer)
    if isinstance(frontmatter, dict):
        frontmatter = element.frontmatter(frontmatter)
    return Document(
        heading=heading,
        body=body,
        section=section,
        footer=footer,
        frontmatter=frontmatter,
        frontmatter_conditions=frontmatter_conditions,
        separate_sections=separate_sections,
        current_section_key=current_section_key,
        toctree_args=toctree_args,
        toctree_dirhtml=toctree_dirhtml,
        target_configs=target_configs,
        target_default=target_default,
        deep_section_generator=deep_section_generator,
    )

def block_container(
    *contents: ContainerContentInputType,
    html_container: Stringable | None = None,
    html_container_attrs: dict | None = None,
    html_container_conditions: list[str] | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> MDContainer:
    return container(
        *contents,
        content_separator="\n\n",
        html_container=html_container,
        html_container_attrs=html_container_attrs,
        html_container_conditions=html_container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )


def inline_container(
    *contents: ContainerContentInputType,
    separator: str = "",
    html_container: Stringable | None = None,
    html_container_attrs: dict | None = None,
    html_container_conditions: list[str] | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> MDContainer:
    return container(
        *contents,
        content_separator=separator,
        html_container=html_container,
        html_container_attrs=html_container_attrs,
        html_container_conditions=html_container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )


def container(
    *contents: ContainerContentInputType,
    content_separator: str,
    html_container: Stringable | None = None,
    html_container_attrs: dict | None = None,
    html_container_conditions: list[str] | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> MDContainer:
    container_ = MDContainer(
        content_separator=content_separator,
        html_container=html_container,
        html_container_attrs=html_container_attrs,
        html_container_conditions=html_container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )
    container_.extend(list(contents))
    return container_


def section_container(
    *unlabeled_contents: ContainerContentInputType,
    **labeled_contents: ContainerContentInputType,
) -> Container:
    container_ = Container()
    container_.extend(*unlabeled_contents, **labeled_contents)
    return container_


def to_block_container(
    content: MDContainer | ContainerContentInputType,
    separator: str = "\n\n",
    html_container: Stringable | None = None,
    html_container_attrs: dict | None = None,
    html_container_conditions: list[str] | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> MDContainer:
    return to_md_container(
        content,
        content_separator=separator,
        html_container=html_container,
        html_container_attrs=html_container_attrs,
        html_container_conditions=html_container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )


def to_inline_container(
    content: MDContainer | ContainerContentInputType,
    separator: str = "",
    html_container: Stringable | None = None,
    html_container_attrs: dict | None = None,
    html_container_conditions: list[str] | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> MDContainer:
    return to_md_container(
        content,
        content_separator=separator,
        html_container=html_container,
        html_container_attrs=html_container_attrs,
        html_container_conditions=html_container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )


def to_md_container(
    content: MDContainer | ContainerContentInputType,
    content_separator: str,
    html_container: Stringable | None = None,
    html_container_attrs: dict | None = None,
    html_container_conditions: list[str] | None = None,
    target_configs: TargetConfigs = None,
    target_default: str = "sphinx",
) -> MDContainer:
    if isinstance(content, MDContainer):
        return content
    container_ = MDContainer(
        content_separator=content_separator,
        html_container=html_container,
        html_container_attrs=html_container_attrs,
        html_container_conditions=html_container_conditions,
        target_configs=target_configs,
        target_default=target_default,
    )
    container_.extend(content)
    return container_
