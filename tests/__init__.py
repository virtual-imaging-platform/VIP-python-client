"""
Tests for the VIP Python Client
"""

# Import classes and packages to secure the namespace
import sys
from pathlib import Path
SOURCE_ROOT = str(Path(__file__).parents[1] / "src") # <=> /src/
sys.path.append(SOURCE_ROOT)
import vip_client