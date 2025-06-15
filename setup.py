from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="calliphoridays",
    version="0.1.0",
    author="grigsbyanthony",
    description="Forensic entomology PMI estimation tool for blow fly evidence",
    long_description="A CLI tool for estimating postmortem intervals using Calliphoridae evidence and temperature data",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "calliphoridays=calliphoridays.main_cli:cli",
            "calliphoridays-single=calliphoridays.cli:main",
            "calliphoridays-multi=calliphoridays.multi_cli:multi_analyze",
            "calliphoridays-gui=calliphoridays.gui:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)