"""This module contains the packaging routine for the pybook package"""

from setuptools import setup
from pip.req import parse_requirements


def get_requirements(source):
    """Get the requirements from the given ``source``

    Parameters
    ----------
    source: str
        The filename containing the requirements

    """

    install_reqs = parse_requirements(source)

    return set(
        [str(ir.req) for ir in install_reqs]
    )

setup(

)


