"""Display HTML and Markdown content in web browser or IPython notebook."""
from __future__ import annotations as  _annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING

import webbrowser as _webbrowser
import tempfile as _tempfile
import time as _time

import rich as _rich
from IPython import display as _display

if _TYPE_CHECKING:
    from rich.console import Console


def browser(content: str) -> None:
    """Display HTML content in a web browser.

    This function writes the content to a temporary file and opens it in the system's default web browser.
    It then waits for 10 seconds (ensuring the browser has enough time to load the content)
    before deleting the temporary file.

    Parameters
    ----------
    content : str
        HTML content to display.
    """
    with _tempfile.NamedTemporaryFile('w', suffix='.html') as temp_file:
        temp_file.write(content)
        temp_file.flush()
        _webbrowser.open(f'file://{temp_file.name}')
        _time.sleep(11)
    return


def ipython(content: str, as_md: bool = True) -> None:
    """Display HTML or Markdown content in an IPython notebook.

    This function uses the `IPython.display` module to render the content
    in the current cell of an IPython notebook.

    Parameters
    ----------
    content : str
        HTML or Markdown content to display.
    as_md : bool, default: False
        If True, the function uses the `IPython.display.Markdown` renderer,
        otherwise (by default) it uses the `IPython.display.HTML` renderer
    """
    renderer = _display.Markdown if as_md else _display.HTML
    _display.display(renderer(content))
    return


def console(content, output: Console | None = None) -> None:
    writer = output or _rich
    writer.print(content)
    return
