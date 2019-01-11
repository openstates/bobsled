#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='bobsled',
      version='0.6',
      description='a cool task runner',
      author='James Turk',
      author_email='james@openstates.org',
      url='https://github.com/openstates/bobsled',
      entry_points={
          'console_scripts': [
              'bobsled = bobsled.cli:cli'
          ]
      },
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'boto3',
          'PyYAML',
          'pynamodb==2.1.5',
          'github3.py==0.9.6',
          'Jinja2==2.9.5',
          'click',
      ]
      )
