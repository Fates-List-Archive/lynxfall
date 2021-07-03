from setuptools import setup
from Cython.Build import cythonize

setup(
    name='lynxfall',
    version = "1.0",
    author = "Rootspring",
    author_email = "tor_needletail@outlook.com",
    ext_modules=cythonize([
        "lynxfall/mdextend/*.pyx",
        "lynxfall/utils/*.pyx",
        "lynxfall/ratelimits/*.pyx",
        "lynxfall/rabbit/*.pyx",
        "lynxfall/rabbit/core/*.pyx",
        "lynxfall/rabbit/core/default_backends/*.pyx"
    ]),
    packages=["lynxfall", "lynxfall.mdextend", "lynxfall.utils", "lynxfall.ratelimits", "lynxfall.rabbit"],
    zip_safe=False,
)
