#!/usr/bin/env python
from setuptools import setup, find_packages
# from admin_reports import __version__
setup(
    name='admin_reports',
    version='0.10.1',
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
