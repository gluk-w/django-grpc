#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from shutil import rmtree
from setuptools import setup, Command


here = os.path.abspath(os.path.dirname(__file__))

about = {}
# Load the package's __version__.py module as a dictionary.
with open(os.path.join(here, 'django_grpc', '__version__.py')) as f:
    exec(f.read(), about)


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(about['__version__']))
        os.system('git push --tags')

        sys.exit()


readme = open('README.md').read()
# history = open('HISTORY.md').read().replace('.. :changelog:', '')

setup(
    name='django-grpc',
    version=about['__version__'],
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
    ],
    cmdclass={
        'upload': UploadCommand,
    },
)
