#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cost Tracker - 即梦AI成本跟踪
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# 路径配置
LOGS_DIR = Path(r"C:\Users\Administrator\Desktop\qingShangVideos\logs")
COST_DAILY_FILE = LOGS_DIR / "cost_daily.json"
COST_WEEKLY_FILE = LOGS_DIR / "cost_weekly.json"

# 价格配置（按需修改）
PRICE_PER_SECOND = 0.5  # 元/秒
DAILY_QUOTA = 100  # 每日配额（元）
WEEKLY_QUOTA = 500  # 每周配额（元）

def ensure_logs_dir():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_daily_cost():
    """加载每日成本"""
    ensure_logs_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if COST_DAILY_FILE.exists():
        with open(COST_DAILY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data.get("date") == today:
                return data
    return {"date": today, "entries": [], "total_cost": 0, "total_clips": 0}

def save_daily_cost(data):
    """保存每日成本"""
    with open(COST_DAILY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_weekly_cost():
    """加载每周成本"""
    ensure_logs_dir()
    week_start = get_week_start().strftime("%Y-%m-%d")
    
    if COST_WEEKLY_FILE.exists():
        with open(COST_WEEKLY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data.get("week_start") == week_start:
                return data
    return {"week_start": week_start, "entries": [], "total_cost": 0, "total_clips": 0}

def save_weekly_cost(data):
    """保存每周成本"""
    with open(COST_WEEKLY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_week_start():
    """获取本周一日期"""
    today = datetime.now()
    return today - timedelta(days=today.weekday())

def record_clip_cost(product_id, duration_seconds, generation_time):
    """记录片段成本"""
    cost = duration_seconds * PRICE_PER_SECOND
    
    # 每日记录
    daily = load_daily_cost()
    daily["entries"].append({
        "timestamp": datetime.now().isoformat(),
        "product_id": product_id,
        "duration": duration_seconds,
        "generation_time": generation_time,
        "cost": cost
    })
    daily["total_cost"] += cost
    daily["total_clips"] += 1
    save_daily_cost(daily)
    
    # 每周记录
    weekly = load_weekly_cost()
    weekly["entries"].append({
        "timestamp": datetime.now().isoformat(),
        "product_id": product_id,
        "duration": duration_seconds,
        "generation_time": generation_time,
        "cost": cost
    })
    weekly["total_cost"] += cost
    weekly["total_clips"] += 1
    save_weekly_cost(weekly)
    
    print(f"  [Cost] 记录成本: {product_id} / {duration_seconds}s / {cost:.2f}元")
    
    return cost

def check_quota():
    """检查配额"""
    daily = load_daily_cost()
    weekly = load_weekly_cost()
    
    daily_ok = daily["total_cost"] < DAILY_QUOTA
    weekly_ok = weekly["total_cost"] < WEEKLY_QUOTA
    
    if not daily_ok:
        print(f"  [WARN] 超出每日配额! 当前: {daily['total_cost']:.2f}元 / 限额: {DAILY_QUOTA}元")
    if not weekly_ok:
        print(f"  [WARN] 超出每周配额! 当前: {weekly['total_cost']:.2f}元 / 限额: {WEEKLY_QUOTA}元")
    
    return daily_ok and weekly_ok

def get_cost_summary():
    """获取成本摘要"""
    daily = load_daily_cost()
    weekly = load_weekly_cost()
    
    return {
        "today": {
            "date": daily["date"],
            "total_cost": daily["total_cost"],
            "total_clips": daily["total_clips"],
            "remaining_quota": max(0, DAILY_QUOTA - daily["total_cost"])
        },
        "this_week": {
            "week_start": weekly["week_start"],
            "total_cost": weekly["total_cost"],
            "total_clips": weekly["total_clips"],
            "remaining_quota": max(0, WEEKLY_QUOTA - weekly["total_cost"])
        }
    }

def print_cost_report():
    """打印成本报告"""
    summary = get_cost_summary()
    
    print("\n" + "=" * 60)
    print("  成本统计报告")
    print("=" * 60)
    print(f"  今日 ({summary['today']['date']})")
    print(f"    总费用: {summary['today']['total_cost']:.2f}元")
    print(f"    片段数: {summary['today']['total_clips']}")
    print(f"    剩余配额: {summary['today']['remaining_quota']:.2f}元")
    print(f"  本周 ({summary['this_week']['week_start']} 开始)")
    print(f"    总费用: {summary['this_week']['total_cost']:.2f}元")
    print(f"    片段数: {summary['this_week']['total_clips']}")
    print(f"    剩余配额: {summary['this_week']['remaining_quota']:.2f}元")
    print("=" * 60)

class CostTracker:
    """成本跟踪器类"""
    
    def __init__(self):
        self.session_cost = 0
        self.session_clips = 0
    
    def record(self, product_id, duration_seconds, generation_time):
        """记录片段成本"""
        cost = record_clip_cost(product_id, duration_seconds, generation_time)
        self.session_cost += cost
        self.session_clips += 1
        return cost
    
    def check_quota(self):
        """检查配额"""
        return check_quota()
    
    def print_session_report(self):
        """打印本次会话报告"""
        print("\n" + "=" * 60)
        print("  本次会话成本")
        print("=" * 60)
        print(f"    片段数: {self.session_clips}")
        print(f"    总费用: {self.session_cost:.2f}元")
        print("=" * 60)

if __name__ == "__main__":
    print_cost_report()
