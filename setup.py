from distutils.core import setup

with open("README", 'r') as f:
    long_description = f.read()

setup(
    name='Japanrealestate',
    version='',
    packages=[
        'japanrealestate',
        'japanrealestate.test'
    ],
    url='',
    license='',
    description='To help analyze the economics of renting and owning real estate in Japan',
    long_description=long_description,
    install_requires=[
        'numpy',
        'python-dateutil',
    ]
)

