"""setup.py"""
import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="persession",
    version="0.1.2",
    description="A wrapper on requests session with persistence and login functionalities",
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
        'Intended Audience :: Developers',
    ],
    python_requires='>=3',
    include_package_data=True,
    install_requires=['requests'],
    keywords='requests session persistent login utility development',
    project_urls={
        'Documentation': 'https://github.com/rishabhsingh971/persession/README.md',
        'Source': 'https://github.com/rishabhsingh971/persession/',
        'Tracker': 'https://github.com/rishabhsingh971/persession/issues',
    },
)
