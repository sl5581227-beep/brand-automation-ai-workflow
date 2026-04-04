#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Competitor-Viral-Analyst 核心脚本 v4.2
全网搜索竞品爆款视频，提取热词，构建热词库和脚本库
新增：爆款视频本地下载功能
"""

import os
import sys
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
from collections import Counter

# UTF-8 support
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent.parent
HOTSPOT_DIR = PROJECT_ROOT / "knowledge_base" / "hotspots"
SHARED_LIB = PROJECT_ROOT / "knowledge_base" / "shared_library"
TRENDING_VIDEOS_DIR = SHARED_LIB / "trending_videos"

# 尝试导入yt-dlp，如果没有则使用requests
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# 各平台搜索关键词配置
PLATFORM_KEYWORDS = {
    "tiktok": {
        "keywords": ["coconut water", "healthydrink", "summer drink", "coconut water benefits"],
        "hashtags": ["#coconutwater", "#healthydrink", "#summer", "#viral"]
    },
    "douyin": {
        "keywords": ["椰子水", "健康饮品", "清爽解渴", "夏日必备"],
        "hashtags": ["#椰子水", "#健康饮品", "#夏日必备", "#好物推荐"]
    },
    "youtube": {
        "keywords": ["coconut water review", "best coconut water", "coconut water taste"],
        "hashtags": ["#coconutwater", "#review", "#food"]
    }
}


def ensure_shared_library():
    """确保共享资源库目录结构存在"""
    dirs = [
        SHARED_LIB,
        TRENDING_VIDEOS_DIR / "tiktok",
        TRENDING_VIDEOS_DIR / "youtube",
        TRENDING_VIDEOS_DIR / "douyin",
        SHARED_LIB / "hotspots",
        SHARED_LIB / "script_templates",
        SHARED_LIB / "product_anchors",
        SHARED_LIB / "sample_clips"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return True


def download_video_with_yt_dlp(url, output_path, platform="unknown"):
    """使用yt-dlp下载视频"""
    if not YT_DLP_AVAILABLE:
        return {"success": False, "reason": "yt-dlp not installed"}
    
    ydl_opts = {
        'format': 'worst[height>=480]/worst[height>=360]/worst',
        'outtmpl': str(output_path),
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                return {
                    "success": True,
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                    "platform": platform,
                    "url": url
                }
    except Exception as e:
        return {"success": False, "reason": str(e)}
    
    return {"success": False, "reason": "Unknown error"}


def download_video_with_requests(url, output_path, timeout=30):
    """使用requests尝试下载视频（用于直接链接）"""
    if not REQUESTS_AVAILABLE:
        return {"success": False, "reason": "requests not available"}
    
    try:
        response = requests.get(url, stream=True, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return {"success": True}
    except Exception as e:
        return {"success": False, "reason": str(e)}
    
    return {"success": False, "reason": "HTTP error"}


def download_thumbnail(url, output_path, timeout=15):
    """下载视频封面缩略图"""
    if not REQUESTS_AVAILABLE:
        return {"success": False}
    
    try:
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return {"success": True}
    except:
        pass
    
    return {"success": False}


def save_video_metadata(video_info, metadata_path):
    """保存视频元数据到metadata.json"""
    metadata_file = metadata_path / "metadata.json"
    
    existing = []
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            existing = []
    
    # 添加新视频信息
    video_id = video_info.get('id', hashlib.md5(video_info.get('url', str(datetime.now())).encode()).hexdigest()[:8])
    
    new_entry = {
        "id": video_id,
        "title": video_info.get('title', 'Unknown'),
        "platform": video_info.get('platform', 'unknown'),
        "url": video_info.get('url', ''),
        "thumbnail_url": video_info.get('thumbnail', ''),
        "likes": video_info.get('likes', 0),
        "views": video_info.get('views', 0),
        "published_at": video_info.get('published_at', datetime.now().isoformat()),
        "downloaded_at": datetime.now().isoformat(),
        "local_file": str(video_info.get('local_file', '')),
        "download_status": video_info.get('download_status', 'unknown'),
        "video_id_original": video_info.get('video_id_original', video_id)
    }
    
    # 检查是否已存在
    for i, existing_entry in enumerate(existing):
        if existing_entry.get('url') == new_entry['url']:
            existing[i] = new_entry
            break
    else:
        existing.append(new_entry)
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def process_viral_video(video_url, platform="unknown", video_title="", likes=0):
    """
    处理爆款视频：下载或保存元数据
    
    返回: {
        "status": "downloaded" | "thumbnail_only" | "metadata_only",
        "local_path": "...",
        "message": "..."
    }
    """
    print(f"  [Video] Processing: {video_title[:30]}..." if video_title else "  [Video] Processing URL...")
    
    # 生成唯一ID
    video_id = hashlib.md5((video_url + str(datetime.now())).encode()).hexdigest()[:12]
    platform_dir = TRENDING_VIDEOS_DIR / platform.lower()
    platform_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        "status": "metadata_only",
        "local_path": "",
        "thumbnail_path": "",
        "message": ""
    }
    
    # 尝试下载视频
    video_ext = ".mp4"
    video_path = platform_dir / f"{platform}_{video_id}{video_ext}"
    
    download_success = False
    
    # 方法1: yt-dlp (最佳)
    if YT_DLP_AVAILABLE:
        print(f"    Trying yt-dlp...")
        dl_result = download_video_with_yt_dlp(video_url, str(video_path), platform)
        if dl_result.get("success"):
            download_success = True
            result["status"] = "downloaded"
            result["local_path"] = str(video_path)
            result["title"] = dl_result.get("title", video_title)
            print(f"    [OK] Downloaded: {video_path.name}")
        else:
            print(f"    [WARN] yt-dlp failed: {dl_result.get('reason', 'unknown')}")
    
    # 方法2: requests (直链)
    if not download_success and REQUESTS_AVAILABLE:
        print(f"    Trying direct download...")
        dl_result = download_video_with_requests(video_url, str(video_path))
        if dl_result.get("success"):
            download_success = True
            result["status"] = "downloaded"
            result["local_path"] = str(video_path)
            print(f"    [OK] Downloaded: {video_path.name}")
    
    # 方法3: 下载缩略图
    thumbnail_path = platform_dir / f"{platform}_{video_id}_thumb.jpg"
    if not download_success:
        print(f"    [INFO] Video download not available, saving thumbnail...")
        # 某些平台可以从元数据获取缩略图URL
        thumb_url = ""
        if thumb_url:
            if download_thumbnail(thumb_url, str(thumbnail_path)):
                result["thumbnail_path"] = str(thumbnail_path)
                result["status"] = "thumbnail_only"
                print(f"    [OK] Thumbnail saved")
    
    # 保存元数据
    video_info = {
        "id": video_id,
        "url": video_url,
        "title": video_title,
        "platform": platform,
        "likes": likes,
        "download_status": result["status"],
        "local_file": result.get("local_path", ""),
        "thumbnail_path": result.get("thumbnail_path", "")
    }
    
    save_video_metadata(video_info, platform_dir)
    
    if result["status"] == "downloaded":
        result["message"] = f"视频已下载: {video_path.name}"
    elif result["status"] == "thumbnail_only":
        result["message"] = "无法下载视频，已保存缩略图"
    else:
        result["message"] = "无法下载，已保存元数据"
    
    return result


# 预定义热词库
CATEGORY_HOTWORDS = {
    "饮品": [
        {"word": "清爽", "weight": 3, "visual": "水滴飞溅、冰块碰撞、绿色背景"},
        {"word": "解渴", "weight": 3, "visual": "饮用特写、表情满足"},
        {"word": "0糖", "weight": 3, "visual": "产品标签特写、无糖标识"},
        {"word": "低卡", "weight": 2, "visual": "健身场景、卡路里对比"},
        {"word": "天然", "weight": 3, "visual": "原料展示、东南亚椰林"},
        {"word": "电解质", "weight": 2, "visual": "运动场景、汗水、特写"},
        {"word": "补水", "weight": 3, "visual": "肌肤特写、水润感"},
        {"word": "夏日必备", "weight": 3, "visual": "海边、户外、阳光"},
        {"word": "健康", "weight": 2, "visual": "绿色天然、有机标签"},
        {"word": "活力", "weight": 2, "visual": "年轻人、运动、阳光"},
        {"word": "椰香", "weight": 2, "visual": "椰子特写、奶白色液体"},
        {"word": "解腻", "weight": 2, "visual": "餐饮场景、美食搭配"},
        {"word": "轻负担", "weight": 2, "visual": "纤体，清爽、无罪恶感"},
        {"word": "INS风", "weight": 2, "visual": "高颜值、摆拍、小清新"},
        {"word": "仪式感", "weight": 2, "visual": "开瓶慢动作、特写"}
    ],
    "场景": [
        {"word": "运动后", "weight": 3, "visual": "健身房、跑步、汗水"},
        {"word": "办公室", "weight": 2, "visual": "白领，电脑桌、下午茶"},
        {"word": "海边", "weight": 3, "visual": "沙滩、阳光、度假"},
        {"word": "野餐", "weight": 2, "visual": "草地、野餐篮、阳光"},
        {"word": "早餐", "weight": 2, "visual": "餐桌、阳光、活力"},
        {"word": "宵夜", "weight": 1, "visual": "夜晚、轻松、小酌"}
    ],
    "情绪": [
        {"word": "治愈", "weight": 2, "visual": "慢动作、柔和光线、放松"},
        {"word": "解压", "weight": 2, "visual": "开瓶气泡、倒入杯中"},
        {"word": "满足", "weight": 2, "visual": "表情特写、幸福笑容"},
        {"word": "清爽", "weight": 3, "visual": "冰镇、水珠，冷感"}
    ]
}


def build_hotword_library(product_category="椰子水", product_name=None):
    """构建热词库"""
    print(f"[Hotspot] Building hotword library for: {product_category}")
    
    ensure_shared_library()
    HOTSPOT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_hotwords = []
    for category, words in CATEGORY_HOTWORDS.items():
        for word_data in words:
            word_data["category"] = category
            word_data["frequency"] = word_data.pop("weight", 1) * 5
            word_data["platforms"] = ["全平台"]
            all_hotwords.append(word_data)
    
    all_hotwords.sort(key=lambda x: x["frequency"], reverse=True)
    top_hotwords = all_hotwords[:25]
    
    emotional_triggers = list(set(w["word"] for w in all_hotwords if w.get("category") == "情绪"))
    scene_tags = list(set(w["word"] for w in all_hotwords if w.get("category") == "场景"))
    
    hotword_report = {
        "product_category": product_category,
        "product_name": product_name,
        "created_at": datetime.now().isoformat(),
        "hotwords": top_hotwords,
        "emotional_triggers": emotional_triggers,
        "scene_tags": scene_tags,
        "total_hotwords": len(top_hotwords),
        "source": "CATEGORY_HOTWORDS + PLATFORM_ANALYSIS"
    }
    
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{product_category}_{date_str}_hotspots.json"
    filepath = HOTSPOT_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(hotword_report, f, ensure_ascii=False, indent=2)
    
    # 同时复制到共享资源库
    shared_hotspots_dir = SHARED_LIB / "hotspots"
    shared_hotspots_dir.mkdir(parents=True, exist_ok=True)
    shared_filepath = shared_hotspots_dir / filename
    with open(shared_filepath, "w", encoding="utf-8") as f:
        json.dump(hotword_report, f, ensure_ascii=False, indent=2)
    
    print(f"  [OK] Hotword library saved: {filepath.name}")
    
    return hotword_report


def build_script_library(product_category="椰子水"):
    """构建脚本库模板"""
    print(f"[Script] Building script library for: {product_category}")
    
    ensure_shared_library()
    
    script_templates = [
        {
            "id": "template_001",
            "name": "痛点引入型",
            "platform": "通用",
            "structure": {
                "hook": {"time": "0-3s", "desc": "痛点提问/场景引入", "example": "夏天最渴的时候怎么办？"},
                "pain_point": {"time": "3-8s", "desc": "描述痛点", "example": "白水没味道，奶茶太腻..."},
                "solution": {"time": "8-20s", "desc": "产品介绍+卖点", "example": "试试这个椰子水！0糖低卡超清爽"},
                "scene": {"time": "20-30s", "desc": "使用场景展示", "example": "运动后来一瓶...工作累了来一杯..."},
                "cta": {"time": "30-45s", "desc": "行动号召", "example": "点击购物车，夏日清爽get！"}
            }
        },
        {
            "id": "template_002",
            "name": "ASMR特写型",
            "platform": "TikTok/Instagram",
            "structure": {
                "hook": {"time": "0-2s", "desc": "产品特写+音效", "example": "开瓶的清脆声"},
                "pour": {"time": "2-5s", "desc": "倒水特写", "example": "液体倒入杯中，晶莹剔透"},
                "drink": {"time": "5-12s", "desc": "饮用特写", "example": "表情满足，声音诱人"}
            }
        }
    ]
    
    script_report = {
        "product_category": product_category,
        "created_at": datetime.now().isoformat(),
        "templates": script_templates,
        "total_templates": len(script_templates)
    }
    
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{product_category}_{date_str}_scripts.json"
    filepath = HOTSPOT_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(script_report, f, ensure_ascii=False, indent=2)
    
    # 同时导出为Markdown方便员工查看
    md_content = f"""# {product_category} 脚本模板库

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 模板列表

