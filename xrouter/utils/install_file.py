# import pydoc
from pathlib import Path

from rich import print


def install_text_file(
    path: str | Path,
    content: str,
    mode: str = "644",
    show_diff: bool = False,
    backup_path: Path | None = None,
):
    if isinstance(path, str):
        path = Path(path)

    print(f"Installing {path} with mode {mode}")

    has_diff, diff = check_file_diff(path, content, mode)
    if not has_diff:
        print(f"{path} is up to date")
        return

    if show_diff:
        # pydoc.pager(diff)
        print(diff)

    if backup_path:
        backup_file(path, backup_path)

    if not has_diff:
        return

    # Install the file
    path.write_text(content)
    path.chmod(int(mode, 8))


def install_template_file(
    path: str | Path,
    template_name: str,
    context: dict,
    mode: str = "644",
    show_diff: bool = False,
    backup_path: Path | None = None,
):
    from xrouter.utils.jinja import render

    content = render(template_name, context)

    install_text_file(path, content, mode, show_diff, backup_path)


def install_binary_file(
    path: str | Path,
    # source file path or source file content
    content: Path | bytes,
    mode: str = "644",
    show_diff: bool = False,
    backup_path: Path | None = None,
):
    if isinstance(path, str):
        path = Path(path)

    print(f"Installing {path} with mode {mode}")

    if isinstance(content, Path):
        content = content.read_bytes()

    has_diff, diff = check_file_diff(path, content, mode)
    if not has_diff:
        print(f"{path} is up to date")
        return

    if show_diff:
        # pydoc.pager(diff)
        print(diff)

    if backup_path:
        backup_file(path, backup_path)

    if not has_diff:
        return

    # Install the file
    path.write_bytes(content)
    path.chmod(int(mode, 8))


def check_file_diff(path: Path, content: str | bytes, mode: str) -> tuple[bool, str]:
    """
    Check difference between current content/mode and filesystem.

    * Generates content diff for text files, binary status for binary files
    * Includes file mode changes
    * Appends (current)/(new) suffixes to filenames
    * Returns empty diff if content and mode are identical

    Returns:
        tuple[bool, str]: A tuple containing:
            - bool: True if there are any changes, False otherwise
            - str: The formatted diff text, empty string if no changes
    """
    import difflib

    # Get current mode
    current_mode = oct(path.stat().st_mode)[-3:] if path.exists() else None

    # Show mode changes if different
    mode_diff = ""
    if current_mode != mode and current_mode is not None:
        mode_diff = f"mode change {current_mode} -> {mode}\n"

    # Handle binary vs text content
    if isinstance(content, bytes):
        try:
            current_binary_content = path.read_bytes() if path.exists() else b""
        except:
            current_binary_content = b""
        if current_binary_content == content:
            return False, ""
        diff = "Binary files differ\n"
    else:
        try:
            current_text_content = path.read_text() if path.exists() else ""
        except:
            current_text_content = ""
        if current_text_content == content:
            return False, ""

        diff = "".join(
            difflib.unified_diff(
                current_text_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                f"{path} (current)",
                f"{path} (new)",
            )
        )

    # Show combined diff through pager
    # if mode_diff or diff:
    #     pydoc.pager(mode_diff + diff)

    return True, mode_diff + diff


def backup_file(path: Path, backup_path: Path):
    """
    Backup the file to $backup_path/[segment1][segment2][filename].{time}.{suffix}

    For example, if path is /etc/sysctl.d/99-xrouter.conf, the backup file is:
    [etc][sysctl.d][99-xrouter.conf].{time}.conf

    $time is in format %Y%m%d%H%M%S%f
    """
    import shutil
    from datetime import datetime

    if not path.exists():
        return

    backup_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")

    # Get all path segments except root
    segments = [seg for seg in path.parts if seg not in ("", "/")]

    # The last segment is the filename
    *dir_segments, filename = segments

    # Get the suffix (including the dot, e.g. ".conf")
    suffix = path.suffix  # includes the dot, e.g. ".conf"
    suffix_no_dot = suffix[1:] if suffix.startswith(".") else suffix

    # Build backup filename: [dir1][dir2][filename].{timestamp}.{suffix}
    backup_name = "".join(f"[{seg}]" for seg in dir_segments + [filename])
    backup_name += f".{timestamp}"
    if suffix_no_dot:
        backup_name += f".{suffix_no_dot}"

    backup_file = backup_path / backup_name

    shutil.copy2(path, backup_file)
