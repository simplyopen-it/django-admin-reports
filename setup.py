from setuptools import find_packages, setup
from admin_reports import __version__ as version_string

setup(
    name='django-admin-reports',
    version=version_string,
    description='Reports for django-admin',
    author='Simplyopen SRL',
    author_email='info@simplyopen.org',
    url='https://github.com/simplyopen-it/django-admin-reports',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        "Intended Audience :: Developers",
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Django>=1.11',
        'pandas>=0.18',
    ]
)
