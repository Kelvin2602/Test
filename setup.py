from setuptools import setup, find_packages

setup(
    name="telegram-attendance-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
    ],
    python_requires='>=3.8',
) 