"""Tests for vortex/seclists.py."""

import os
from unittest.mock import patch


def test_find_seclists_returns_none_when_absent():
    """find_seclists() returns None when no SecLists installation is present."""
    import vortex.seclists as sl_mod

    with patch.dict(os.environ, {"SECLISTS_PATH": ""}, clear=False):
        with patch("vortex.wordlists._SECLISTS_SEARCH_PATHS", ["/nonexistent/seclists"]):
            from vortex.wordlists import SecListsProvider
            provider = SecListsProvider()
            with patch.object(sl_mod, "_provider", provider):
                assert sl_mod.find_seclists() is None


def test_find_seclists_returns_path_when_present(tmp_path):
    """find_seclists() returns the detected SecLists base directory."""
    import vortex.seclists as sl_mod

    with patch.dict(os.environ, {"SECLISTS_PATH": str(tmp_path)}):
        from vortex.wordlists import SecListsProvider
        provider = SecListsProvider()
        with patch.object(sl_mod, "_provider", provider):
            assert sl_mod.find_seclists() == str(tmp_path)


def test_find_seclists_prefers_cached_wordlists(tmp_path):
    """find_seclists() should return the local cache directory when it exists."""
    import vortex.seclists as sl_mod
    import vortex.wordlists as wl_mod

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "seclists_subdomains_small.txt").write_text("cached\n")

    with patch.object(wl_mod, "WORDLIST_DIR", str(cache_dir)):
        with patch.dict(os.environ, {"SECLISTS_PATH": ""}, clear=False):
            provider = wl_mod.SecListsProvider()
            with patch.object(sl_mod, "_provider", provider):
                assert sl_mod.find_seclists() == str(cache_dir)


def test_get_seclists_wordlist_returns_none_when_absent():
    """get_seclists_wordlist() returns None when SecLists is not installed."""
    import vortex.seclists as sl_mod

    with patch.dict(os.environ, {"SECLISTS_PATH": ""}, clear=False):
        with patch("vortex.wordlists._SECLISTS_SEARCH_PATHS", ["/nonexistent"]):
            from vortex.wordlists import SecListsProvider
            provider = SecListsProvider()
            with patch.object(sl_mod, "_provider", provider):
                assert sl_mod.get_seclists_wordlist("subdomains") is None


def test_get_seclists_wordlist_returns_cached_path(tmp_path):
    """get_seclists_wordlist() should prefer the cached local copy when present."""
    import vortex.seclists as sl_mod
    import vortex.wordlists as wl_mod

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cached_wordlist = cache_dir / "seclists_subdomains_small.txt"
    cached_wordlist.write_text("cached\n")

    source = tmp_path / "SecLists"
    sl_dns = source / "Discovery" / "DNS"
    sl_dns.mkdir(parents=True)
    (sl_dns / "subdomains-top1million-5000.txt").write_text("live\n")

    with patch.object(wl_mod, "WORDLIST_DIR", str(cache_dir)):
        with patch.dict(os.environ, {"SECLISTS_PATH": str(source)}):
            from vortex.wordlists import SecListsProvider
            provider = SecListsProvider()
            with patch.object(sl_mod, "_provider", provider):
                path = sl_mod.get_seclists_wordlist("subdomains", "small")
                assert path == str(cached_wordlist)


def test_get_seclists_wordlist_returns_path_when_file_exists(tmp_path):
    """get_seclists_wordlist() returns the correct path when the file exists."""
    import vortex.seclists as sl_mod

    sl_dns = tmp_path / "Discovery" / "DNS"
    sl_dns.mkdir(parents=True)
    wordlist_file = sl_dns / "subdomains-top1million-5000.txt"
    wordlist_file.write_text("example\n")

    with patch.dict(os.environ, {"SECLISTS_PATH": str(tmp_path)}):
        from vortex.wordlists import SecListsProvider
        provider = SecListsProvider()
        with patch.object(sl_mod, "_provider", provider):
            path = sl_mod.get_seclists_wordlist("subdomains", "small")
            assert path is not None
            assert os.path.isfile(path)
            assert "subdomains-top1million-5000.txt" in path


def test_seclists_module_exports():
    """seclists module exposes expected public API."""
    from vortex import seclists
    assert callable(seclists.find_seclists)
    assert callable(seclists.get_seclists_wordlist)
    assert callable(seclists.get_wordlist_for_size)
