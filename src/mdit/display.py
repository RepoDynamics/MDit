"""Display HTML and Markdown content in web browser or IPython notebook."""

import webbrowser as _webbrowser
import tempfile as _tempfile
import time as _time
from pathlib import Path as _Path

from IPython import display as _display


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
    with _tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as temp_file:
        temp_file.write(content)
        temp_file.flush()
        temp_filepath = temp_file.name
    _webbrowser.open(f'file://{temp_filepath}')
    _time.sleep(10)
    _Path(temp_filepath).unlink()
    return


def ipython(content: str, as_md: bool = False) -> None:
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
    if ipython:
        renderer = _display.Markdown if as_md else _display.HTML
        _display.display(renderer(content))
        return

    return
