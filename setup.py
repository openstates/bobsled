#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='bobsled',
      version='0.2',
      description='a cool task runner',
      author='James Turk',
      author_email='james@openstates.org',
      url='https://github.com/openstates/bobsled',
      packages=find_packages(),
      include_package_data=True,
)