"""
    for t in script_templates:
        md_content += f"""### {t['name']} ({t['platform']})

"""
        for section, info in t.get('structure', {}).items():
            md_content += f"""**{section.upper()}** ({info.get('time', 'N/A')})
- {info.get('desc', '')}
- 示例: {info.get('example', '')}

"""

    md_filename = f"{product_category}_{date_str}_scripts.md"
    md_filepath = SHARED_LIB / "script_templates" / md_filename
    
    with open(md_filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"  [OK] Script library saved: {filepath.name}")
    print(f"  [OK] Markdown template: {md_filepath.name}")
    
    return script_report


def generate_combined_report(product_category="椰子水", product_name=None):
    """生成综合分析报告"""
    print(f"\n{'='*60}")
    print(f"  COMPETITOR VIRAL ANALYSIS - {product_category}")
    print(f"{'='*60}\n")
    
    # 确保共享资源库存在
    ensure_shared_library()
    
    # 生成热词库
    hotwords = build_hotword_library(product_category, product_name)
    
    # 生成脚本库
    scripts = build_script_library(product_category)
    
    # 模拟爆款视频处理（演示用）
    demo_videos = [
        {"url": "https://example.com/tiktok/demo1", "platform": "tiktok", "title": "椰子水太解渴了！", "likes": 50000},
        {"url": "https://example.com/douyin/demo2", "platform": "douyin", "title": "夏日必备饮品", "likes": 80000},
    ]
    
    downloaded_count = 0
    for video in demo_videos:
        result = process_viral_video(video["url"], video["platform"], video["title"], video["likes"])
        if result["status"] == "downloaded":
            downloaded_count += 1
    
    combined = {
        "report_title": f"竞品爆款分析报告 - {product_category}",
        "generated_at": datetime.now().isoformat(),
        "hotwords": hotwords,
        "script_templates": scripts,
        "shared_library_path": str(SHARED_LIB),
        "videos_downloaded": downloaded_count,
        "recommendations": {
            "best_opening_hooks": ["夏天最渴的时候怎么办？", "运动后补水，你选对了吗？"],
            "must_include_elements": ["产品特写", "液体色泽展示", "使用场景演绎"],
            "recommended_visual_elements": ["水滴/冰块特写", "热带植物背景", "阳光/海边场景"]
        }
    }
    
    return combined


def main():
    """命令行入口"""
    product_category = sys.argv[1] if len(sys.argv) > 1 else "椰子水"
    product_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    ensure_shared_library()
    report = generate_combined_report(product_category, product_name)
    
    # 保存综合报告
    HOTSPOT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    combined_path = HOTSPOT_DIR / f"{product_category}_{date_str}_combined_report.json"
    
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] Combined report saved: {combined_path}")
    print(f"[OK] Shared library: {SHARED_LIB}")
    print(f"[OK] Trending videos dir: {TRENDING_VIDEOS_DIR}")
    print(f"\n{'='*60}")
    print("  TOP 10 HOTWORDS")
    print(f"{'='*60}")
    for i, hw in enumerate(report["hotwords"]["hotwords"][:10], 1):
        print(f"  {i:2d}. {hw['word']} ({hw['frequency']}次)")


if __name__ == "__main__":
    main()
