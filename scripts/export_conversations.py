import os
import json
import re
import sys
from datetime import datetime

def clean_user_content(content):
    if not content:
        return ""
    # Extract content inside <USER_REQUEST> tags if present
    match = re.search(r'<USER_REQUEST>(.*?)</USER_REQUEST>', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return content.strip()

def make_safe_filename(text):
    # Remove non-alphanumeric characters, spaces to underscores
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)  # remove tags
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '_', text)
    return text[:50].strip('_')

def main():
    brain_dir = "/Users/evapaula/.gemini/antigravity-ide/brain"
    project_dir = "/Users/evapaula/mba_thesis"
    export_dir = os.path.join(project_dir, "docs", "conversations")
    
    if not os.path.exists(brain_dir):
        print(f"Error: Brain directory not found at {brain_dir}")
        sys.exit(1)
        
    os.makedirs(export_dir, exist_ok=True)
    print(f"Exporting conversations to: {export_dir}")
    
    conversations = []
    
    for uuid_folder in os.listdir(brain_dir):
        folder_path = os.path.join(brain_dir, uuid_folder)
        if not os.path.isdir(folder_path):
            continue
            
        transcript_path = os.path.join(folder_path, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(transcript_path):
            continue
            
        print(f"Processing conversation {uuid_folder}...")
        
        turns = []
        first_timestamp = None
        
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        step = json.loads(line)
                        source = step.get("source")
                        step_type = step.get("type")
                        content = step.get("content")
                        created_at = step.get("created_at")
                        
                        if not first_timestamp and created_at:
                            first_timestamp = created_at
                            
                        # Capture User Inputs
                        if source == "USER_EXPLICIT" and step_type == "USER_INPUT":
                            cleaned = clean_user_content(content)
                            if cleaned:
                                turns.append({
                                    "role": "user",
                                    "content": cleaned,
                                    "timestamp": created_at
                                })
                        
                        # Capture Model Answers
                        elif source == "MODEL" and step_type in ["PLANNER_RESPONSE", "GENERIC"]:
                            if content and content.strip():
                                turns.append({
                                    "role": "assistant",
                                    "content": content.strip(),
                                    "timestamp": created_at
                                })
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"  Error reading {transcript_path}: {e}")
            continue
            
        if not turns:
            print(f"  Skipping {uuid_folder}: no messages found.")
            continue
            
        # Parse timestamp for ordering
        dt = None
        if first_timestamp:
            try:
                # e.g., 2026-06-19T10:52:56Z
                dt = datetime.strptime(first_timestamp.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass
                
        # Generate Title from first user turn
        first_user_turn = next((t for t in turns if t["role"] == "user"), None)
        raw_title = "Untitled Conversation"
        if first_user_turn:
            # Get first line of text
            first_line = first_user_turn["content"].split("\n")[0].strip()
            if first_line:
                raw_title = first_line[:80]
                if len(first_user_turn["content"]) > 80:
                    raw_title += "..."
                    
        safe_title = make_safe_filename(raw_title) or "conversation"
        date_prefix = dt.strftime("%Y-%m-%d") if dt else "unknown_date"
        filename = f"{date_prefix}_{safe_title}_{uuid_folder[:8]}.md"
        file_path = os.path.join(export_dir, filename)
        
        # Build Markdown content
        md_content = []
        md_content.append(f"# {raw_title}")
        md_content.append(f"**Date**: {first_timestamp or 'Unknown'}")
        md_content.append(f"**Conversation ID**: `{uuid_folder}`")
        md_content.append(f"**Total Messages**: {len(turns)}")
        md_content.append("\n---\n")
        
        for turn in turns:
            role_title = "User" if turn["role"] == "user" else "Antigravity (Assistant)"
            md_content.append(f"### 👤 {role_title}")
            if turn["timestamp"]:
                md_content.append(f"*{turn['timestamp']}*\n")
            md_content.append(turn["content"])
            md_content.append("\n---\n")
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_content))
            print(f"  Exported → {filename}")
            
            conversations.append({
                "uuid": uuid_folder,
                "title": raw_title,
                "filename": filename,
                "date": dt or datetime.min,
                "date_str": first_timestamp or "Unknown",
                "turns_count": len(turns)
            })
        except Exception as e:
            print(f"  Error writing {filename}: {e}")
            
    # Sort conversations by date (newest first)
    conversations.sort(key=lambda x: x["date"], reverse=True)
    
    # Write Index README.md
    readme_path = os.path.join(export_dir, "README.md")
    readme_content = []
    readme_content.append("# Exported Chat History")
    readme_content.append("This directory contains the chronological markdown exports of your assistant chats for this project.\n")
    readme_content.append("| Date | Conversation Title | Turns | File |")
    readme_content.append("| --- | --- | --- | --- |")
    
    for c in conversations:
        # Format links to be relative
        link = f"./{c['filename']}"
        date_display = c['date_str'][:10] if c['date_str'] != "Unknown" else "Unknown"
        title_display = c['title'].replace("|", "\\|")
        readme_content.append(f"| {date_display} | {title_display} | {c['turns_count']} | [{c['filename']}]({link}) |")
        
    try:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("\n".join(readme_content))
        print(f"\nCreated master index at: {readme_path}")
    except Exception as e:
        print(f"Error writing master README: {e}")

if __name__ == "__main__":
    main()
