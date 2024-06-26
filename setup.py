#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
import versioneer
from setuptools import setup, find_packages


requirements = ['simpy', 'pandas', 'xlwt', 'zope.dottedname', 'confluent_kafka', 'questdb', 'scipy']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Data Revenue GmbH, AImotion Bavaria",
    author_email='alan@datarevenue.com, lukas.lodes@thi.de',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="ManPy ported to Python 3",
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    keywords='manpy',
    name='manpy',
    packages=find_packages(),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/datarevenue-berlin/manpy',
    version = versioneer.get_version(),
    cmdclass = versioneer.get_cmdclass(),
    zip_safe=False,
)
