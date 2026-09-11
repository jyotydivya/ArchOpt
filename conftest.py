"""
conftest.py — pytest configuration for the ArchOpt project.
Ensures the repo root is on sys.path so imports work from any test.
"""
import sys
import os

# Add repo root so `contracts` and `optimization` are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
