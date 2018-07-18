#!/usr/bin/env python3
from dexbot import VERSION, APP_NAME

from setuptools import setup, find_packages
from distutils.command import build as build_module

cmd_class = {}
console_scripts = ['dexbot-cli = dexbot.cli:main']
install_requires = [
    "bitshares==0.1.18",
    "uptick>=0.1.4",
    "click",
    "sqlalchemy",
    "ruamel.yaml>=0.15.37",
    "sdnotify",
    "appdirs>=1.4.3"
]


class BuildCommand(build_module.build):
    def run(self):
        self.run_command('build_ui')
        build_module.build.run(self)


try:
    from pyqt_distutils.build_ui import build_ui
    cmd_class = {
        'build_ui': build_ui,
        'build': BuildCommand
    }
    console_scripts.append('dexbot-gui = dexbot.gui:main')
    install_requires.extend(["pyqt-distutils"])
except BaseException as e:
    print("GUI not available: {}".format(e))


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
    cmdclass=cmd_class,
    entry_points={
        'console_scripts': console_scripts
    },
    install_requires=install_requires,
    include_package_data=True,
)
