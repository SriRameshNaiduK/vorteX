import os
from unittest.mock import patch

from setuptools import Distribution

import setup as setup_mod


def test_build_py_stages_seclists_to_source_and_build_tree(tmp_path):
    calls = []

    def fake_cache(**kwargs):
        calls.append(kwargs)
        return {}

    dist = Distribution()
    cmd = setup_mod.build_py(dist)
    cmd.build_lib = str(tmp_path / 'build' / 'lib')

    with patch('vortex.wordlists.cache_seclists_wordlists', side_effect=fake_cache):
        with patch.object(setup_mod._build_py, 'run', return_value=None):
            cmd.run()

    assert len(calls) == 2
    assert calls[0]['destination_dir'].endswith(os.path.join('vortex', 'wordlists'))
    assert calls[1]['destination_dir'].endswith(os.path.join('build', 'lib', 'vortex', 'wordlists'))
    assert calls[0]['overwrite'] is True
    assert calls[1]['overwrite'] is True

