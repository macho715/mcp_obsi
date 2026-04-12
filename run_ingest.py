# ruff: noqa: E501
import json
import pathlib
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(".").absolute()))

from app.config import settings
from app.models import MemoryCreate, RawConversationCreate
from app.services.memory_store import MemoryStore
from scripts.ollama_kb import MODELS, generate, normalize_ascii_slug

files_to_process = [
    r"c:\Users\jichu\Downloads\mcp_obsidian\whatsapp groupchat\Guideline_Abu_Dhabi_Logistics.txt",  # noqa: E501
    r"c:\Users\jichu\Downloads\mcp_obsidian\whatsapp groupchat\Guideline_DSV_Delivery.txt",  # noqa: E501
    r"c:\Users\jichu\Downloads\mcp_obsidian\whatsapp groupchat\Guideline_HVDC_Project_Lightning.txt",  # noqa: E501
    r"c:\Users\jichu\Downloads\mcp_obsidian\whatsapp groupchat\Guideline_Jopetwil_71_Group.txt",  # noqa: E501
    r"c:\Users\jichu\Downloads\mcp_obsidian\whatsapp groupchat\Guideline_MIR_Logistics.txt",  # noqa: E501
    r"c:\Users\jichu\Downloads\mcp_obsidian\whatsapp groupchat\Guideline_SHU_Logistics.txt",
]

store = MemoryStore(vault_path=settings.vault_path, index_db_path=settings.index_db_path)
results = []
today = date.today().isoformat()

