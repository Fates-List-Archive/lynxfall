from setuptools import setup
from Cython.Build import cythonize
import os

os.system("pip install -r requirements.txt") # Hacky solution to get it working
          
setup(
    name='lynxfall',
    version = "1.0",
    author = "Rootspring",
    author_email = "tor_needletail@outlook.com",
    ext_modules=cythonize([
        "lynxfall/mdextend/*.pyx",
        "lynxfall/utils/*.pyx",
    ]),
    packages=[
        "lynxfall", 
        "lynxfall.core",
        "lynxfall.mdextend",
        "lynxfall.utils",
    ],
    zip_safe=False,
)
