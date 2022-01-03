import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="liquer-framework",
    version="0.7.0",
    author="Orest Dubay",
    author_email="orest3.dubay@gmail.com",
    description="LiQuer - Query in (URL) link",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/orest-d/liquer",
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