for file_path in files_to_process:
    p = pathlib.Path(file_path)
    if not p.exists():
        print(f"File not found: {file_path}")
        continue
    print(f"\nProcessing {p.name}...")
    input_text = p.read_text(encoding="utf-8")

    # Simple check on input length to not blow up Ollama context window
    # Actually, we'll slice [:4000] for classify but pass whole for extract
    slug = normalize_ascii_slug(p.stem)

    # 1a. Copy to vault/raw/articles/
    raw_path = pathlib.Path(f"vault/raw/articles/{slug}.md")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        f"---\nslug: {slug}\ndate: {today}\nsource: obsidian-ingest\n---\n\n{input_text}",
        encoding="utf-8",
    )
    print(f"  raw copy  : {raw_path}")

    # 1b. Archive raw via memory_store
    mcp_id = f"convo-ingest-{slug}-{today}"
    raw_payload = RawConversationCreate(
        mcp_id=mcp_id,
        source="obsidian-ingest",
        body_markdown=input_text,
        created_by="obsidian-ingest",
    )
    store.archive_raw_conversation(raw_payload)
    print(f"  raw id    : {mcp_id}")

    # 2. Classify
    classify_prompt = [
        {
            "role": "system",
            "content": (
                "You classify knowledge fragments for an Obsidian vault. "
                "Reply with exactly one JSON object: "
                '{"category": "<sources|concepts|entities|analyses>", '
                '"title": "<concise title, <=60 chars>", '
                '"summary": "<one sentence>", '
                '"tags": ["<tag1>", "<tag2>"]}'
            ),
        },
        {"role": "user", "content": f"Classify this:\n\n{input_text[:4000]}"},
    ]

    category = "sources"
    title = slug
    summary = "No summary provided."
    tags = []

    try:
        class_resp = generate(messages=classify_prompt, model=MODELS["primary"])
        start = class_resp.find("{")
        end = class_resp.rfind("}")
        if start != -1 and end != -1:
            classification = json.loads(class_resp[start : end + 1])
        else:
            classification = json.loads(class_resp)

        category = classification.get("category", "sources")
        if category not in ["sources", "concepts", "entities", "analyses"]:
            category = "sources"
        title = classification.get("title", slug)
        summary = classification.get("summary", summary)
        tags = classification.get("tags", [])
    except Exception as e:
        print(f"  Classification failed: {e}")

    # 3. Extract
    extract_prompt = [
        {
            "role": "system",
            "content": (
                "You are a structured knowledge-base compiler. "
                "Given source text, produce a clean Obsidian markdown note. "
                "Include: key facts, important quotes (with attribution), "
                "related concepts, open questions. "
                "Do not invent facts not present in the source."
            ),
        },
        {"role": "user", "content": input_text},
    ]
    try:
        body = generate(messages=extract_prompt, model=MODELS["primary"])
    except Exception as e:
        print(f"  Extraction failed: {e}")
        body = input_text

    # 4. Write wiki note
    wiki_path = pathlib.Path(f"vault/wiki/{category}/{slug}.md")
    wiki_path.parent.mkdir(parents=True, exist_ok=True)
    tags_json = json.dumps(tags, ensure_ascii=False)
    wiki_note_content = (
        f"---\n"
        f"note_kind: wiki\n"
        f"category: {category}\n"
        f"title: {title}\n"
        f"slug: {slug}\n"
        f"created: {today}\n"
        f"tags: {tags_json}\n"
        f"source_raw_id: {mcp_id}\n"
        f"---\n\n"
        f"{body}"
    )
    wiki_path.write_text(wiki_note_content, encoding="utf-8")
    print(f"  wiki note : {wiki_path}")

    # 5. Patch cross-links
    new_note_link = f"[[wiki/{category}/{slug}]]"
    for related_dir in ("vault/wiki/entities", "vault/wiki/concepts"):
        r_dir_path = pathlib.Path(related_dir)
        if not r_dir_path.exists():
            continue
        for related_path in r_dir_path.glob("*.md"):
            try:
                related_text = related_path.read_text(encoding="utf-8")
                # Need to be careful. The note title or stem could be short.
                if related_path.stem in body and new_note_link not in related_text:
                    related_text += f"\n\n## Related\n\n- {new_note_link}\n"
                    related_path.write_text(related_text, encoding="utf-8")
            except Exception:
                pass

    # 6. Update log and index
    log_path = pathlib.Path("vault/wiki/log.md")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_line = f"| {today} | ingest | {category}/{slug}.md | obsidian-ingest | {summary[:60]} |\n"
    try:
        if log_path.exists():
            with log_path.open("a", encoding="utf-8") as f:
                f.write(log_line)
        else:
            log_path.write_text(
                f"| Date | Action | Note | Source | Summary |\n|---|---|---|---|---|\n{log_line}",
                encoding="utf-8",
            )
    except Exception as e:
        print(f"  Log update failed: {e}")

    index_path = pathlib.Path("vault/wiki/index.md")
    new_link = f"- [[wiki/{category}/{slug}]]"
    try:
        if index_path.exists():
            idx_content = index_path.read_text(encoding="utf-8")
            if "## Recent Notes" in idx_content:
                idx_content = idx_content.replace("## Recent Notes", f"## Recent Notes\n{new_link}")
                index_path.write_text(idx_content, encoding="utf-8")
            else:
                index_path.write_text(
                    idx_content + f"\n\n## Recent Notes\n{new_link}\n", encoding="utf-8"
                )
        else:
            index_path.write_text(
                f"# Wiki Index\n\n## Recent Notes\n{new_link}\n", encoding="utf-8"
            )
        print("  log entry : vault/wiki/log.md + index.md updated")
    except Exception as e:
        print(f"  Index update failed: {e}")

    # 7. Create pointer memory note
    memory_content = f"{summary}\n\nSee [[wiki/{category}/{slug}]] for full details."
    mem_payload = MemoryCreate(
        title=f"KB: {title}",
        content=memory_content,
        source="obsidian-ingest",
        roles=["fact"],
        topics=tags,
        entities=[],
        projects=["mcp_obsidian"],
        tags=["kb", "wiki", category],
        raw_refs=[mcp_id],
    )

    try:
        mem_result = store.save(mem_payload)
        mem_id = mem_result["id"]
        print(f"  memory id : {mem_id}")
        results.append({"file": p.name, "mem_id": mem_id, "slug": slug})
    except Exception as e:
        print(f"  Save memory failed: {e}")

print("\n--- SUMMARY TABLE ---")
print("File | Memory ID | Slug")
print("---|---|---")
for r in results:
    print(f"{r['file']} | {r['mem_id']} | {r['slug']}")
