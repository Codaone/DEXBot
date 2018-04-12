#!/usr/bin/env python3

from setuptools import setup, find_packages
from distutils.command import build as build_module
from pyqt_distutils.build_ui import build_ui

from dexbot import VERSION, APP_NAME


class BuildCommand(build_module.build):
    def run(self):
        self.run_command('build_ui')
        build_module.build.run(self)


setup(
    name=APP_NAME,
    version=VERSION,
    description='Trading bot for the DEX (BitShares)',
    long_description=open('README.md').read(),
    author='Codaone Oy',
    author_email='support@codaone.com',
    maintainer='Codaone Oy',
    maintainer_email='support@codaone.com',
    url='http://www.github.com/codaone/dexbot',
    keywords=['DEX', 'bot', 'trading', 'api', 'blockchain'],
    packages=find_packages(),
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    cmdclass={
        'build_ui': build_ui,
        'build': BuildCommand
    },
    entry_points={
        'console_scripts': [
            'dexbot-cli = dexbot.cli:main',
            'dexbot-gui = dexbot.gui:main',
        ],
    },
    install_requires=[
        "bitshares",
        "uptick>=0.1.4",
        "click",
        "sqlalchemy",
        "appdirs",
        "ruamel.yaml>=0.15.37"
    ],
    include_package_data=True,
)

