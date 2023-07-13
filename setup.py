# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages
setup(
    name='vip_python_client',            # The name registered on PyPI
    version='0.0.1',
    description='Use VIP through a Python client.', # This text will be displayed on the plugin page
    include_package_data=True,
    packages=find_packages(),
    zip_safe=False,
    install_requires=['requests'],      # Add any plugin dependencies here
)
