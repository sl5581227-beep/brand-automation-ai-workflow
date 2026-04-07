"""
#!/usr/bin/env python3
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

OUT_DIR = Path("diagnostic_output")
OUT_DIR.mkdir(exist_ok=True)

report = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "python_version": sys.version,
    "files": [],
    "matches": {},
}

search_patterns = {
    "main_guard": re.compile(r"if\s+__name__\s*==\s*[\'\"]__main__[\'\"]"),
    "def_main": re.compile(r"def\s+main\s*\("),
    "whisper": re.compile(r"whispe?r", re.I),
    "ffmpeg": re.compile(r"ffmpeg", re.I),
    "tts": re.compile(r"tts|text-?to-?speech|eleven|coqui|vits", re.I),
    "clip": re.compile(r"clip|CLIP|VideoCLIP", re.I),
    "yolo": re.compile(r"yolo|detectron|yolov", re.I),
    "longxia_cn": re.compile(r"龙虾"),
    "longxia_en": re.compile(r"longxia|long-?xia", re.I),
    "subtitle": re.compile(r"subtitles?|srt|vtt|caption", re.I),
}

PY_EXT = ".py"

print("Starting diagnostic scan...\n")

for root, dirs, files in os.walk("."):
    for f in files:
        fp = Path(root) / f
        rel = str(fp.relative_to(Path('.')))
        report["files"].append(rel)
        if fp.suffix.lower() == PY_EXT:
            try:
                text = fp.read_text(encoding='utf-8')
            except Exception:
                try:
                    text = fp.read_text(encoding='latin-1')
                except Exception:
                    text = None
            if text:
                for key, pat in search_patterns.items():
                    if pat.search(text):
                        report.setdefault("matches", {}).setdefault(key, []).append(rel)

# Save file list and matches
with open(OUT_DIR / "file_list.json", "w", encoding='utf-8') as fh:
    json.dump(report, fh, ensure_ascii=False, indent=2)

print(f"Scanned {len(report['files'])} files. Found matches for: {list(report.get('matches', {}).keys())}\n")

# Attempt to capture last git commit and status
try:
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    git_status = subprocess.check_output(["git", "status", "--porcelain"]).decode().strip()
    with open(OUT_DIR / "git_info.txt", "w", encoding='utf-8') as fh:
        fh.write(f"commit: {git_commit}\nstatus:\n{git_status}\n")
    print("Captured git information.\n")
except Exception as e:
    with open(OUT_DIR / "git_info.txt", "w", encoding='utf-8') as fh:
        fh.write(f"git info not available: {e}\n")
    print("Git information not available.\n")

# Attempt to list common entrypoint files and print recommended commands
entry_candidates = ["main.py", "run.py", "app.py", "cli.py"]
found_entries = [p for p in entry_candidates if Path(p).exists()]
with open(OUT_DIR / "recommendations.txt", "w", encoding='utf-8') as fh:
    fh.write("Diagnostic recommendations and common test commands:\n\n")
    fh.write("1) Place 2-3 sample videos in ./tests/samples or provide links.\n")
    fh.write("2) To generate subtitles via Whisper locally (example):\n")
    fh.write("   whisper sample.mp4 --model medium --task transcribe --language zh -o ./diagnostic_output/whisper_output\n")
    fh.write("3) To merge TTS and video using ffmpeg (example):\n")
    fh.write("   ffmpeg -i clipped.mp4 -i tts.wav -c:v copy -c:a aac -map 0:v -map 1:a -shortest out_with_voice.mp4\n")
    fh.write("4) To burn subtitles into video (example):\n")
    fh.write("   ffmpeg -i out_with_voice.mp4 -vf \"subtitles=sub.srt:force_style='Fontsize=40'\" -c:a copy final.mp4\n")
    fh.write("\nFound candidate entry files: " + ", ".join(found_entries) + "\n")

print("Wrote recommendations and diagnostic outputs to diagnostic_output/\n")

print("Next steps:\n - Upload 3 representative sample videos to ./tests/samples or provide URLs.\n - Provide the most recent error log (full trace) from the pipeline run that produced missing audio/subtitles.\n - I will then run the pipeline and produce a targeted patch to externalize TTS/subtitles and add visual understanding.\n")

print("Diagnostic run complete.")
