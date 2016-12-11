# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name = 'bluepy_devices',
    version = '0.3.0',
    packages = ['bluepy_devices', 'bluepy_devices.devices', 'bluepy_devices.lib'],
    install_requires = ['bluepy>=1.0.4'],
    description = 'Usability Library for bluepy, and device implementations, mainly for homeassistant integration',
    author = 'Markus Peter',
    author_email = 'mpeter@emdev.de',
    url = 'https://github.com/bimbar/bluepy_devices.git',
    license ="MIT"
)
