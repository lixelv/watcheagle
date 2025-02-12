from setuptools import setup, find_packages


def readme():
    with open("README.md", "r") as f:
        return f.read()


setup(
    name="watcheagle",
    version="1.0.1",
    author="lixelv",
    author_email="simeongfremenko@gmail.com",
    description="watcheagle - is hot reloader for your project based on watchdog!",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/lixelv/watcheagle",
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3.11",
    ],
    keywords="watchcat watchdogs watcheagle watcheagle hotreloader reloader",
    python_requires=">=3.11",
)
