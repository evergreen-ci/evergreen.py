#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from glob import glob
import os
from os.path import basename, splitext

from setuptools import find_packages
from setuptools import setup


def _find_version_line_in_file(file_path):
    with open(str(file_path), "r") as fileh:
        version_lines = [
            line for line in fileh.readlines() if line.startswith("VERSION")
        ]
        if len(version_lines) != 1:
            raise ValueError(
                "Unable to determine 'VERSION' in {file}".format(file=file_path)
            )
        return version_lines[0]


def lookup_local_module_version(file_path):
    path_to_init = os.path.join(str(file_path), "__init__.py")
    version_tuple = eval(_find_version_line_in_file(path_to_init).split("=")[-1])
    return ".".join([str(x) for x in version_tuple])


version = lookup_local_module_version(os.path.join(os.path.dirname(__file__), "src", "evergreen"))

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='evergreen.py',
    version=version,  # The version can be updated in `src/evergreen/__init__.py`.
    license='Apache License, Version 2.0',
    description='Python client for the Evergreen API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='David Bradford',
    author_email='david.bradford@mongodb.com',
    url='https://github.com/evergreen-ci/evergreen.py',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    install_requires=[
        'backports.functools_lru_cache ~= 1.5;python_version<"3.3"',
        'enum34 ~= 1.1.6;python_version<"3.3"',
        'Click ~= 7.0',
        'pylibversion ~= 0.1.0',
        'PyYAML ~= 5.1',
        'requests ~= 2.22.0',
        'structlog ~= 19.1.0',
        'tenacity ~= 5.0.4',
    ],
    entry_points={
        'console_scripts': [
            'evg-api=evergreen.cli.main:main',
        ],
    },
)
