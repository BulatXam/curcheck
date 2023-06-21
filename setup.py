from setuptools import setup

long_description = "None description"

setup(
    name='curcheck',
    version='1.1.2b',
    description='Library for parsing SPA and MPA sites',
    packages=['curcheck'],
    author="BulatXam",
    author_email='Khamdbulat@yandex.ru',
    zip_safe=False,
    install_requires=[
        "pyppeteer",
        "aiohttp",
        "lxml",
    ],

    long_description=long_description,
    long_description_content_type='text/markdown',
)
