"""Runner for the NASA POWER climate download (long-running, RESUMABLE)."""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fetch", ROOT / "src" / "01_fetch_data.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["fetch"] = mod
spec.loader.exec_module(mod)
mod.fetch_nasa_power()
