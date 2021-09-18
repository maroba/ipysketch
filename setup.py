#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import exists, realpath, dirname
import sys
from setuptools import setup, find_packages

author = 'Matthias Baer'
email = 'matthias.r.baer@googlemail.com'
description = 'Handwriting and sketching in Jupyter notebooks'
name = 'ipysketch'
year = '2021'
url = 'https://github.com/maroba/ipysketch'
version = '0.2.2'

sys.path.insert(0, realpath(dirname(__file__))+"/"+name)

setup(
    name=name,
    author=author,
    author_email=email,
    url=url,
    version=version,
    packages=find_packages(exclude=("tests",)),
    package_dir={name: name},
    include_package_data=True,
    license='GPLv3',
    description=description,
    long_description=open('res/README_pypi.md').read() if exists('README.md') else '',
    long_description_content_type="text/markdown",
    install_requires=['sphinx',
                      'ipywidgets',
                      'ipython',
                      'scikit-image',
                      'Pillow',
                      'setuptools',
                      'scipy',
                      'Shapely',
                      'numpy'
                      ],
    python_requires=">=3.6",
    classifiers=['Operating System :: OS Independent',
                 'Programming Language :: Python :: 3',
                 ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    platforms=['ALL'],
)
