"""Start the complete eBay scraper from Google Colab."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).parent / "run_colab.py"), run_name="__main__")
