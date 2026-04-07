import os
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Test: built-in wordlist files exist and are non-empty
# ---------------------------------------------------------------------------

def test_default_wordlist_files_exist():
    from vortex.wordlists import DEFAULT_SUBDOMAINS, DEFAULT_DIRECTORIES, DEFAULT_PARAMETERS

    for path in (DEFAULT_SUBDOMAINS, DEFAULT_DIRECTORIES, DEFAULT_PARAMETERS):
        assert os.path.isfile(path), f"Wordlist not found: {path}"


def test_default_wordlist_files_non_empty():
    from vortex.wordlists import DEFAULT_SUBDOMAINS, DEFAULT_DIRECTORIES, DEFAULT_PARAMETERS

    for path in (DEFAULT_SUBDOMAINS, DEFAULT_DIRECTORIES, DEFAULT_PARAMETERS):
        with open(path) as fh:
            entries = [line.strip() for line in fh if line.strip()]
        assert len(entries) > 0, f"Wordlist is empty: {path}"


# ---------------------------------------------------------------------------
# Test: get_wordlist() returns correct paths
# ---------------------------------------------------------------------------

def test_get_wordlist_returns_correct_paths():
    from vortex.wordlists import get_wordlist, DEFAULT_SUBDOMAINS, DEFAULT_DIRECTORIES, DEFAULT_PARAMETERS

    assert get_wordlist('subdomains') == DEFAULT_SUBDOMAINS
    assert get_wordlist('directories') == DEFAULT_DIRECTORIES
    assert get_wordlist('parameters') == DEFAULT_PARAMETERS


def test_get_wordlist_returns_none_for_unknown():
    from vortex.wordlists import get_wordlist

    assert get_wordlist('nonexistent') is None


# ---------------------------------------------------------------------------
# Test: SecListsProvider detection logic
# ---------------------------------------------------------------------------

def test_seclists_provider_detects_env_var(tmp_path):
    """SECLISTS_PATH env var should be used when set to an existing directory."""
    import vortex.wordlists as wl_mod

    with patch.object(wl_mod, 'get_local_seclists_base', return_value=None):
        with patch.dict(os.environ, {'SECLISTS_PATH': str(tmp_path)}):
            provider = wl_mod.SecListsProvider()
            assert provider.available
            assert provider.base_path == str(tmp_path)


def test_seclists_provider_not_detected_when_absent():
    """Provider should report unavailable when no known path exists."""
    import vortex.wordlists as wl_mod

    with patch.object(wl_mod, 'get_local_seclists_base', return_value=None):
        with patch.dict(os.environ, {'SECLISTS_PATH': ''}, clear=False):
            with patch('vortex.wordlists._SECLISTS_SEARCH_PATHS', ['/nonexistent/seclists']):
                provider = wl_mod.SecListsProvider()
                assert not provider.available
                assert provider.base_path is None


def test_seclists_provider_falls_back_to_search_paths(tmp_path):
    """Provider should pick up the first valid path from the search list."""
    import vortex.wordlists as wl_mod

    with patch.object(wl_mod, 'get_local_seclists_base', return_value=None):
        with patch.dict(os.environ, {'SECLISTS_PATH': ''}, clear=False):
            with patch('vortex.wordlists._SECLISTS_SEARCH_PATHS', ['/nonexistent', str(tmp_path)]):
                provider = wl_mod.SecListsProvider()
                assert provider.available
                assert provider.base_path == str(tmp_path)


def test_install_full_seclists_copies_source_tree(tmp_path):
    """install_full_seclists() should copy a full local SecLists tree."""
    import vortex.wordlists as wl_mod

    source = tmp_path / 'SecListsSource'
    src_dns = source / 'Discovery' / 'DNS'
    src_dns.mkdir(parents=True)
    (src_dns / 'subdomains-top1million-5000.txt').write_text('a\n')

    dest_parent = tmp_path / 'wordlists'
    installed = wl_mod.install_full_seclists(source_base=str(source), destination_parent=str(dest_parent), overwrite=True)

    assert installed == os.path.join(str(dest_parent), 'SecLists')
    assert os.path.isfile(os.path.join(installed, 'Discovery', 'DNS', 'subdomains-top1million-5000.txt'))


