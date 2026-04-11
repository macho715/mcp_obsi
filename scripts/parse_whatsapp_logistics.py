import os
import pathlib
import re
import sys
from datetime import datetime, timedelta

# Ensure we can import scripts.ollama_kb from the root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from scripts.ollama_kb import MODELS, generate
except ImportError:
    print("Error: Could not import ollama_kb. Make sure you run this from the repo root.")
    sys.exit(1)

LOGS_DIR = pathlib.Path("whatsapp groupchat/대화")
VAULT_RAW = pathlib.Path("vault/raw/articles")
VAULT_WIKI = pathlib.Path("vault/wiki/analyses")

VAULT_RAW.mkdir(parents=True, exist_ok=True)
VAULT_WIKI.mkdir(parents=True, exist_ok=True)

CHANNELS = {
    "Abu Dhabi": {
        "pattern": "*Abu Dhabi Logistics*",
        "slug_prefix": "abu_dhabi",
        "tags": ["analysis", "logistics", "abu_dhabi", "hub", "coordination"],
        "persona": "You are the central control tower coordinator for the UAE HVDC project."
    },
    "DSV Delivery": {
        "pattern": "*DSV Delivery*",
        "slug_prefix": "dsv_delivery",
        "tags": ["analysis", "logistics", "dsv", "inland", "warehouse"],
        "persona": "You are an inland transport and warehouse coordinator for the UAE HVDC project."
    },
    "Project Lightning": {
        "pattern": "*Project Lightning*",
        "slug_prefix": "project_lightning",
        "tags": ["analysis", "logistics", "lightning", "marine", "program"],
        "persona": "You are a marine transport program manager for the UAE HVDC project."
    },
    "Jopetwil 71 Group": {
        "pattern": "*Jopetwil 71 Group*",
        "slug_prefix": "jpt71",
        "tags": ["analysis", "logistics", "jpt71", "barge", "port"],
        "persona": "You are a specialized barge and port operations coordinator for the UAE HVDC project."
    },
    "MIR Logistics": {
        "pattern": "*MIR Logistics*",
        "slug_prefix": "mir",
        "tags": ["analysis", "logistics", "mir", "site", "indoor"],
        "persona": "You are a site logistics coordinator at the MIR site for the UAE HVDC project."
    },
    "SHU Logistics": {
        "pattern": "*SHU Logistics*",
        "slug_prefix": "shu",
        "tags": ["analysis", "logistics", "shu", "site", "inspection"],
        "persona": "You are a site logistics and inspection coordinator at the SHU site for the UAE HVDC project."
    }
}

STANDARD_TAGS = [
    r"\[URGENT\]", r"\[ACTION\]", r"\[FYI\]", r"\[ETA\]", r"\[RISK\]", 
    r"\[COST\]", r"\[GATE\]", r"\[CRANE\]", r"\[MANIFEST\]"
]
PRE_CONSTRAINTS = [
    r"D-1 16:00 Planning", r"Hold at DSV", r"weather", r"tide", r"fog"
]
FALLBACK_KEYWORDS = [
    r"delay", r"hold", r"cancel", r"terminated", r"problem", r"issue", r"damage", r"mismatch", r"congestion", r"closed"
]

ALL_KEYWORDS = STANDARD_TAGS + PRE_CONSTRAINTS + FALLBACK_KEYWORDS
KEYWORD_REGEX = re.compile(r"(" + "|".join(ALL_KEYWORDS) + r")", re.IGNORECASE)

LOG_PATTERN = re.compile(r"^(\d{2}/\d{1,2}/\d{1,2})\s+(AM|PM|오전|오후)\s+(\d{1,2}:\d{2})\s+-\s+([^:]+):\s+(.*)$")

def parse_date(date_str, am_pm, time_str):
    parts = date_str.split('/')
    if len(parts) == 3:
        year = int(parts[0]) + 2000
        month = int(parts[1])
        day = int(parts[2])
    else:
        return None

    time_parts = time_str.split(':')
    if len(time_parts) == 2:
        hour = int(time_parts[0])
        minute = int(time_parts[1])
    else:
        return None

    if am_pm in ("PM", "오후") and hour < 12:
        hour += 12
    if am_pm in ("AM", "오전") and hour == 12:
        hour = 0

    try:
        return datetime(year, month, day, hour, minute)
    except ValueError:
        return None

