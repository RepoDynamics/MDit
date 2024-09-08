"""Generate and process Markdown content.

References
----------
- [GitHub Flavored Markdown Spec](https://github.github.com/gfm/)
"""

from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING

from mdit.container import Container, MDContainer, BlockMDContainer, InlineMDContainer
from mdit.document import Document
from mdit import target, element, display, parse, protocol
__version__ = "XXX"

if _TYPE_CHECKING:
    from mdit.protocol import ContainerContentType, ContainerInputType, Stringable





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
    default_output_target: protocol.TargetConfigType | None = None,
):
    if heading and not isinstance(heading, element.Heading):
        heading = element.heading(1, heading)
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
        default_output_target=default_output_target,
    )


def container(
    content,
    content_seperator: str,
    html_container: Stringable | None = None,
    html_container_attrs: dict | None = None,
    html_container_conditions: list[str] | None = None,
) -> MDContainer:
    if isinstance(content, MDContainer):
        return content
    cont = MDContainer(
        content_separator=content_seperator,
        html_container=html_container,
        html_container_attrs=html_container_attrs,
        html_container_conditions=html_container_conditions,
    )
    if not content:
        return cont
    if isinstance(content, dict):
        cont.extend(**content)
    elif isinstance(content, (list, tuple)):
        cont.extend(*content)
    else:
        cont.append(content)
    return cont


def block_container(
    *unlabeled_contents: ContainerContentType,
    **labeled_contents: ContainerContentType,
) -> BlockMDContainer:
    container_ = BlockMDContainer()
    container_.extend(*unlabeled_contents, **labeled_contents)
    return container_


def inline_container(
    *unlabeled_contents: ContainerContentType,
    **labeled_contents: ContainerContentType,
) -> InlineMDContainer:
    container_ = InlineMDContainer()
    container_.extend(*unlabeled_contents, **labeled_contents)
    return container_


def section_container(
    *unlabeled_contents: ContainerContentType,
    **labeled_contents: ContainerContentType,
) -> Container:
    container_ = Container()
    container_.extend(*unlabeled_contents, **labeled_contents)
    return container_