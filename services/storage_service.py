from pathlib import Path


OUTPUT_DIR = Path('generated')
OUTPUT_DIR.mkdir(exist_ok=True)


def make_file_path(filename: str) -> Path:
    return OUTPUT_DIR / filename
 