def extract_events(file_path):
    print(f"Reading log file: {file_path}")
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    messages = []
    current_msg = None

    for line in lines:
        match = LOG_PATTERN.match(line)
        if match:
            if current_msg:
                messages.append(current_msg)
            date_str, am_pm, time_str, sender, content = match.groups()
            dt = parse_date(date_str, am_pm, time_str)
            if dt:
                current_msg = {"timestamp": dt, "sender": sender.strip(), "content": content.strip(), "raw": line}
            else:
                current_msg = None
        else:
            if current_msg:
                current_msg["content"] += "\n" + line.strip()
                current_msg["raw"] += line
    
    if current_msg:
        messages.append(current_msg)

    print(f"Parsed {len(messages)} valid messages.")
    
    hits = []
    for i, msg in enumerate(messages):
        if KEYWORD_REGEX.search(msg["content"]):
            hits.append(i)

    print(f"Found {len(hits)} messages containing risk/event keywords.")

    events = []
    current_event = []
    
    for idx in hits:
        msg = messages[idx]
        if not current_event:
            current_event.append(idx)
        else:
            last_idx = current_event[-1]
            time_diff = msg["timestamp"] - messages[last_idx]["timestamp"]
            if time_diff <= timedelta(hours=2):
                current_event.append(idx)
            else:
                events.append(current_event)
                current_event = [idx]
    
    if current_event:
        events.append(current_event)

    print(f"Grouped into {len(events)} distinct event blocks.")

    event_blocks = []
    for ev in events:
        start_time = messages[ev[0]]["timestamp"] - timedelta(hours=2)
        end_time = messages[ev[-1]]["timestamp"] + timedelta(hours=2)
        block_msgs = [m for m in messages if start_time <= m["timestamp"] <= end_time]
        
        event_blocks.append({
            "start": start_time,
            "end": end_time,
            "messages": block_msgs
        })

    return event_blocks

def process_event(block, index, channel_info):
    start_date = block["start"].strftime("%Y-%m-%d")
    slug_prefix = channel_info["slug_prefix"]
    slug = f"logistics_issue_{slug_prefix}_{start_date}_{index}"
    raw_id = f"convo-{slug}"

    # 1. Save raw block
    raw_text = "".join([m["raw"] for m in block["messages"]])
    raw_path = VAULT_RAW / f"{slug}.md"
    
    raw_frontmatter = f"---\nslug: {slug}\ndate: {start_date}\nsource: whatsapp_{slug_prefix}\nmcp_id: {raw_id}\n---\n\n"
    raw_path.write_text(raw_frontmatter + raw_text, encoding="utf-8")

    # 2. Call LLM for structuring (Skipped - LLM takes too long, delegating to Assistant in parallel)
    # print(f"[{index}] Calling Ollama for event on {start_date} ({slug_prefix})...")
    # try:
    #     body = generate(messages=prompt, model=MODELS["primary"])
    # except Exception as e:
    #     print(f"[{index}] Ollama call failed: {e}")
    #     return

    # 3. Write Wiki Note (Skipped, will be done by subagents)
    print(f"[{index}] Saved raw event to {raw_path}. Delegation pending.")

def main():
    if not LOGS_DIR.exists():
        print(f"Logs directory not found: {LOGS_DIR}")
        return

    print("Starting full batch processing for all defined channels...")
    
    for channel_name, info in CHANNELS.items():
        pattern = info["pattern"]
        matched_files = list(LOGS_DIR.glob(pattern))
        if not matched_files:
            print(f"No log files found for channel '{channel_name}' matching '{pattern}'.")
            continue
            
        for file_path in matched_files:
            print(f"\n--- Processing Channel: {channel_name} | File: {file_path.name} ---")
            blocks = extract_events(file_path)
            if not blocks:
                print(f"No events extracted for {file_path.name}")
                continue
                
            # No MAX_TO_PROCESS limit, process everything (Modified: Limited to 1 per channel to test parallel assistant delegation)
            MAX_TO_PROCESS = 10
            print(f"Processing {MAX_TO_PROCESS} event block(s) for delegation...")
            for i, block in enumerate(blocks[:MAX_TO_PROCESS]):
                process_event(block, i + 1, info)
                
    print("\nBatch extraction complete.")

if __name__ == "__main__":
    main()
