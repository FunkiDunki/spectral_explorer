from setuptools import setup, find_packages

setup(
    name="spectral_explorer",
    version="0.1.0",
    description="A package for running a text game about exploring generated worlds",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Nicholas Hotelling",
    author_email="nicholashotelling@gmail.com",
    url="https://github.com/FunkiDunki/spectral_explorer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "openai",
    ],
    extras_require={
        "dev": [],
    },
)
