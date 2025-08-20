#!/usr/bin/env python3
"""
Demo script showing Enhanced Auto-Fix capabilities
This file intentionally contains various issues to demonstrate fixes
"""

import os

# This function has issues that auto-fix will detect and improve


def demo_function(name):
    print("Hello " + name)  # Should use logging and f-strings
    var x = 5  # Invalid syntax
    return x

# Function without docstring


def another_function():
    return "test"


class TestClass:
    def method(self):
        return True


# Hardcoded values that could be environment variables
API_KEY = "hardcoded_key_12345"
PASSWORD = "secret_password"

if __name__ == "__main__":
    demo_function("World")
