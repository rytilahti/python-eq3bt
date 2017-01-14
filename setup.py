# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='python-eq3bt',
    version='0.1.1',
    packages=['eq3bt'],
    install_requires=['bluepy>=1.0.5'],
    description='EQ3 bluetooth thermostat support library',
    author='Markus Peter',
    author_email='mpeter@emdev.de',
    maintainer='Teemu Rytilahti',
    maintainer_email='tpr@iki.fi',
    url='https://github.com/rytilahti/python-eq3bt.git',
    license="MIT",
    entry_points={
        'console_scripts': [
            'eq3cli = utils.eq3cli:cli'
        ]
    }
)
