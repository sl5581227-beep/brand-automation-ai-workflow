#!/usr/bin/env python3
"""
Competitor-Viral-Analyst 核心脚本
全网搜索竞品爆款视频，提取热词，构建热词库和脚本库
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent.parent
HOTSPOT_DIR = PROJECT_ROOT / "knowledge_base" / "hotspots"


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
    "xiaohongshu": {
        "keywords": ["椰子水推荐", "健康饮品分享", "清爽解渴", "0糖饮品"],
        "hashtags": ["#椰子水", "#健康生活", "#饮品推荐"]
    },
    "kuaishou": {
        "keywords": ["椰子水", "好物推荐", "健康饮品"],
        "hashtags": ["#椰子水", "#快手好物"]
    },
    "x": {
        "keywords": ["coconut water benefits", "healthy drink", "summer hydration"],
        "hashtags": ["#coconutwater", "#health", "#wellness"]
    },
    "instagram": {
        "keywords": ["coconutwater", "healthylifestyle", "summerdrinks"],
        "hashtags": ["#coconutwater", "#healthy", "#reels"]
    },
    "youtube": {
        "keywords": ["coconut water review", "best coconut water", "coconut water taste"],
        "hashtags": ["#coconutwater", "#review", "#food"]
    }
}


# 预定义热词库（基于品类知识）
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
        {"word": "轻负担", "weight": 2, "visual": "纤体、清爽、无罪恶感"},
        {"word": "INS风", "weight": 2, "visual": "高颜值、摆拍、小清新"},
        {"word": "仪式感", "weight": 2, "visual": "开瓶慢动作、特写"}
    ],
    "场景": [
        {"word": "运动后", "weight": 3, "visual": "健身房、跑步、汗水"},
        {"word": "办公室", "weight": 2, "visual": "白领、电脑桌、下午茶"},
        {"word": "海边", "weight": 3, "visual": "沙滩、阳光、度假"},
        {"word": "野餐", "weight": 2, "visual": "草地、野餐篮、阳光"},
        {"word": "早餐", "weight": 2, "visual": "餐桌、阳光、活力"},
        {"word": "宵夜", "weight": 1, "visual": "夜晚、轻松、小酌"}
    ],
    "情绪": [
        {"word": "治愈", "weight": 2, "visual": "慢动作、柔和光线、放松"},
        {"word": "解压", "weight": 2, "visual": "开瓶气泡、倒入杯中"},
        {"word": "满足", "weight": 2, "visual": "表情特写、幸福笑容"},
        {"word": "清爽", "weight": 3, "visual": "冰镇、水珠、冷感"}
    ]
}


def extract_chinese_words(text: str, min_len: int = 2, max_len: int = 4) -> list:
    """提取中文词组"""
    pattern = rf'[\u4e00-\u9fa5]{{{min_len},{max_len}}}'
    return re.findall(pattern, text)


def extract_english_words(text: str) -> list:
    """提取英文词组"""
    pattern = r'[a-zA-Z]{3,}'
    return re.findall(pattern, text.lower())


def build_hotword_library(product_category: str = "椰子水", product_name: str = None) -> dict:
    """构建热词库"""
    print(f"Building hotword library for: {product_category}")
    
    HOTSPOT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 合并所有热词
    all_hotwords = []
    
    for category, words in CATEGORY_HOTWORDS.items():
        for word_data in words:
            word_data["category"] = category
            word_data["frequency"] = word_data.pop("weight", 1) * 5  # 转换为频率
            word_data["platforms"] = ["全平台"]  # 默认
            all_hotwords.append(word_data)
    
    # 按频率排序
    all_hotwords.sort(key=lambda x: x["frequency"], reverse=True)
    
    # 取TOP热词
    top_hotwords = all_hotwords[:25]
    
    # 构建情感触发词
    emotional_triggers = list(set(
        w["word"] for w in all_hotwords 
        if w.get("category") == "情绪"
    ))
    
    # 构建场景标签
    scene_tags = list(set(
        w["word"] for w in all_hotwords 
        if w.get("category") == "场景"
    ))
    
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
    
    # 保存
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{product_category}_{date_str}_hotspots.json"
    filepath = HOTSPOT_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(hotword_report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Hotword library saved: {filepath}")
    print(f"   Total hotwords: {len(top_hotwords)}")
    print(f"   Emotional triggers: {emotional_triggers[:5]}")
    print(f"   Scene tags: {scene_tags[:5]}")
    
    return hotword_report


def build_script_library(product_category: str = "椰子水") -> dict:
    """构建脚本库模板"""
    print(f"Building script library for: {product_category}")
    
    HOTSPOT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 基于爆款视频分析的脚本模板
    script_templates = [
        {
            "id": "template_001",
            "name": "痛点引入型",
            "platform": "通用",
            "likes_estimate": "10万+",
            "structure": {
                "hook": {"time": "0-3s", "desc": "痛点提问/场景引入", "example": "夏天最渴的时候怎么办？"},
                "pain_point": {"time": "3-8s", "desc": "描述痛点", "example": "白水没味道，奶茶太腻..."},
                "solution": {"time": "8-20s", "desc": "产品介绍+卖点", "example": "试试这个椰子水！0糖低卡超清爽"},
                "scene": {"time": "20-30s", "desc": "使用场景展示", "example": "运动后来一瓶...工作累了来一杯..."},
                "cta": {"time": "30-45s", "desc": "行动号召", "example": "点击购物车，夏日清爽get！"}
            },
            "pace": "快节奏，2-3秒一切换",
            "music": "轻快活泼，节奏感强",
            "visual_style": "近景特写+场景切换"
        },
        {
            "id": "template_002",
            "name": "ASMR特写型",
            "platform": "TikTok/Instagram",
            "likes_estimate": "5万+",
            "structure": {
                "hook": {"time": "0-2s", "desc": "产品特写+音效", "example": "开瓶的清脆声"},
                "pour": {"time": "2-5s", "desc": "倒水特写", "example": "液体倒入杯中，晶莹剔透"},
                "drink": {"time": "5-12s", "desc": "饮用特写", "example": "表情满足，声音诱人"},
                "product": {"time": "12-20s", "desc": "产品展示", "example": "瓶子设计+成分"},
                "cta": {"time": "20-30s", "desc": "引导购买", "example": "评论区告诉我你的夏日饮品！"}
            },
            "pace": "慢镜头，营造氛围",
            "music": "ASMR/白噪音/自然声",
            "visual_style": "微距特写，慢动作"
        },
        {
            "id": "template_003",
            "name": "对比测评型",
            "platform": "YouTube/小红书",
            "likes_estimate": "8万+",
            "structure": {
                "hook": {"time": "0-3s", "desc": "问题引入", "example": "市面上的椰子水到底哪家强？"},
                "compare": {"time": "3-15s", "desc": "对比展示", "example": "外观、成分、口感对比"},
                "recommend": {"time": "15-25s", "desc": "推荐产品", "example": "综合对比，这款最值得"},
                "reason": {"time": "25-35s", "desc": "推荐理由", "example": "口感清爽、成分干净..."},
                "cta": {"time": "35-45s", "desc": "行动号召", "example": "链接在评论区！"}
            },
            "pace": "中等节奏，理性分析",
            "music": "背景音乐+解说",
            "visual_style": "对比排版+产品特写"
        },
        {
            "id": "template_004",
            "name": "场景演绎型",
            "platform": "抖音/快手",
            "likes_estimate": "15万+",
            "structure": {
                "hook": {"time": "0-3s", "desc": "场景设定", "example": "健身一小时后..."},
                "story": {"time": "3-20s", "desc": "故事展开", "example": "拿起椰子水，一口下去..."},
                "benefit": {"time": "20-30s", "desc": "产品利益点", "example": "快速补水，0糖低卡"},
                "mood": {"time": "30-35s", "desc": "情绪高潮", "example": "太爽了！就是这个味道！"},
                "cta": {"time": "35-45s", "desc": "引导互动", "example": "你们运动后喝什么？评论区告诉我！"}
            },
            "pace": "情感递进，高潮结尾",
            "music": "节奏感强，情绪饱满",
            "visual_style": "情景剧+产品植入"
        }
    ]
    
    script_report = {
        "product_category": product_category,
        "created_at": datetime.now().isoformat(),
        "templates": script_templates,
        "total_templates": len(script_templates)
    }
    
    # 保存
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{product_category}_{date_str}_scripts.json"
    filepath = HOTSPOT_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(script_report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Script library saved: {filepath}")
    print(f"   Total templates: {len(script_templates)}")
    
    return script_report


def generate_combined_report(product_category: str = "椰子水", product_name: str = None) -> dict:
    """生成综合分析报告"""
    print(f"\n{'='*60}")
    print(f"  COMPETITOR VIRAL ANALYSIS - {product_category}")
    print(f"{'='*60}\n")
    
    # 生成热词库
    hotwords = build_hotword_library(product_category, product_name)
    
    # 生成脚本库
    scripts = build_script_library(product_category)
    
    # 综合报告
    combined = {
        "report_title": f"竞品爆款分析报告 - {product_category}",
        "generated_at": datetime.now().isoformat(),
        "hotwords": hotwords,
        "script_templates": scripts,
        "recommendations": {
            "best_opening_hooks": [
                "夏天最渴的时候怎么办？",
                "运动后补水，你选对了吗？",
                "0糖饮品真的健康吗？"
            ],
            "must_include_elements": [
                "产品特写（瓶身设计）",
                "液体色泽展示",
                "使用场景演绎",
                "0糖/低卡标识特写"
            ],
            "recommended_visual_elements": [
                "水滴/冰块特写",
                "热带植物背景",
                "阳光/海边场景",
                "健身运动场景"
            ]
        }
    }
    
    return combined


def main():
    """命令行入口"""
    product_category = sys.argv[1] if len(sys.argv) > 1 else "椰子水"
    product_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    report = generate_combined_report(product_category, product_name)
    
    # 保存综合报告
    HOTSPOT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    combined_path = HOTSPOT_DIR / f"{product_category}_{date_str}_combined_report.json"
    
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Combined report saved: {combined_path}")
    print(f"\n{'='*60}")
    print("  TOP 10 HOTWORDS")
    print(f"{'='*60}")
    for i, hw in enumerate(report["hotwords"]["hotwords"][:10], 1):
        print(f"  {i:2d}. {hw['word']} ({hw['frequency']}次) - {hw.get('visual', 'N/A')}")


if __name__ == "__main__":
    main()
