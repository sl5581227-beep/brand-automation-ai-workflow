#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluate Final Video - 成片质量评估
"""

import os
import sys
import json
import uuid
import subprocess
import re
from pathlib import Path
from datetime import datetime

FFMPEG = Path(r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe")
FFPROBE = Path(r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffprobe.exe")

DB_FILE = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\metadata\final_db.json")

def load_db():
    """加载数据库"""
    if DB_FILE.exists():
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"videos": []}

def save_db(db):
    """保存数据库"""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def generate_video_id():
    """生成唯一视频ID"""
    return str(uuid.uuid4())[:8]

def ffmpeg_qc(video_path):
    """FFmpeg质量检测"""
    results = {"status": "PASS", "checks": {}}
    
    # 分辨率
    cmd = [str(FFPROBE), "-v", "error", "-select_streams", "v:0", 
           "-show_entries", "stream=width,height", "-of", "json", str(video_path)]
    ok, out, err = run_cmd(cmd)
    if ok:
        try:
            data = json.loads(out)
            w = data["streams"][0]["width"]
            h = data["streams"][0]["height"]
            results["checks"]["resolution"] = "PASS" if w >= 720 and h >= 720 else "FAIL"
        except:
            results["checks"]["resolution"] = "FAIL"
    
    # 黑屏
    cmd = [str(FFMPEG), "-i", str(video_path), "-vf", "blackdetect=d=0.5:pix_th=0.00", "-f", "null", "-"]
    ok, out, err = run_cmd(cmd)
    has_black = "black_start" in err
    results["checks"]["blackdetect"] = "PASS" if not has_black else "FAIL"
    
    return results

def run_cmd(cmd):
    """运行命令"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return True, result.stderr
    except:
        return False, ""

def evaluate(video_path, product_id, hot_topic="", used_hotwords=None, cost_estimate=0):
    """
    评估成片并记录到数据库
    
    返回: {
        "status": "PASS/FAIL",
        "score": 75,
        "video_id": "uuid",
        ...
    }
    """
    if used_hotwords is None:
        used_hotwords = []
    
    print(f"  [Final-QC] 评估: {video_path}")
    
    # FFmpeg QC
    qc = ffmpeg_qc(video_path)
    print(f"    QC: {qc['status']}")
    
    # 生成唯一ID
    video_id = generate_video_id()
    
    # 获取文件信息
    file_size = Path(video_path).stat().st_size
    
    # 记录到数据库
    db = load_db()
    entry = {
        "video_id": video_id,
        "product_id": product_id,
        "generated_at": datetime.now().isoformat(),
        "hot_topic": hot_topic,
        "used_hotwords": used_hotwords,
        "quality_score": 75 if qc["status"] == "PASS" else 60,
        "qc_status": qc["status"],
        "file_paths": {
            "9x16": str(video_path)
        },
        "cost_estimate": cost_estimate,
        "file_size": file_size
    }
    db["videos"].append(entry)
    save_db(db)
    
    print(f"    Video ID: {video_id}")
    print(f"    DB updated: {DB_FILE}")
    
    return {
        "status": qc["status"],
        "score": entry["quality_score"],
        "video_id": video_id,
        "qc": qc
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: evaluate_final.py <video_path> <product_id> [hot_topic]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    product_id = sys.argv[2]
    hot_topic = sys.argv[3] if len(sys.argv) > 3 else ""
    
    result = evaluate(video_path, product_id, hot_topic)
    print(f"\n结果: {result}")
