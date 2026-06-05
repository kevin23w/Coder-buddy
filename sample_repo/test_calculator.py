"""
test_calculator.py — pytest tests that expose the 3 bugs in calculator.py.

Run with: pytest sample_repo/ -v --tb=short
"""
import pytest
from calculator import add, subtract, multiply, divide, square_root, factorial


# ── Sanity checks (these should pass even with bugs) ──────────────────────────

def test_add_positive():
    assert add(2, 3) == 5


def test_subtract_positive():
    assert subtract(10, 4) == 6


def test_multiply_positive():
    assert multiply(3, 4) == 12


# ── Bug 1: divide uses * instead of / ─────────────────────────────────────────

def test_divide_basic():
    """10 / 2 should be 5.0, not 20."""
    assert divide(10, 2) == pytest.approx(5.0)


def test_divide_floats():
    """7 / 2 should be 3.5."""
    assert divide(7, 2) == pytest.approx(3.5)


def test_divide_by_zero_raises():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(5, 0)


# ── Bug 2: square_root missing `import math` ──────────────────────────────────

def test_square_root_perfect():
    """sqrt(9) should be 3.0."""
    assert square_root(9) == pytest.approx(3.0)


def test_square_root_float():
    """sqrt(2.25) should be 1.5."""
    assert square_root(2.25) == pytest.approx(1.5)


def test_square_root_negative_raises():
    with pytest.raises(ValueError, match="negative"):
        square_root(-1)


# ── Bug 3: factorial missing base case → RecursionError ───────────────────────

def test_factorial_zero():
    """0! should be 1."""
    assert factorial(0) == 1


def test_factorial_one():
    """1! should be 1."""
    assert factorial(1) == 1


def test_factorial_five():
    """5! should be 120."""
    assert factorial(5) == 120


def test_factorial_negative_raises():
    """Negative input should raise ValueError."""
    with pytest.raises((ValueError, RecursionError)):
        factorial(-1)
