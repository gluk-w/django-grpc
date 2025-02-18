#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from shutil import rmtree
from setuptools import setup, Command


here = os.path.abspath(os.path.dirname(__file__))

readme = open('README.md').read()

setup(
    name='django-grpc',
    version='1.0',  # update in pyproject.toml
    description="""Easy Django based gRPC service""",
    long_description=readme,  # + '\n\n' + history,
    long_description_content_type="text/markdown",
    author='Stan Misiurev',
    author_email='smisiurev@gmail.com',
    url='https://github.com/gluk-w/django-grpc',
    packages=[
        'django_grpc',
        'django_grpc_testtools',
    ],
    include_package_data=True,
    install_requires=['setuptools'],
    license="MIT",
    zip_safe=False,
    keywords='django-grpc',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
