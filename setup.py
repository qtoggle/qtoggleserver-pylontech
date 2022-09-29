from setuptools import setup, find_namespace_packages


setup(
    name='qtoggleserver-pylontech',
    version='unknown-version',
    description='Pylontech batteries support for qToggleServer',
    author='Calin Crisan',
    author_email='ccrisan@gmail.com',
    license='Apache 2.0',

    packages=find_namespace_packages(),

    install_requires=[
        'pyserial>=3.4',
        'python-pylontech<0.3',
    ]
)
