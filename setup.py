from setuptools import find_packages, setup
from admin_reports import __version__ as version_string

setup(
    name='django-admin-reports',
    # packages=find_packages(),
    packages = ['admin_reports'],
    version=version_string,
    license='MIT',
    description='Reports for django-admin',
    author='Simplyopen SRL',
    author_email='info@simplyopen.org',
    url='https://github.com/mohitgoel188/django-admin-reports',
    download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',
    keywords = 'django admin reports',
    install_requires=[
        'Django>=1.11',
        'pandas>=0.18',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        "Intended Audience :: Developers",
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
    ],
    include_package_data=True,
    zip_safe=False,
)
