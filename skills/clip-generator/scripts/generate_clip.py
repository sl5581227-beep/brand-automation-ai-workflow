#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Clip - 带重试逻辑的片段生成
"""

import os
import sys
import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
import time

# 路径配置
DREAMINA = r"C:\Users\Administrator\bin\dreamina.exe"
LOGS_DIR = Path(r"C:\Users\Administrator\Desktop\qingShangVideos\logs")
FAILED_CLIPS_FILE = LOGS_DIR / "failed_clips.json"

MAX_RETRIES = 3
RETRY_INTERVAL = 10  # 秒

def ensure_logs_dir():
    """确保日志目录存在"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_failed_clips():
    """加载失败记录"""
    if FAILED_CLIPS_FILE.exists():
        with open(FAILED_CLIPS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"failed_clips": []}

def save_failed_clips(data):
    """保存失败记录"""
    ensure_logs_dir()
    with open(FAILED_CLIPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def record_failure(shot_id, scene_name, prompt, reason):
    """记录失败片段"""
    data = load_failed_clips()
    data["failed_clips"].append({
        "shot_id": shot_id,
        "scene_name": scene_name,
        "original_prompt": prompt,
        "reason": reason,
        "failed_at": datetime.now().isoformat()
    })
    save_failed_clips(data)
    print(f"  [FAIL RECORDED] shot_id={shot_id}, reason={reason}")

def modify_prompt_for_retry(prompt, retry_count):
    """修改提示词用于重试"""
    modifications = [
        # 缩短到50词以内
        lambda p: ' '.join(p.split()[:50]),
        # 改变镜头类型
        lambda p: p.replace("close-up", "medium shot").replace("close up", "medium shot"),
        lambda p: p.replace("medium shot", "wide shot").replace("panoramic", "quick"),
        # 简化描述
        lambda p: p[:200] + " professional quality" if len(p) > 200 else p,
    ]
    
    if retry_count < len(modifications):
        return modifications[retry_count](prompt)
    return prompt

def generate_with_dreamina(prompt, duration=5, ratio="9:16"):
    """调用即梦AI生成片段"""
    cmd = [
        DREAMINA, "text2video",
        "--prompt", prompt,
        "--duration", str(duration),
        "--ratio", ratio,
        "--poll", "0"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout
        
        # 解析提交ID
        try:
            data = json.loads(output)
            return data.get("submit_id"), data
        except:
            return None, {"error": "JSON parse failed", "output": output[:200]}
            
    except subprocess.TimeoutExpired:
        return None, {"error": "Submit timeout"}
    except Exception as e:
        return None, {"error": str(e)}

def poll_for_result(submit_id, max_wait=180):
    """轮询等待结果"""
    waited = 0
    interval = 10
    
    while waited < max_wait:
        time.sleep(interval)
        
        cmd = [DREAMINA, "query_result", "--submit_id", submit_id]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stdout
            
            if "success" in output:
                try:
                    data = json.loads(output)
                    videos = data.get("result_json", {}).get("videos", [])
                    if videos:
                        return videos[0].get("video_url"), data
                except:
                    pass
            
            if "fail" in output:
                return None, {"error": "Generation failed"}
                
        except:
            pass
        
        waited += interval
        print(f"    等待中... ({waited}s)")
    
    return None, {"error": "Timeout"}

def generate_clip(shot_id, scene_name, prompt, duration=5, ratio="9:16", output_path=None):
    """
    生成单个片段（带重试逻辑）
    
    返回: {
        "status": "success" | "skipped" | "failed",
        "submit_id": "...",
        "video_url": "...",
        "local_path": "...",
        "retry_count": 0,
        "reason": "..."
    }
    """
    print(f"\n  [Clip Generator] shot_id={shot_id}")
    print(f"    场景: {scene_name}")
    print(f"    Prompt: {prompt[:60]}...")
    
    current_prompt = prompt
    last_error = None
    
    for retry in range(MAX_RETRIES):
        if retry > 0:
            print(f"  [RETRY {retry}/{MAX_RETRIES-1}] 修改提示词重试...")
            current_prompt = modify_prompt_for_retry(prompt, retry)
            print(f"    新Prompt: {current_prompt[:60]}...")
            time.sleep(RETRY_INTERVAL)
        
        # 提交
        submit_id, submit_data = generate_with_dreamina(current_prompt, duration, ratio)
        
        if not submit_id:
            last_error = submit_data.get("error", "Unknown")
            print(f"  [RETRY] 提交失败: {last_error}")
            continue
        
        print(f"    提交成功: {submit_id}")
        
        # 轮询
        video_url, result_data = poll_for_result(submit_id)
        
        if video_url:
            print(f"  [SUCCESS] 生成成功!")
            return {
                "status": "success",
                "submit_id": submit_id,
                "video_url": video_url,
                "retry_count": retry,
                "reason": None
            }
        else:
            last_error = result_data.get("error", "Unknown")
            print(f"  [RETRY] 获取结果失败: {last_error}")
    
    # 3次都失败
    print(f"  [FAILED] 3次重试都失败，跳过该片段")
    record_failure(shot_id, scene_name, prompt, last_error)
    
    return {
        "status": "skipped",
        "submit_id": submit_id,
        "retry_count": MAX_RETRIES,
        "reason": last_error
    }

def download_clip(video_url, output_path):
    """下载片段"""
    FFMPEG = Path(r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe")
    
    cmd = [str(FFMPEG), "-y", "-i", video_url, "-c", "copy", str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    return result.returncode == 0

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: generate_clip.py <shot_id> <scene_name> <prompt> [duration] [ratio]")
        sys.exit(1)
    
    shot_id = sys.argv[1]
    scene_name = sys.argv[2]
    prompt = sys.argv[3]
    duration = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    ratio = sys.argv[5] if len(sys.argv) > 5 else "9:16"
    
    result = generate_clip(shot_id, scene_name, prompt, duration, ratio)
    print(f"\nResult: {result}")
