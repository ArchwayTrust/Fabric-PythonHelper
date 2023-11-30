from setuptools import setup, find_packages

setup(
    name='fabric_python_helper',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        "msal",
        "requests",
        "json",
        "base64",
        "time",
        "logging"
    ],
    author='Ben Dobbs',
    author_email='bdobbs@archwaytrust.co.uk',
    description='Collection of useful python code for automation in Microsoft Fabric.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ArchwayTrust/Fabric-PythonHelper',
)