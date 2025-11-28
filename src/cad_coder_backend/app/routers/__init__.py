"""
Router package initialization for CAD-Coder.
Contains API endpoints for generation, history, health, and authentication.
"""
from . import generate, history, health, auth

__all__ = ["generate", "history", "health", "auth"]