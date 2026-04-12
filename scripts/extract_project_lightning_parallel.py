# ruff: noqa: E501
import concurrent.futures
import os
import pathlib
import sys

# Ensure we can import scripts.ollama_kb from the root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from scripts.ollama_kb import MODELS, generate
except ImportError:
    print("Error: Could not import ollama_kb. Make sure you run this from the repo root.")
    sys.exit(1)

VAULT_RAW = pathlib.Path("vault/raw/articles")
VAULT_WIKI = pathlib.Path("vault/wiki/analyses")
VAULT_WIKI.mkdir(parents=True, exist_ok=True)

PROMPT_TEMPLATE = """You are a marine transport program manager for the UAE HVDC project.
Analyze the following WhatsApp chat log (Project Lightning) and extract the core logistics issue or event.
Write a structured "Lessons Learned" or "Issue Report" in Korean.
You MUST include YAML frontmatter at the very top of your response exactly like this:
---
slug: {slug}
title: <Korean Title Summarizing the Issue>
tags: [LogisticsIssue, ProjectLightning, <Site/Hub/Vessel name like MOSB, Das Island, etc.>, <IssueType like delay, weather, hold, etc.>]
---

Body of the markdown should include:
## 이슈 개요 (Issue Overview)
...

## 타임라인 (Timeline)
...

## 해결/조치 (Resolution/Action)
...

Make sure to mask any personal names or phone numbers (e.g., Manager A, Driver B).

Raw Chat Log:
{raw_text}
"""


def process_file(file_path):
    slug = file_path.stem
    wiki_path = VAULT_WIKI / f"{slug}.md"

    if wiki_path.exists():
        print(f"Skipping {slug}, wiki note already exists.")
        return slug, True

    print(f"Processing {slug} via Ollama...")
    raw_text = file_path.read_text(encoding="utf-8")

    prompt = PROMPT_TEMPLATE.format(
        slug=slug, raw_text=raw_text[:4000]
    )  # Limit to 4000 chars to avoid context overflow

    messages = [
        {
            "role": "system",
            "content": "You are a logistics expert. Respond only with the requested Markdown and YAML frontmatter.",  # noqa: E501
        },
        {"role": "user", "content": prompt},
    ]

    try:
        # Call local LLM (gemma4)
        response_text = generate(messages=messages, model=MODELS["primary"])
        wiki_path.write_text(response_text, encoding="utf-8")
        print(f"Successfully generated wiki note for {slug}")
        return slug, True
    except Exception as e:
        print(f"Error processing {slug}: {e}")
        return slug, False


def main():
    target_files = list(VAULT_RAW.glob("logistics_issue_project_lightning_*.md"))
    if not target_files:
        print("No raw event files found for Project Lightning.")
        return

    print(
        f"Found {len(target_files)} files. Starting parallel processing using Local LLM (Ollama)..."
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_file, p): p for p in target_files}
        for future in concurrent.futures.as_completed(futures):
            slug, success = future.result()
            if not success:
                print(f"Failed to process {slug}")


if __name__ == "__main__":
    main()
