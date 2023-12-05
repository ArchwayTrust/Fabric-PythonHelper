from setuptools import setup, find_packages
from fabric_python_helper import __version__, __author_email__, __author__, __description__, __url__

setup(
    name='fabric_python_helper',
    version=__version__,
    packages=find_packages(),
    install_requires=[
        "msal",
        "requests"
    ],
    author=__author__,
    author_email=__author_email__,
    description=__description__,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url=__url__
)