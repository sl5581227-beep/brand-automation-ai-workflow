#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clip Cache - 片段缓存与复用
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

CACHE_FILE = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\knowledge_base\clip_cache.json")
CACHE_TTL_DAYS = 30

def load_cache():
    """加载缓存"""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"clips": [], "updated_at": None}

def save_cache(cache):
    """保存缓存"""
    cache["updated_at"] = datetime.now().isoformat()
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def compute_scene_hash(scene_desc):
    """计算场景描述的MD5哈希"""
    return hashlib.md5(scene_desc.encode('utf-8')).hexdigest()

def check_cache(product_id, scene_desc, min_score=75):
    """检查缓存"""
    cache = load_cache()
    scene_hash = compute_scene_hash(scene_desc)
    
    cutoff_date = datetime.now() - timedelta(days=CACHE_TTL_DAYS)
    
    for clip in cache.get("clips", []):
        # 检查是否匹配
        if clip.get("product_id") == product_id and clip.get("scene_hash") == scene_hash:
            # 检查评分
            if clip.get("quality_score", 0) >= min_score:
                # 检查是否过期
                created_at = datetime.fromisoformat(clip.get("created_at", "2000-01-01"))
                if created_at > cutoff_date:
                    return {
                        "hit": True,
                        "cached_file": clip.get("file_path"),
                        "clip_id": clip.get("clip_id"),
                        "quality_score": clip.get("quality_score"),
                        "message": "缓存命中"
                    }
                else:
                    return {
                        "hit": False,
                        "reason": "缓存已过期"
                    }
    
    return {"hit": False, "reason": "未找到匹配缓存"}

def add_to_cache(product_id, scene_desc, file_path, quality_score, clip_id=None):
    """添加到缓存"""
    cache = load_cache()
    
    # 检查是否已存在
    scene_hash = compute_scene_hash(scene_desc)
    for existing in cache.get("clips", []):
        if existing.get("product_id") == product_id and existing.get("scene_hash") == scene_hash:
            # 更新现有条目
            existing["file_path"] = file_path
            existing["quality_score"] = quality_score
            existing["created_at"] = datetime.now().isoformat()
            if clip_id:
                existing["clip_id"] = clip_id
            save_cache(cache)
            return
    
    # 添加新条目
    cache.setdefault("clips", []).append({
        "clip_id": clip_id or f"clip_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "product_id": product_id,
        "scene_hash": scene_hash,
        "scene_desc": scene_desc[:200],  # 保留前200字符
        "file_path": str(file_path),
        "quality_score": quality_score,
        "created_at": datetime.now().isoformat()
    })
    
    save_cache(cache)
    print(f"  [Cache] 添加到缓存: {product_id} / {scene_desc[:30]}...")

def get_cache_stats():
    """获取缓存统计"""
    cache = load_cache()
    clips = cache.get("clips", [])
    
    total = len(clips)
    expired = 0
    cutoff_date = datetime.now() - timedelta(days=CACHE_TTL_DAYS)
    
    for clip in clips:
        created_at = datetime.fromisoformat(clip.get("created_at", "2000-01-01"))
        if created_at < cutoff_date:
            expired += 1
    
    return {
        "total": total,
        "active": total - expired,
        "expired": expired
    }

def copy_cached_clip(cached_file, target_path):
    """复制缓存片段到目标路径"""
    if Path(cached_file).exists():
        shutil.copy2(cached_file, target_path)
        return True
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("  Clip Cache")
    print("=" * 60)
    
    stats = get_cache_stats()
    print(f"  缓存统计:")
    print(f"    总数: {stats['total']}")
    print(f"    活跃: {stats['active']}")
    print(f"    已过期: {stats['expired']}")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            result = check_cache(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
            print(f"\n  缓存检查结果: {result}")
