"""
AI Security Scanner — the core brain of PatchWatch.

Uses LangChain with two models via NVIDIA API:
  1. MiniMax M2.7 (primary) — reasoning model for deep security analysis
  2. Qwen 3 Coder (secondary) — code-focused, catches code-level vulns

Both are called per file, results are merged and deduplicated.
"""

import json
import hashlib
import asyncio
import re
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.config import get_settings

settings = get_settings()

# ── LangChain LLM Clients ─────────────────────────────────────

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

minimax_llm = ChatOpenAI(
    api_key=settings.minimax_api_key,
    base_url=NVIDIA_BASE_URL,
    model="minimax/minimax-m2.7",
    temperature=0.1,
    max_tokens=4096,
) if settings.minimax_api_key and not settings.minimax_api_key.startswith("your_") else None

qwen_llm = ChatOpenAI(
    api_key=settings.openrouter_api_key,
    base_url=NVIDIA_BASE_URL,
    model="qwen/qwen3-coder",
    temperature=0.1,
    max_tokens=4096,
) if settings.openrouter_api_key and not settings.openrouter_api_key.startswith("your_") else None


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

async def _scan_with_model(llm: ChatOpenAI, model_name: str, filename: str,
                           changed_lines: str, context: Optional[str] = None) -> list[dict]:
    """Scan a file using a LangChain ChatOpenAI model."""
    if not llm:
        return []

    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_build_file_prompt(filename, changed_lines, context)),
        ]

        response = await llm.ainvoke(messages)
        return _parse_llm_response(response.content, filename)

    except Exception as e:
        print(f"[{model_name}] Error scanning {filename}: {e}")
        return []


def _parse_llm_response(content: str, fallback_filename: str) -> list[dict]:
    """Parse the LLM JSON response, handling common formatting issues."""
    if not content:
        return []

    # Strip thinking tags if present (reasoning models)
    content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else content

    # Direct JSON parse
    try:
        result = json.loads(content)
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        pass

    # Extract JSON array from mixed content
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
    severity_order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}

    for vuln in all_vulns:
        vid = _generate_vuln_id(vuln)
        vuln["id"] = vid

        if vid not in seen:
            seen[vid] = vuln
        else:
            existing_sev = severity_order.get(seen[vid].get("severity", "info"), 0)
            new_sev = severity_order.get(vuln.get("severity", "info"), 0)
            if new_sev > existing_sev:
                seen[vid] = vuln

    return list(seen.values())


async def scan_file(filename: str, changed_lines: str,
                    previous_context: Optional[str] = None) -> list[dict]:
    """Scan a single file with both AI models in parallel, merge and deduplicate."""
    minimax_task = _scan_with_model(minimax_llm, "MiniMax", filename, changed_lines, previous_context)
    qwen_task = _scan_with_model(qwen_llm, "Qwen", filename, changed_lines, previous_context)

    minimax_results, qwen_results = await asyncio.gather(minimax_task, qwen_task)

    all_vulns = minimax_results + qwen_results
    return _deduplicate_vulns(all_vulns)


async def scan_commit(files: list[dict], previous_context: Optional[str] = None) -> list[dict]:
    """
    Scan all files from a commit.
    Files are processed sequentially to respect rate limits,
    but both models run in parallel per file.
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
