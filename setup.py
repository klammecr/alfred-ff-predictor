from distutils.core import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='alfred',
    version='0.1',
    packages=['alfred',],
    long_description=open('README.md').read(),
    install_requires=required
)