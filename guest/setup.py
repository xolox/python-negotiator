#!/usr/bin/python

# Setup script for the `negotiator-guest' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 22, 2014
# URL: https://negotiator.readthedocs.org

"""Setup script for the ``negotiator-guest`` package."""

# Standard library modules.
import os
import re

# De-facto standard solution for Python packaging.
from setuptools import setup, find_packages

# Find the directory where the source distribution was unpacked.
source_directory = os.path.dirname(os.path.abspath(__file__))

# Find the current version.
module = os.path.join(source_directory, 'negotiator_guest', '__init__.py')
for line in open(module, 'r'):
    match = re.match(r'^__version__\s*=\s*["\']([^"\']+)["\']$', line)
    if match:
        version_string = match.group(1)
        break
else:
    raise Exception("Failed to extract version from %s!" % module)

# Fill in the long description (for the benefit of PyPI)
# with the contents of README.rst (rendered by GitHub).
try:
    readme_file = os.path.join(source_directory, 'README.rst')
    readme_text = open(readme_file, 'r').read()
except IOError:
    # This happens on readthedocs.org.
    readme_text = ''

setup(name='negotiator-guest',
      version=version_string,
      description="Generic QEMU guest agent (guest side of things)",
      long_description=readme_text,
      url='https://negotiator.readthedocs.org',
      author="Peter Odding",
      author_email='peter@peterodding.com',
      packages=find_packages(),
      entry_points=dict(console_scripts=[
          'negotiator-guest = negotiator_guest.cli:main'
      ]),
      install_requires=[
          'coloredlogs >= 0.6',
          'executor >= 1.3',
          'negotiator-common >= 0.1',
      ])
