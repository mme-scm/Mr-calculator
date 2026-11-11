"""Convention tests of section 3 (run before every pass)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import conventions  # noqa: E402


@pytest.mark.parametrize('name,func', conventions.TESTS, ids=[t[0] for t in conventions.TESTS])
def test_convention(name, func):
    ok, detail = func()
    assert ok, detail
