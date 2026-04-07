"""SecLists auto-detection helpers.

This module provides a lightweight public interface for finding a local
SecLists installation and resolving per-module wordlist paths.  It
delegates to the richer ``vortex.wordlists`` implementation so that
detection logic is kept in a single place.
"""

import os

from vortex.wordlists import (
    SecListsProvider,
    _SECLISTS_FILES,
    get_cached_wordlist_path,
    get_local_seclists_archive,
    get_local_seclists_base,
    get_wordlist_for_size,
)

# Re-export the singleton provider for convenience
_provider = SecListsProvider()


def find_seclists():
    """Return the cached or installed SecLists base directory path.

    Searches (in order):
    1. Full local install at ``vortex/wordlists/SecLists``.
    2. A cached copy inside ``vortex/wordlists``.
    3. The ``SECLISTS_PATH`` environment variable.
    4. ``/usr/share/seclists/``
    5. ``/usr/share/SecLists/``
    6. ``/opt/seclists/``
    7. ``~/SecLists/``
    """
    local = get_local_seclists_base()
    if local:
        return local

    archive = get_local_seclists_archive()
    if archive:
        return archive

    for module, sizes in _SECLISTS_FILES.items():
        for size in sizes:
            cached = get_cached_wordlist_path(module, size)
            if cached:
                return os.path.dirname(cached)
    return _provider.base_path


def get_seclists_wordlist(category, size="small"):
    """Return the absolute path to a SecLists wordlist for *category*.

    Parameters
    ----------
    category : str
        One of ``'subdomains'``, ``'directories'``, or ``'parameters'``.
    size : str
        One of ``'small'`` (default), ``'medium'``, or ``'large'``.

    Returns
    -------
    str or None
        Absolute path to the cached or installed wordlist file, or ``None``
        when SecLists is not installed and no cached copy is available.
    """
    cached = get_cached_wordlist_path(category, size)
    if cached:
        return cached
    return _provider.get_path(category, size)


__all__ = [
    "find_seclists",
    "get_seclists_wordlist",
    "get_wordlist_for_size",
    "_SECLISTS_FILES",
]
