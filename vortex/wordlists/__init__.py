import os
import shutil
import urllib.error
import urllib.request

WORDLIST_DIR = os.path.dirname(os.path.abspath(__file__))

_LOCAL_SECLISTS_PREFIX = 'seclists_'
_SECLISTS_RAW_BASE = 'https://raw.githubusercontent.com/danielmiessler/SecLists/master'

_BUNDLED_SUBDOMAINS = os.path.join(WORDLIST_DIR, 'subdomains.txt')
_BUNDLED_DIRECTORIES = os.path.join(WORDLIST_DIR, 'directories.txt')
_BUNDLED_PARAMETERS = os.path.join(WORDLIST_DIR, 'parameters.txt')

# SecLists relative paths for each size tier
_SECLISTS_FILES = {
    'subdomains': {
        'small':  'Discovery/DNS/subdomains-top1million-5000.txt',
        'medium': 'Discovery/DNS/subdomains-top1million-20000.txt',
        'large':  'Discovery/DNS/subdomains-top1million-110000.txt',
    },
    'directories': {
        'small':  'Discovery/Web-Content/common.txt',
        'medium': 'Discovery/Web-Content/raft-medium-directories.txt',
        'large':  'Discovery/Web-Content/directory-list-2.3-medium.txt',
    },
    'parameters': {
        'small':  'Discovery/Web-Content/burp-parameter-names.txt',
        'medium': 'Discovery/Web-Content/burp-parameter-names.txt',
        'large':  'Discovery/Web-Content/burp-parameter-names.txt',
    },
}

# Search order for SecLists installation paths.
# Both lowercase and capitalised variants are intentional for case-sensitive Linux filesystems.
_SECLISTS_SEARCH_PATHS = [
    '/usr/share/seclists',
    '/usr/share/SecLists',
    '/opt/seclists',
    os.path.expanduser('~/SecLists'),
]


def _local_seclists_filename(module, size):
    if module not in _SECLISTS_FILES:
        return None
    if size not in _SECLISTS_FILES[module]:
        return None
    return f"{_LOCAL_SECLISTS_PREFIX}{module}_{size}.txt"


def _local_seclists_url(module, size):
    relative = _SECLISTS_FILES.get(module, {}).get(size)
    if not relative:
        return None
    return f"{_SECLISTS_RAW_BASE}/{relative}"


def _download_to_path(url, destination, timeout=10):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            content = response.read()
    except (OSError, urllib.error.URLError, ValueError):
        return False

    if not content:
        return False

    with open(destination, 'wb') as handle:
        handle.write(content)
    return True


def get_cached_wordlist_path(module, size='small'):
    """Return a cached SecLists copy stored inside ``WORDLIST_DIR`` if present."""
    filename = _local_seclists_filename(module, size)
    if not filename:
        return None
    path = os.path.join(WORDLIST_DIR, filename)
    return path if os.path.isfile(path) else None


def is_cached_wordlist(path):
    """Return True when *path* points to a cached SecLists copy."""
    if not path:
        return False
    abs_path = os.path.abspath(path)
    return os.path.dirname(abs_path) == os.path.abspath(WORDLIST_DIR) and os.path.basename(abs_path).startswith(
        _LOCAL_SECLISTS_PREFIX
    )


