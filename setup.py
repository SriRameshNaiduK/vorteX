import os

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        try:
            from vortex.wordlists import cache_seclists_wordlists

            auto_download = os.environ.get('VORTEX_SECLISTS_AUTO_DOWNLOAD', '1') != '0'
            cache_seclists_wordlists(overwrite=True, download_missing=auto_download)
        except Exception:
            # Best-effort only: never block installation if SecLists cannot be fetched.
            pass
        super().run()

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


