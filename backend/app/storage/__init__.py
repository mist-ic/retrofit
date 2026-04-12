"""Storage package."""

from .artifacts import (
    get_run_config,
    load_html,
    load_screenshot,
    save_html,
    save_screenshot,
    store_run_config,
)

__all__ = [
    "store_run_config",
    "get_run_config",
    "save_screenshot",
    "load_screenshot",
    "save_html",
    "load_html",
]
