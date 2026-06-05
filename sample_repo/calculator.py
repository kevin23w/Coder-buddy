"""
calculator.py — intentionally buggy calculator module.

Bugs introduced for Coder Buddy demo:
  1. divide()    → uses * instead of /  (line ~14)
  2. square_root() → missing `import math` (line ~22)
  3. factorial() → missing base case → infinite recursion (line ~30)
"""


def add(a: float, b: float) -> float:
    """Return the sum of a and b."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Return a minus b."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Return the product of a and b."""
    return a * b


def divide(a: float, b: float) -> float:
    """
    Return a divided by b.
    BUG: uses multiplication (*) instead of division (/).
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a * b  # BUG: should be a / b


def square_root(n: float) -> float:
    """
    Return the square root of n.
    BUG: `import math` is missing from this file.
    """
    if n < 0:
        raise ValueError("Cannot take square root of a negative number")
    return math.sqrt(n)  # BUG: math is not imported


def factorial(n: int) -> int:
    """
    Return n! (n factorial).
    BUG: missing base case — causes infinite recursion for n <= 0.
    """
    # BUG: should have: if n == 0: return 1
    return n * factorial(n - 1)