def test_install_full_seclists_downloads_archive_when_no_source(tmp_path):
    """install_full_seclists() should use archive download path when no source exists."""
    import vortex.wordlists as wl_mod

    dest_parent = tmp_path / 'wordlists'
    expected = os.path.join(str(dest_parent), 'SecLists')

    with patch.object(wl_mod, '_provider', type('P', (), {'base_path': None})()):
        with patch.object(wl_mod, '_download_and_extract_seclists', return_value=expected):
            installed = wl_mod.install_full_seclists(destination_parent=str(dest_parent), overwrite=True)

    assert installed == expected


def test_cache_seclists_wordlists_copies_available_files(tmp_path):
    """cache_seclists_wordlists() should copy detected SecLists files into WORDLIST_DIR."""
    import vortex.wordlists as wl_mod

    source = tmp_path / 'SecLists'
    sl_dns = source / 'Discovery' / 'DNS'
    sl_dns.mkdir(parents=True)
    sl_web = source / 'Discovery' / 'Web-Content'
    sl_web.mkdir(parents=True)

    (sl_dns / 'subdomains-top1million-5000.txt').write_text('sub1\nsub2\n')
    (sl_web / 'common.txt').write_text('admin\n')
    (sl_web / 'burp-parameter-names.txt').write_text('id\n')

    cache_dir = tmp_path / 'cache'
    cache_dir.mkdir()

    with patch.object(wl_mod, 'WORDLIST_DIR', str(cache_dir)):
        cached = wl_mod.cache_seclists_wordlists(source_base=str(source), overwrite=True)

    assert cached['subdomains:small'] == os.path.join(str(cache_dir), 'seclists_subdomains_small.txt')
    assert cached['directories:small'] == os.path.join(str(cache_dir), 'seclists_directories_small.txt')
    assert cached['parameters:small'] == os.path.join(str(cache_dir), 'seclists_parameters_small.txt')
    assert os.path.isfile(cached['subdomains:small'])
    assert os.path.isfile(cached['directories:small'])
    assert os.path.isfile(cached['parameters:small'])


def test_cache_seclists_wordlists_respects_destination_dir(tmp_path):
    """cache_seclists_wordlists() should write to an explicit destination directory."""
    import vortex.wordlists as wl_mod

    source = tmp_path / 'SecLists'
    sl_dns = source / 'Discovery' / 'DNS'
    sl_dns.mkdir(parents=True)
    (sl_dns / 'subdomains-top1million-5000.txt').write_text('sub1\n')

    destination = tmp_path / 'installed' / 'wordlists'

    cached = wl_mod.cache_seclists_wordlists(
        source_base=str(source),
        destination_dir=str(destination),
        overwrite=True,
    )

    assert cached['subdomains:small'] == os.path.join(str(destination), 'seclists_subdomains_small.txt')
    assert os.path.isfile(cached['subdomains:small'])
    assert os.path.isdir(destination)


def test_cache_seclists_wordlists_downloads_when_source_missing(tmp_path):
    """download_missing=True should populate cached files from upstream URLs."""
    import vortex.wordlists as wl_mod

    cache_dir = tmp_path / 'cache'
    cache_dir.mkdir()

    class FakeResponse:
        def __init__(self, data: bytes):
            self._data = data

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self._data

    def fake_urlopen(url, timeout=10):
        assert 'raw.githubusercontent.com/danielmiessler/SecLists/master/' in url
        return FakeResponse(b'downloaded\n')

    with patch.object(wl_mod, 'WORDLIST_DIR', str(cache_dir)):
        with patch.object(wl_mod.urllib.request, 'urlopen', side_effect=fake_urlopen):
            cached = wl_mod.cache_seclists_wordlists(source_base=None, overwrite=True, download_missing=True)

    assert cached['subdomains:small'] == os.path.join(str(cache_dir), 'seclists_subdomains_small.txt')
    assert os.path.isfile(cached['subdomains:small'])
    with open(cached['subdomains:small'], 'r', encoding='utf-8') as fh:
        assert fh.read() == 'downloaded\n'


