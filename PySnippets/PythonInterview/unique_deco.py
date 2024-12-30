"""
This function can return non-unique outputs. How can we change so that it returns only unique outputs, i.e. if we already saw some output, it shouldn't show up again?
"""

from random import choices, randint
from string import ascii_lowercase

def randstr():
    return ''.join(choices(ascii_lowercase, k=randint(0,100)))

