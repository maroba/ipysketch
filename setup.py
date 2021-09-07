#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import exists
from setuptools import setup, find_packages

author = 'Matthias Baer'
email = 'matthias.r.baer@googlemail.com'
description = 'Handwriting and sketching in Jupyter notebooks'
name = 'ipysketch'
year = '2021'
url = 'https://github.com/maroba/ipysketch'
version = '0.1.0'

setup(
    name=name,
    author=author,
    author_email=email,
    url=url,
    version=version,
    packages=find_packages(),
    package_dir={name: name},
    include_package_data=True,
    license='None',
    description=description,
    long_description=open('res/README_pypi.md').read() if exists('README.md') else '',
    long_description_content_type="text/markdown",
    install_requires=['sphinx',
                      'ipywidgets',
                      'ipython',
                      'scikit-image',
                      'Pillow',
                      'setuptools'
                      ],
    python_requires=">=3.6",
    classifiers=['Operating System :: OS Independent',
                 'Programming Language :: Python :: 3',
                 ],
    platforms=['ALL'],
)