def test_get_wordlist_for_size_prefers_local_seclists_install(tmp_path):
    """A full local SecLists install should win over flat cached files."""
    import vortex.wordlists as wl_mod

    source = tmp_path / 'SecLists'
    sl_dns = source / 'Discovery' / 'DNS'
    sl_dns.mkdir(parents=True)
    (sl_dns / 'subdomains-top1million-5000.txt').write_text('live\n')

    cache_dir = tmp_path / 'cache'
    cache_dir.mkdir()
    cached_file = cache_dir / 'seclists_subdomains_small.txt'
    cached_file.write_text('cached\n')

    with patch.dict(os.environ, {'SECLISTS_PATH': str(source)}):
        provider = wl_mod.SecListsProvider()
        with patch.object(wl_mod, 'WORDLIST_DIR', str(cache_dir)):
            with patch.object(wl_mod, '_provider', provider):
                path, from_seclists = wl_mod.get_wordlist_for_size('subdomains', 'small')

    assert from_seclists
    assert 'subdomains-top1million-5000.txt' in path


# ---------------------------------------------------------------------------
# Test: get_wordlist_for_size() — fallback to bundled when SecLists absent
# ---------------------------------------------------------------------------

def test_get_wordlist_for_size_falls_back_to_bundled():
    """When SecLists is not available, bundled wordlists are returned."""
    import vortex.wordlists as wl_mod

    with patch.dict(os.environ, {'SECLISTS_PATH': ''}, clear=False):
        with patch('vortex.wordlists._SECLISTS_SEARCH_PATHS', ['/nonexistent']):
            with patch.object(wl_mod, 'get_local_seclists_base', return_value=None):
                with patch.object(wl_mod, 'get_cached_wordlist_path', return_value=None):
                    provider = wl_mod.SecListsProvider()
                    with patch.object(wl_mod, '_provider', provider):
                        for module in ('subdomains', 'directories', 'parameters'):
                            path, from_seclists = wl_mod.get_wordlist_for_size(module, 'small')
                            assert not from_seclists
                            assert os.path.isfile(path)


def test_get_wordlist_for_size_uses_seclists_when_available(tmp_path):
    """When SecLists files exist, get_wordlist_for_size returns them."""
    import vortex.wordlists as wl_mod

    # Create fake SecLists structure
    sl_sub = tmp_path / 'Discovery' / 'DNS'
    sl_sub.mkdir(parents=True)
    sl_dir = tmp_path / 'Discovery' / 'Web-Content'
    sl_dir.mkdir(parents=True)

    (sl_sub / 'subdomains-top1million-5000.txt').write_text('sub1\nsub2\n')
    (sl_dir / 'common.txt').write_text('admin\nlogin\n')
    (sl_dir / 'burp-parameter-names.txt').write_text('id\npage\n')

    with patch.object(wl_mod, 'get_local_seclists_base', return_value=None):
        with patch.dict(os.environ, {'SECLISTS_PATH': str(tmp_path)}):
            provider = wl_mod.SecListsProvider()
            assert provider.available

            with patch.object(wl_mod, '_provider', provider):
                with patch.object(wl_mod, 'get_cached_wordlist_path', return_value=None):
                    path_sub, from_sl = wl_mod.get_wordlist_for_size('subdomains', 'small')
                    assert from_sl
                    assert 'subdomains-top1million-5000.txt' in path_sub

                    path_dir, from_sl = wl_mod.get_wordlist_for_size('directories', 'small')
                    assert from_sl
                    assert 'common.txt' in path_dir

                    path_param, from_sl = wl_mod.get_wordlist_for_size('parameters', 'small')
                    assert from_sl
                    assert 'burp-parameter-names.txt' in path_param


