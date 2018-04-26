#!/usr/bin/python

# Setup script for the `negotiator-common' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: April 26, 2018
# URL: https://negotiator.readthedocs.org

"""Setup script for the ``negotiator-common`` package."""

# Standard library modules.
import os
import re

# De-facto standard solution for Python packaging.
from setuptools import setup, find_packages

# Find the directory where the source distribution was unpacked.
source_directory = os.path.dirname(os.path.abspath(__file__))

# Find the current version.
module = os.path.join(source_directory, 'negotiator_common', '__init__.py')
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

setup(name='negotiator-common',
      version=version_string,
      description="Scriptable KVM/QEMU guest agent (common functionality)",
      long_description=readme_text,
      url='https://negotiator.readthedocs.org',
      author="Peter Odding",
      author_email='peter@peterodding.com',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'executor >= 1.3',
          'humanfriendly >= 4.12',
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX',
          'Operating System :: POSIX :: Linux',
          'Operating System :: Unix',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Topic :: Communications',
          'Topic :: Software Development',
          'Topic :: System',
          'Topic :: System :: Installation/Setup',
          'Topic :: System :: Operating System',
          'Topic :: System :: Operating System Kernels :: Linux',
          'Topic :: System :: Systems Administration',
      ])
