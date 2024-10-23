import os

from setuptools import find_packages, setup

import uk_geo_utils

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


def _get_description():
    try:
        path = os.path.join(os.path.dirname(__file__), "README.md")
        with open(path, encoding="utf-8") as f:
            return f.read()
    except IOError:
        return ""


def get_version():
    return uk_geo_utils.__version__


setup(
    name="uk_geo_utils",
    version=get_version(),
    author="chris48s",
    license="MIT",
    url="https://github.com/DemocracyClub/uk-geo-utils",
    packages=find_packages(),
    include_package_data=True,
    description="Django app for working with OS Addressbase, ONSUD and ONSPD",
    long_description=_get_description(),
    long_description_content_type="text/markdown",
    install_requires=["Django>=4.2", "psycopg2-binary", "psutil"],
    extras_require={"development": ["coveralls", "mkdocs", "ruff==0.6.2"]},
    classifiers=[
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.1",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.12",
    ],
    project_urls={
        "Documentation": "https://democracyclub.github.io/uk-geo-utils/",
        "Source": "https://github.com/DemocracyClub/uk-geo-utils",
    },
)