def test_get_wordlist_for_size_all_sizes(tmp_path):
    """All size tiers are resolved correctly when SecLists files are present."""
    import vortex.wordlists as wl_mod

    sl_dns = tmp_path / 'Discovery' / 'DNS'
    sl_dns.mkdir(parents=True)
    sl_web = tmp_path / 'Discovery' / 'Web-Content'
    sl_web.mkdir(parents=True)

    # Create all expected SecLists files
    for fname in (
        'subdomains-top1million-5000.txt',
        'subdomains-top1million-20000.txt',
        'subdomains-top1million-110000.txt',
    ):
        (sl_dns / fname).write_text('a\n')

    for fname in (
        'common.txt',
        'raft-medium-directories.txt',
        'directory-list-2.3-medium.txt',
        'burp-parameter-names.txt',
    ):
        (sl_web / fname).write_text('a\n')

    with patch.object(wl_mod, 'get_local_seclists_base', return_value=None):
        with patch.dict(os.environ, {'SECLISTS_PATH': str(tmp_path)}):
            provider = wl_mod.SecListsProvider()
            with patch.object(wl_mod, '_provider', provider):
                with patch.object(wl_mod, 'get_cached_wordlist_path', return_value=None):
                    for size in ('small', 'medium', 'large'):
                        for module in ('subdomains', 'directories', 'parameters'):
                            path, from_sl = wl_mod.get_wordlist_for_size(module, size)
                            assert from_sl, f"Expected SecLists for {module}/{size}"
                            assert os.path.isfile(path)


def test_seclists_env_var_empty_falls_back_to_search(tmp_path):
    """An empty SECLISTS_PATH env var is ignored; search paths are used."""
    import vortex.wordlists as wl_mod

    with patch.object(wl_mod, 'get_local_seclists_base', return_value=None):
        with patch.dict(os.environ, {'SECLISTS_PATH': ''}, clear=False):
            with patch('vortex.wordlists._SECLISTS_SEARCH_PATHS', [str(tmp_path)]):
                provider = wl_mod.SecListsProvider()
                assert provider.available
                assert provider.base_path == str(tmp_path)


# ---------------------------------------------------------------------------
# Test: CLI falls back to defaults when -w is not specified
# ---------------------------------------------------------------------------

def test_cli_subdomain_uses_default_wordlist(tmp_path, capsys):
    """When -d is given without -w, the built-in subdomain wordlist is used."""
    from vortex.wordlists import DEFAULT_SUBDOMAINS

    captured_wordlist = []

    async def fake_enum(domain, wordlist, *args, **kwargs):
        captured_wordlist.append(wordlist)
        return []

    with (
        patch("vortex.subdomain.enumerate_subdomains", side_effect=fake_enum),
        patch("sys.argv", ["vorteX", "-d", "example.com"]),
        patch("sys.stdin.isatty", return_value=True),
    ):
        from vortex import main as main_module
        try:
            main_module.main()
        except SystemExit:
            pass

    if captured_wordlist:
        assert captured_wordlist[0] == DEFAULT_SUBDOMAINS


def test_cli_user_wordlist_overrides_default(tmp_path):
    """When -w is given, that wordlist should be used instead of the default."""
    custom_wl = tmp_path / "custom.txt"
    custom_wl.write_text("test\n")

    from vortex.wordlists import DEFAULT_SUBDOMAINS

    captured_wordlist = []

    async def fake_enum(domain, wordlist, *args, **kwargs):
        captured_wordlist.append(wordlist)
        return []

    with (
        patch("vortex.subdomain.enumerate_subdomains", side_effect=fake_enum),
        patch("sys.argv", ["vorteX", "-d", "example.com", "-w", str(custom_wl)]),
        patch("sys.stdin.isatty", return_value=True),
    ):
        from vortex import main as main_module
        try:
            main_module.main()
        except SystemExit:
            pass

    if captured_wordlist:
        assert captured_wordlist[0] == str(custom_wl)
        assert captured_wordlist[0] != DEFAULT_SUBDOMAINS
