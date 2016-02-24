from setuptools import setup, find_packages
#import ez_setup
#ez_setup.use_setuptools()
import IceCat
version = IceCat.__version__
setup(
    name = "IceCat",
    version = version,
    author = "Vasiliy Gokoyev",
    author_email = "gokoyev@gmail.com",
    packages = find_packages(),
    include_package_data = True,
    url = "https://github.com/moonlitesolutions/pyIceCat",
    description = "Python based parser for IceCat catalog. ",
    install_requires = [
        "requests>=2.2.1",
        "progressbar2>=3.6.0",
        "urllib3>=1.14",
        "xmltodict>=0.9.2"
    ],
)