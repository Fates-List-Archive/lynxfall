from setuptools import setup
from Cython.Build import cythonize

setup(
    name='mdextend',
    version = "1.0",
    author = "Rootspring",
    author_email = "tor_needletail@outlook.com",
    ext_modules=cythonize(
        "lynxfall/mdextend/eme.pyx"
    ),
    packages=["lynxfall"],
    zip_safe=False,
)
