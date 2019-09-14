"""setup.py"""
import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="persession",
    version="0.0.2",
    description="A wrapper on requests session with persistance and login functionalities",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/rishabhsingh971/persession",
    author="Rishabh Singh",
    author_email="rishabhsingh971@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        'Development Status :: 3 - Alpha',
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3',
    packages=find_packages(),
    include_package_data=True,
    install_requires=find_packages(),
)
