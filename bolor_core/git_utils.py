from pathlib import Path
from typing import List, Tuple


def apply_patch(file_path: Path, suggestions: List[Tuple[int, str, str]]):
    """
    Apply suggested fixes directly to the file by inserting lines above the reported issue.

    Args:
        file_path: Path to the Python file
        suggestions: List of (line, message, fix) tuples
    """
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Sort fixes in reverse line order so we don't mess up indexing
    suggestions = sorted(suggestions, key=lambda x: x[0], reverse=True)

    for line_number, _, fix in suggestions:
        insertion = fix + "\n"
        if 0 <= line_number - 1 < len(lines):
            lines.insert(line_number - 1, insertion)

    # Backup original
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    file_path.rename(backup_path)

    with open(file_path, "w") as f:
        f.writelines(lines)

    print(f"🛠️ Patch applied. Original saved as {backup_path.name}")
