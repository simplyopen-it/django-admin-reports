#!/usr/bin/env python
import os
import re
import codecs
from setuptools import setup, find_packages

def find_version(*file_paths):
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    with codecs.open(filename, encoding='utf-8') as fp:
        version_file = fp.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='admin_reports',
    version=find_version('admin_reports', '__init__.py'),
    description='Reports for django-admin',
    long_description="Easily define and show data analysis reports for django-admin.",
    author='Simplyopen',
    author_email='info@simplyopen.org',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
    ],
    packages=find_packages(),
    package_dir={'admin_reports': 'admin_reports'},
    include_package_data=True,
    install_requires=['Django>=1.7'],
)
