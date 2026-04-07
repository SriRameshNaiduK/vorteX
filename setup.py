import os
import shutil
import tempfile
import urllib.request
import zipfile

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py

_SECLISTS_ARCHIVE_URL = 'https://github.com/danielmiessler/SecLists/archive/refs/heads/master.zip'
_SECLISTS_SEARCH_PATHS = [
    '/usr/share/seclists',
    '/usr/share/SecLists',
    '/opt/seclists',
    os.path.expanduser('~/SecLists'),
]


def _detect_seclists_source(explicit_source=None):
    if explicit_source and os.path.isdir(explicit_source):
        return explicit_source

    env_path = os.environ.get('SECLISTS_PATH', '').strip()
    if env_path and os.path.isdir(env_path):
        return env_path

    for candidate in _SECLISTS_SEARCH_PATHS:
        if os.path.isdir(candidate):
            return candidate

    return None


def _download_and_extract_seclists(destination_parent):
    os.makedirs(destination_parent, exist_ok=True)
    target_dir = os.path.join(destination_parent, 'SecLists')

    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = os.path.join(temp_dir, 'seclists.zip')
        with urllib.request.urlopen(_SECLISTS_ARCHIVE_URL, timeout=30) as response:
            content = response.read()
        if not content:
            return None

        with open(archive_path, 'wb') as handle:
            handle.write(content)

        with zipfile.ZipFile(archive_path, 'r') as archive:
            archive.extractall(temp_dir)

        extracted_root = None
        for name in os.listdir(temp_dir):
            candidate = os.path.join(temp_dir, name)
            if os.path.isdir(candidate) and name.lower().startswith('seclists-'):
                extracted_root = candidate
                break

        if not extracted_root:
            return None

        if os.path.isdir(target_dir):
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.copytree(extracted_root, target_dir)

    return target_dir


def install_full_seclists(destination_parent, source_base=None, overwrite=False):
    destination_parent = os.path.abspath(destination_parent)
    target_dir = os.path.join(destination_parent, 'SecLists')
    os.makedirs(destination_parent, exist_ok=True)

    if os.path.isdir(target_dir) and not overwrite:
        return target_dir

    source_base = _detect_seclists_source(source_base)
    if source_base:
        source_base = os.path.abspath(source_base)
        if source_base != os.path.abspath(target_dir):
            if os.path.isdir(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)
            shutil.copytree(source_base, target_dir)
            return target_dir
        return target_dir

    return _download_and_extract_seclists(destination_parent)


class build_py(_build_py):
    def run(self):
        project_root = os.path.dirname(os.path.abspath(__file__))
        source_wordlist_dir = os.path.join(project_root, 'vortex', 'wordlists')
        build_wordlist_dir = os.path.join(self.build_lib, 'vortex', 'wordlists')

        source_installed = install_full_seclists(destination_parent=source_wordlist_dir, overwrite=True)
        build_installed = install_full_seclists(
            destination_parent=build_wordlist_dir,
            source_base=source_installed,
            overwrite=True,
        )

        if not source_installed or not build_installed:
            raise RuntimeError('SecLists installation failed: unable to install full SecLists corpus.')
        super().run()

def main():
    setup(
        name='vortex-recon',
        version='1.0.2',
        author='SriRameshNaidu Kusu',
        description='vorteX - Advanced Async Reconnaissance & Fuzzing Tool',
        packages=find_packages(),
        include_package_data=True,
        install_requires=open('requirements.txt').read().splitlines(),
        cmdclass={'build_py': build_py},
        entry_points={
            'console_scripts': [
                'vorteX = vortex.main:main',
            ],
        },
    )


if __name__ == '__main__':
    main()


