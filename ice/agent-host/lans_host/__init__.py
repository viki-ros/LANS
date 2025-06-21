"""
LANS ICE Agent Host

Backend service providing system access and real-time communication
for the LANS Integrated Cognitive Environment desktop application.
"""

__version__ = "0.1.0"
__author__ = "LANS Team"

from .main import app

__all__ = ["app"]
