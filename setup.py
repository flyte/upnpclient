#  -*- coding: utf-8 -*-
"""
Setuptools script for the PyuPnPClient project.
"""

import os
from textwrap import fill, dedent


try:
    from setuptools import setup, find_packages
    from setuptools.command.build_py import build_py
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
    from setuptools.command.build_py import build_py


def required(fname):
    return open(
        os.path.join(
            os.path.dirname(__file__), fname
        )
    ).read().split('\n')


setup(
    name="PyuPnPClient",
    version="0.0.1",
    packages=find_packages(
        exclude=[
            "*.tests",
            "*.tests.*",
            "tests.*",
            "tests",
            "*.ez_setup",
            "*.ez_setup.*",
            "ez_setup.*",
            "ez_setup",
            "*.examples",
            "*.examples.*",
            "examples.*",
            "examples"
        ]
    ),
    scripts=[],
    include_package_data=True,
    setup_requires='pytest-runner',
    tests_require='pytest',
    install_requires=required('requirements.txt'),
    test_suite='pytest',
    zip_safe=False,
    # Metadata for upload to PyPI
    author='FIXME',
    author_email="FIXME",
    description=fill(dedent("""\
        FIXME
    """)),
    classifiers=[
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Communications",
        "Topic :: Home Automation",
        "Topic :: System :: Networking"
    ],
    license="MIT",
    keywords="",
    url="https://github.com/FIXME"
)
