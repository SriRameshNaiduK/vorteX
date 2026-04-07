import os

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        from vortex.wordlists import install_full_seclists

        project_root = os.path.dirname(os.path.abspath(__file__))
        source_wordlist_dir = os.path.join(project_root, 'vortex', 'wordlists')
        build_wordlist_dir = os.path.join(self.build_lib, 'vortex', 'wordlists')

        source_installed = install_full_seclists(destination_parent=source_wordlist_dir, overwrite=True)
        build_installed = install_full_seclists(destination_parent=build_wordlist_dir, overwrite=True)

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


