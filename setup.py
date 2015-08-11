from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

long_description = """
A Cary command for querying the US Government per diem tables;
email with the body 'city, state, USA' or 'city, country' and it
will respond with the per diem rates for that area.  Must download
data files from the US government websites.
"""

setup(
    name='cary_perdiemcommand',
    version='1.0.1',
    description='US gov per-diem lookup for Cary',
    long_description=long_description,
    url='https://github.com/vputz/cary_perdiemcommand',
    author='Victor Putz',
    author_email='vputz@nyx.net',

    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Communications :: Email',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        ],

    keywords='email',

    packages=['cary_perdiemcommand'],

    install_requires=['cary',
                      'jinja2',
                      'tinydb',
                      'pyquery',
                      'fuzzywuzzy',
                      'python-Levenshtein'
                  ],

    extras_require={},

    package_data={
        'cary_perdiemcommand': ['templates/*']
        },

    data_files=[],

    entry_points={
        'console_scripts': [
            'cary_perdiem = cary_perdiemcommand.__main__:main'
            ]
            },
)
