from setuptools import setup, find_packages

setup(
    name="atlas-support-bot",
    version="0.1.0",
    description="A Slack bot designed to facilitate technical support requests",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "slack-bolt>=1.16.1",
        "slack-sdk>=3.19.5",
        "python-dotenv>=0.21.0",
        "openai>=0.27.8",
        "requests>=2.28.2",
        "pydantic>=1.10.8",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.8",
) 