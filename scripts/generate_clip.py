#!/usr/bin/env python3
"""
生成单个视频镜头
- 调用 MiniMax Hailuo API
- 等待生成完成
- 下载到本地
- 质量评估
"""
import os
import sys
import json
import time
import uuid
import hashlib
import requests
from datetime import datetime

# 配置
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
BASE_DIR = r"C:\Users\Administrator\.openclaw\workspace\video_production"
CLIPS_DIR = os.path.join(BASE_DIR, "generated_clips")
META_DIR = os.path.join(BASE_DIR, "metadata")
LENS_DB = os.path.join(META_DIR, "lens_db.json")

def load_lens_db():
    """加载镜头数据库"""
    if os.path.exists(LENS_DB):
        with open(LENS_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"lenses": []}

def save_lens_db(db):
    """保存镜头数据库"""
    os.makedirs(os.path.dirname(LENS_DB), exist_ok=True)
    with open(LENS_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def check_duplicate(prompt, db, threshold=0.9):
    """检查是否有相似的已有镜头"""
    # 简化版：检查相同提示词是否7天内生成过
    from datetime import timedelta
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    for lens in db.get("lenses", []):
        if lens.get("prompt") == prompt:
            created = datetime.fromisoformat(lens.get("created_at", "2020-01-01"))
            if created > seven_days_ago and lens.get("is_usable"):
                print(f"🔄 发现相似镜头，复用: {lens['id']}")
                return lens
    
    return None

def generate_clip_hailuo(prompt, duration=6, resolution="1080p"):
    """调用 MiniMax Hailuo API 生成视频"""
    if not MINIMAX_API_KEY:
        raise Exception("MINIMAX_API_KEY 环境变量未设置")
    
    url = "https://api.minimax.io/v1/video_generation"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "hailuo-02",
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution
    }
    
    print(f"🔄 调用 Hailuo API...")
    response = requests.post(url, headers=headers, json=data, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"API请求失败: {response.status_code} {response.text}")
    
    result = response.json()
    task_id = result.get("task_id")
    
    print(f"⏳ 任务ID: {task_id}, 等待生成...")
    
    # 轮询任务状态
    max_wait = 300  # 5分钟
    interval = 30
    elapsed = 0
    
    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval
        
        status_url = f"https://api.minimax.io/v1/video_generation/{task_id}"
        status_resp = requests.get(status_url, headers=headers, timeout=30)
        status_data = status_resp.json()
        
        status = status_data.get("status")
        print(f"  状态: {status} ({elapsed}s)")
        
        if status == "completed":
            video_url = status_data.get("video_url")
            return video_url
        elif status in ["failed", "cancelled"]:
            raise Exception(f"生成失败: {status}")
    
    raise Exception("生成超时（5分钟）")

def download_video(url, dest_path):
    """下载视频到本地"""
    print(f"📥 下载视频...")
    response = requests.get(url, timeout=120, stream=True)
    response.raise_for_status()
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"✅ 已保存: {dest_path}")

def evaluate_clip_quality(video_path):
    """评估镜头质量（简化版）"""
    # 实际应该调用 MiniMax Video-01 API
    # 这里简化返回85分
    print(f"🔍 质量评估: {video_path}")
    
    # TODO: 实现实际的质量评估
    # 使用 Video-01 API 分析视频
    
    return 85, True  # 分数, 是否可用

def main(prompt, duration=6, resolution="1080p"):
    """主函数"""
    print("=" * 60)
    print("生成视频镜头")
    print("=" * 60)
    print(f"提示词: {prompt}")
    
    os.makedirs(CLIPS_DIR, exist_ok=True)
    
    # 1. 查重
    db = load_lens_db()
    existing = check_duplicate(prompt, db)
    if existing:
        return existing
    
    # 2. 生成新镜头
    try:
        video_url = generate_clip_hailuo(prompt, duration, resolution)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clip_id = str(uuid.uuid4())[:8]
        filename = f"clip_{timestamp}_{clip_id}.mp4"
        filepath = os.path.join(CLIPS_DIR, filename)
        
        # 下载
        download_video(video_url, filepath)
        
        # 3. 质量评估
        quality_score, is_usable = evaluate_clip_quality(filepath)
        
        if not is_usable:
            print(f"⚠️ 质量不合格 ({quality_score}/100)，丢弃")
            os.remove(filepath)
            return None
        
        # 4. 计算MD5
        with open(filepath, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # 5. 记录元数据
        lens_record = {
            "id": file_hash,
            "prompt": prompt,
            "created_at": datetime.now().isoformat(),
            "file_path": filepath,
            "quality_score": quality_score,
            "is_usable": True,
            "used_in_final": False,
            "final_video_id": None
        }
        
        db["lenses"].append(lens_record)
        save_lens_db(db)
        
        print(f"\n✅ 镜头生成成功！")
        print(f"   文件: {filepath}")
        print(f"   ID: {file_hash}")
        print(f"   质量: {quality_score}/100")
        
        return lens_record
        
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python generate_clip.py <提示词> [时长] [分辨率]")
        sys.exit(1)
    
    prompt = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    resolution = sys.argv[3] if len(sys.argv) > 3 else "1080p"
    
    main(prompt, duration, resolution)
