#!/usr/bin/env python3
# 🌊 WARPCORE Launcher - Compact with swag
import sys, os
from pathlib import Path

print("🌊 WARPCORE")
os.chdir(Path(__file__).parent / "src")
sys.path.insert(0, ".")

exec(open("../start_warpcore.py").read())