def cache_seclists_wordlists(source_base=None, destination_dir=None, overwrite=False, download_missing=False):
    """Copy available SecLists wordlists into a destination directory.

    Parameters
    ----------
    source_base : str or None
        Base path of a SecLists installation. When omitted, the detected
        system installation is used.
    destination_dir : str or None
        Directory that should receive the cached files. Defaults to
        ``WORDLIST_DIR``.
    overwrite : bool
        Replace already-cached files when True.
    download_missing : bool
        Fetch missing files from the upstream SecLists repository when no local
        installation is available.

    Returns
    -------
    dict[str, str]
        Mapping of ``"module:size"`` to the cached file path for every file
        that was copied or already present.
    """
    source_base = source_base or _provider.base_path
    destination_dir = destination_dir or WORDLIST_DIR
    os.makedirs(destination_dir, exist_ok=True)
    if not source_base or not os.path.isdir(source_base):
        if not download_missing:
            return {}
        source_base = None

    cached = {}
    for module, sizes in _SECLISTS_FILES.items():
        for size, relative in sizes.items():
            filename = _local_seclists_filename(module, size)
            if not filename:
                continue

            destination = os.path.join(destination_dir, filename)
            if not overwrite and os.path.isfile(destination):
                cached[f'{module}:{size}'] = destination
                continue

            copied = False
            if source_base:
                source = os.path.join(source_base, relative)
                if os.path.isfile(source):
                    shutil.copy2(source, destination)
                    copied = True
            elif download_missing:
                url = _local_seclists_url(module, size)
                if url:
                    copied = _download_to_path(url, destination)

            if not copied and not os.path.isfile(destination):
                continue
            cached[f'{module}:{size}'] = destination

    return cached


class SecListsProvider:
    """Detects a local SecLists installation and resolves wordlist paths."""

    def __init__(self):
        self._base = self._detect()

    def _detect(self):
        """Return the SecLists base directory, or None if not found."""
        # Environment variable override takes highest priority
        env_path = os.environ.get('SECLISTS_PATH', '').strip()
        if env_path and os.path.isdir(env_path):
            return env_path

        for candidate in _SECLISTS_SEARCH_PATHS:
            if os.path.isdir(candidate):
                return candidate

        return None

    @property
    def available(self):
        """True when a SecLists installation was found."""
        return self._base is not None

    @property
    def base_path(self):
        """The detected SecLists base directory (may be None)."""
        return self._base

    def get_path(self, module, size='small'):
        """Return the absolute path to a SecLists wordlist, or None.

        Parameters
        ----------
        module : str
            One of ``'subdomains'``, ``'directories'``, ``'parameters'``.
        size : str
            One of ``'small'``, ``'medium'``, ``'large'``.
        """
        if not self.available:
            return None
        relative = _SECLISTS_FILES.get(module, {}).get(size)
        if not relative:
            return None
        full = os.path.join(self._base, relative)
        return full if os.path.isfile(full) else None


# Module-level singleton — evaluated once at import time
_provider = SecListsProvider()


def get_wordlist_for_size(module, size='small'):
    """Return the best wordlist path for *module* at the requested *size*.

    Tries a cached SecLists copy first, then a system SecLists install, then
    falls back to the bundled wordlist when neither is available.

    Parameters
    ----------
    module : str
        ``'subdomains'``, ``'directories'``, or ``'parameters'``.
    size : str
        ``'small'`` (default), ``'medium'``, or ``'large'``.

    Returns
    -------
    tuple[str, bool]
        ``(path, from_seclists)`` where *from_seclists* is True when the
        returned path comes from a cached or system SecLists source.
    """
    cached_path = get_cached_wordlist_path(module, size)
    if cached_path:
        return cached_path, True

    seclists_path = _provider.get_path(module, size)
    if seclists_path:
        return seclists_path, True

    bundled = {
        'subdomains': _BUNDLED_SUBDOMAINS,
        'directories': _BUNDLED_DIRECTORIES,
        'parameters': _BUNDLED_PARAMETERS,
    }
    return bundled.get(module, _BUNDLED_SUBDOMAINS), False


# Public defaults — point to SecLists (small) when available, else bundled
DEFAULT_SUBDOMAINS, _ = get_wordlist_for_size('subdomains', 'small')
DEFAULT_DIRECTORIES, _ = get_wordlist_for_size('directories', 'small')
DEFAULT_PARAMETERS, _ = get_wordlist_for_size('parameters', 'small')


def get_wordlist(name):
    """Get path to a wordlist by name (uses SecLists when available)."""
    mapping = {
        'subdomains': DEFAULT_SUBDOMAINS,
        'directories': DEFAULT_DIRECTORIES,
        'parameters': DEFAULT_PARAMETERS,
    }
    return mapping.get(name)
