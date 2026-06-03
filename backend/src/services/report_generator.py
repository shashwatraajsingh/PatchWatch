"""
Report Generator — creates structured markdown vulnerability reports.
"""

from datetime import datetime, timezone


def generate_severity_summary(vulnerabilities: list[dict]) -> dict:
    """Count vulnerabilities by severity level."""
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for v in vulnerabilities:
        sev = v.get("severity", "info").lower()
        if sev in summary:
            summary[sev] += 1
    return summary


def generate_natural_summary(repo: str, branch: str, commit_sha: str,
                              vulnerabilities: list[dict], comparison: dict) -> str:
    """Generate a natural language summary for memory storage."""
    total = len(vulnerabilities)
    severity = generate_severity_summary(vulnerabilities)
    new_count = len(comparison.get("new_issues", []))
    resolved_count = len(comparison.get("resolved_issues", []))
    recurring_count = len(comparison.get("recurring_issues", []))

    parts = [f"Commit {commit_sha[:8]} on {repo}/{branch}: {total} issue(s) found."]

    if severity["critical"] > 0:
        parts.append(f"{severity['critical']} CRITICAL.")
    if severity["high"] > 0:
        parts.append(f"{severity['high']} HIGH.")

    if new_count:
        parts.append(f"{new_count} new issue(s) introduced.")
    if resolved_count:
        parts.append(f"{resolved_count} issue(s) resolved.")
    if recurring_count:
        parts.append(f"{recurring_count} recurring issue(s).")

    return " ".join(parts)


def generate_markdown_report(repo: str, branch: str, commit_sha: str,
                              commit_message: str, author: str,
                              vulnerabilities: list[dict], comparison: dict,
                              files_scanned: int, scan_duration_ms: int) -> str:
    """Generate a full markdown vulnerability report."""
    severity = generate_severity_summary(vulnerabilities)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    new_issues = comparison.get("new_issues", [])
    resolved = comparison.get("resolved_issues", [])
    recurring = comparison.get("recurring_issues", [])

    # Header
    report = f"""# 🛡️ PatchWatch Security Report

| Field | Value |
|-------|-------|
| **Repository** | `{repo}` |
| **Branch** | `{branch}` |
| **Commit** | `{commit_sha[:8]}` |
| **Message** | {commit_message} |
| **Author** | {author} |
| **Scanned At** | {now} |
| **Files Scanned** | {files_scanned} |
| **Scan Duration** | {scan_duration_ms}ms |

---

## 📊 Severity Summary

| Critical | High | Medium | Low | Info |
|----------|------|--------|-----|------|
| {'🔴 ' + str(severity['critical']) if severity['critical'] else '✅ 0'} | {'🟠 ' + str(severity['high']) if severity['high'] else '✅ 0'} | {'🟡 ' + str(severity['medium']) if severity['medium'] else '✅ 0'} | {'🔵 ' + str(severity['low']) if severity['low'] else '✅ 0'} | {'⚪ ' + str(severity['info']) if severity['info'] else '0'} |

"""

    # Comparison section
    if new_issues or resolved or recurring:
        report += "## 🔄 Changes Since Last Scan\n\n"
        if new_issues:
            report += f"- 🆕 **{len(new_issues)} new issue(s)** introduced in this commit\n"
        if resolved:
            report += f"- ✅ **{len(resolved)} issue(s) resolved** since last commit\n"
        if recurring:
            report += f"- 🔁 **{len(recurring)} recurring issue(s)** still present\n"
        report += "\n---\n\n"

    # Vulnerabilities detail
    if not vulnerabilities:
        report += "## ✅ No Vulnerabilities Found\n\nThis commit looks clean! No security issues detected.\n"
        return report

    report += "## 🔍 Vulnerabilities Found\n\n"

    # Group by severity
    for sev_level in ["critical", "high", "medium", "low", "info"]:
        sev_vulns = [v for v in vulnerabilities if v.get("severity", "").lower() == sev_level]
        if not sev_vulns:
            continue

        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}
        report += f"### {icon.get(sev_level, '')} {sev_level.upper()}\n\n"

        for v in sev_vulns:
            is_new = v.get("id", "") in {i.get("id", "") for i in new_issues}
            tag = " `🆕 NEW`" if is_new else ""

            report += f"**{v.get('category', 'Unknown')}** — `{v.get('file', '?')}`{tag}\n\n"
            report += f"> {v.get('description', 'No description')}\n\n"

            if v.get("code_snippet"):
                report += f"```\n{v['code_snippet']}\n```\n\n"

            report += f"**Fix:** {v.get('recommendation', 'N/A')}\n\n---\n\n"

    return report
