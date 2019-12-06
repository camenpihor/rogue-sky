"""Packaging for the amex-risk library."""
from setuptools import find_packages, setup


def get_version():
    """Get library version."""
    with open("VERSION") as f:
        return f.read()


setup(
    name="rogue-sky",
    version=get_version(),
    url="",
    author="Camen",
    author_email="camenpihor@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=open("requirements.in").readlines(),
    tests_require=open("requirements.testing.in").readlines(),
    description="Get daily predictions for star visibility anywhere in the US",
    long_description="\n" + open("README.md").read(),
)
