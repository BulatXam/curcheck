from setuptools import setup

with open('readme.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='curcheck',
    version='1.0',
    description='Library for parsing SPA and MPA sites',
    packages=['curcheck'],
    author="BulatXam",
    author_email='Khamdbulat@yandex.ru',
    zip_safe=False,
    install_requires=[
        "pyppeteer",
        "pydantic",
        "aiohttp",
        "lxml",
    ],

    long_description=long_description,
    long_description_content_type='text/markdown',
)
