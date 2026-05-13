"""
AI Security Scanner — the core brain of PatchWatch.

Uses two models:
  1. MiniMax M2.7 (primary) — reasoning model, great for deep security analysis
  2. Qwen 3 Coder via OpenRouter (secondary) — code-focused, catches code-level vulns

Both are called per file, results are merged and deduplicated.
"""

import json
import hashlib
from typing import Optional
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()

# ── AI Clients ─────────────────────────────────────────────────

minimax_client = AsyncOpenAI(
    api_key=settings.minimax_api_key,
    base_url="https://api.minimax.io/v1",
) if settings.minimax_api_key else None

qwen_client = AsyncOpenAI(
    api_key=settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
) if settings.openrouter_api_key else None


# ── Prompts ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are PatchWatch, an expert security code reviewer. You analyze code diffs (git patches) and identify security vulnerabilities.

Your job:
1. Analyze the changed code for security issues
2. Focus ONLY on real, actionable vulnerabilities — not style issues
3. For each vulnerability found, provide structured JSON output

Categories to check:
- Hardcoded secrets (API keys, passwords, tokens in code)
- SQL injection
- XSS (Cross-Site Scripting)
- Command injection
- Path traversal
- Insecure deserialization
- Insecure cryptography (weak hashing, no salt, etc.)
- Authentication/authorization flaws
- Exposed sensitive data in logs
- Insecure HTTP (missing HTTPS, no TLS verification)
- SSRF (Server-Side Request Forgery)
- Race conditions
- Insecure file operations
- Missing input validation
- Dependency vulnerabilities (known CVEs in imports)

Severity levels: critical, high, medium, low, info

IMPORTANT: Return ONLY a JSON array. No markdown, no explanation outside JSON.
If no vulnerabilities found, return an empty array: []

Each vulnerability object must have:
{
  "severity": "critical|high|medium|low|info",
  "category": "Category Name",
  "file": "filename",
  "line": line_number_or_null,
  "description": "Clear description of the vulnerability",
  "recommendation": "How to fix it",
  "code_snippet": "the problematic code line(s)"
}"""

CONTEXT_PROMPT_TEMPLATE = """Previous scan context for this repo+branch:
{previous_summary}

Known existing issues:
{existing_issues}

When analyzing, note if any issue is NEW (introduced in this commit) vs RECURRING (already existed)."""


def _build_file_prompt(filename: str, changed_lines: str, previous_context: Optional[str] = None) -> str:
    """Build the user prompt for scanning a single file."""
    prompt = f"""Analyze this code diff for security vulnerabilities.

**File:** `{filename}`

**Changed Code (diff):**
```
{changed_lines}
```

Return a JSON array of vulnerabilities found. If none, return [].
"""
    if previous_context:
        prompt = f"""{previous_context}

---

{prompt}"""

    return prompt


# ── Scanning Logic ─────────────────────────────────────────────

async def _scan_with_minimax(filename: str, changed_lines: str, context: Optional[str] = None) -> list[dict]:
    """Scan a file using MiniMax M2.7."""
    if not minimax_client:
        return []

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_file_prompt(filename, changed_lines, context)},
        ]

        response = await minimax_client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=messages,
            temperature=0.1,  # low temp for consistent analysis
        )

        content = response.choices[0].message.content
        return _parse_llm_response(content, filename)

    except Exception as e:
        print(f"[MiniMax] Error scanning {filename}: {e}")
        return []


async def _scan_with_qwen(filename: str, changed_lines: str, context: Optional[str] = None) -> list[dict]:
    """Scan a file using Qwen 3 Coder via OpenRouter."""
    if not qwen_client:
        return []

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_file_prompt(filename, changed_lines, context)},
        ]

        response = await qwen_client.chat.completions.create(
            model="qwen/qwen3-coder",
            messages=messages,
            temperature=0.1,
        )

        content = response.choices[0].message.content
        return _parse_llm_response(content, filename)

    except Exception as e:
        print(f"[Qwen] Error scanning {filename}: {e}")
        return []


def _parse_llm_response(content: str, fallback_filename: str) -> list[dict]:
    """Parse the LLM JSON response, handling common formatting issues."""
    if not content:
        return []

    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith("```"):
        # Remove ```json ... ``` wrapper
        lines = content.split("\n")
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else content

    # Try to find JSON array in the response
    try:
        # Direct parse
        result = json.loads(content)
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array from mixed content
    import re
    match = re.search(r'\[[\s\S]*\]', content)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []


def _generate_vuln_id(vuln: dict) -> str:
    """Generate a unique fingerprint for a vulnerability."""
    key = f"{vuln.get('category', '')}-{vuln.get('file', '')}-{vuln.get('line', '')}-{vuln.get('description', '')[:50]}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def _deduplicate_vulns(all_vulns: list[dict]) -> list[dict]:
    """Merge results from multiple models, removing duplicates."""
    seen = {}

    for vuln in all_vulns:
        vid = _generate_vuln_id(vuln)
        vuln["id"] = vid

        if vid not in seen:
            seen[vid] = vuln
        else:
            # If duplicate, keep the one with higher severity
            severity_order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
            existing_sev = severity_order.get(seen[vid].get("severity", "info"), 0)
            new_sev = severity_order.get(vuln.get("severity", "info"), 0)
            if new_sev > existing_sev:
                seen[vid] = vuln

    return list(seen.values())


async def scan_file(
    filename: str,
    changed_lines: str,
    previous_context: Optional[str] = None,
) -> list[dict]:
    """
    Scan a single file with both AI models, merge and deduplicate results.
    """
    import asyncio

    # Run both models in parallel
    minimax_task = _scan_with_minimax(filename, changed_lines, previous_context)
    qwen_task = _scan_with_qwen(filename, changed_lines, previous_context)

    minimax_results, qwen_results = await asyncio.gather(minimax_task, qwen_task)

    # Merge and deduplicate
    all_vulns = minimax_results + qwen_results
    return _deduplicate_vulns(all_vulns)


async def scan_commit(
    files: list[dict],
    previous_context: Optional[str] = None,
) -> list[dict]:
    """
    Scan all files from a commit. Processes files sequentially to avoid
    rate limits, but uses both models in parallel per file.
    """
    all_vulnerabilities = []

    for file_info in files:
        vulns = await scan_file(
            filename=file_info["filename"],
            changed_lines=file_info["changed_lines"],
            previous_context=previous_context,
        )
        all_vulnerabilities.extend(vulns)

    return all_vulnerabilities
