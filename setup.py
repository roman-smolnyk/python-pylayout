from setuptools import setup, find_packages


setup(
    name="pylayout",
    version="0.0.4",
    license="MIT",
    author="Roman Smolnyk",
    author_email="poma23324@gmail.com",
    packages=find_packages("src"),
    package_dir={"": "src"},
    url="https://gitlab.com/roman-smolnyk/pylayout",
    keywords="Keyboard layout",
    install_requires=[
        "pywin32; platform_system=='Windows'",
    ],
    description="Get/Set keyboard layout"
)
