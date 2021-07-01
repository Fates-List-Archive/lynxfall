from setuptools import setup
from Cython.Build import cythonize

setup(
    name='mdextend',
    version = "1.0",
    author = "Rootspring",
    author_email = "tor_needletail@outlook.com",
    ext_modules=cythonize("mdextend/emd_hab.pyx"),
    packages=["mdextend"],
    zip_safe=False,
)
