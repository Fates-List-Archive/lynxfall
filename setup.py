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
        "lynxfall/ratelimits/*.pyx",
    ]),
    packages=[
        "lynxfall", 
        "lynxfall.core",
        "lynxfall.mdextend",
        "lynxfall.utils",
        "lynxfall.ratelimits",
        "lynxfall.rabbit",
        "lynxfall.rabbit.client",
        "lynxfall.rabbit.core",
        "lynxfall.oauth",
        "lynxfall.oauth.providers"
    ],
    zip_safe=False,
)
