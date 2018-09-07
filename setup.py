#!/usr/bin/env python
from setuptools import setup

setup(
    name='scrapy-browser',
    version='0.0.1',
    url='https://github.com/michalmo/scrapy-browser',
    description='Proof of Concept of scraping with browser automation',
    packages=['scrapy_browser'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Scrapy',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    requires=['scrapy'],
)
