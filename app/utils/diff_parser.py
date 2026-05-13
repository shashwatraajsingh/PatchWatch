"""
Diff Parser — extracts meaningful changed code from GitHub patch data.
Filters out noise (lock files, images, etc.) and returns only security-relevant diffs.
"""

import re
from typing import Optional

# File extensions worth scanning for security issues
SCANNABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb",
    ".php", ".c", ".cpp", ".h", ".cs", ".swift", ".kt",
    ".sql", ".sh", ".bash", ".zsh",
    ".yaml", ".yml", ".toml", ".json", ".xml",
    ".env", ".cfg", ".ini", ".conf",
    ".dockerfile", ".tf", ".hcl",
}

# Files to always skip
SKIP_PATTERNS = [
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"pnpm-lock\.yaml$",
    r"Pipfile\.lock$",
    r"poetry\.lock$",
    r"\.min\.js$",
    r"\.min\.css$",
    r"\.map$",
    r"\.svg$",
    r"\.png$",
    r"\.jpg$",
    r"\.jpeg$",
    r"\.gif$",
    r"\.ico$",
    r"\.woff",
    r"\.ttf$",
    r"\.eot$",
    r"dist/",
    r"build/",
    r"node_modules/",
    r"__pycache__/",
    r"\.git/",
]


def should_scan_file(filename: str) -> bool:
    """Check if a file is worth scanning based on extension and skip patterns."""
    # Skip known noise files
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, filename):
            return False

    # Check if extension is scannable
    for ext in SCANNABLE_EXTENSIONS:
        if filename.endswith(ext):
            return True

    # Also scan files with no extension (could be scripts, Dockerfiles, etc.)
    if "." not in filename.split("/")[-1]:
        return True

    return False


def extract_changed_lines(patch: str) -> str:
    """
    From a unified diff patch, extract only the added/modified lines
    with their context. Returns a clean string for LLM consumption.
    """
    if not patch:
        return ""

    lines = patch.split("\n")
    result = []
    current_section = None

    for line in lines:
        # Capture hunk headers for context (line numbers)
        if line.startswith("@@"):
            current_section = line
            result.append(f"\n{line}")
        elif line.startswith("+") and not line.startswith("+++"):
            # Added line — this is what we care about most
            result.append(line)
        elif line.startswith("-") and not line.startswith("---"):
            # Removed line — still useful for context (what was replaced)
            result.append(line)
        elif not line.startswith("\\"):
            # Context line — keep for understanding surrounding code
            result.append(f" {line.lstrip()}" if line.strip() else "")

    return "\n".join(result)


def parse_commit_files(files_data: list[dict]) -> list[dict]:
    """
    Parse GitHub API commit files response into a clean list of diffs.
    Returns only scannable files with their extracted changes.
    """
    parsed = []

    for file_info in files_data:
        filename = file_info.get("filename", "")
        if not should_scan_file(filename):
            continue

        patch = file_info.get("patch", "")
        if not patch:
            continue

        changed_lines = extract_changed_lines(patch)
        if not changed_lines.strip():
            continue

        parsed.append({
            "filename": filename,
            "status": file_info.get("status", "modified"),  # added, modified, removed
            "additions": file_info.get("additions", 0),
            "deletions": file_info.get("deletions", 0),
            "patch": patch,
            "changed_lines": changed_lines,
        })

    return parsed


def prioritize_files(files: list[dict]) -> list[dict]:
    """
    Sort files by security risk — config files, auth-related files,
    and env files go first.
    """
    HIGH_RISK_PATTERNS = [
        r"\.env",
        r"config",
        r"auth",
        r"secret",
        r"password",
        r"credential",
        r"token",
        r"key",
        r"security",
        r"permission",
        r"middleware",
        r"docker",
        r"\.sql",
        r"migration",
    ]

    def risk_score(file_info: dict) -> int:
        name = file_info["filename"].lower()
        score = 0
        for pattern in HIGH_RISK_PATTERNS:
            if re.search(pattern, name):
                score += 10
        # More additions = more new code to review
        score += min(file_info.get("additions", 0), 20)
        return score

    return sorted(files, key=risk_score, reverse=True)
