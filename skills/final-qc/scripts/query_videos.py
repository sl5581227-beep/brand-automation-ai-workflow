#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Videos - 查询成片数据库
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

DB_FILE = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\metadata\final_db.json")

def load_db():
    """加载数据库"""
    if DB_FILE.exists():
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"videos": []}

def query_by_product(product_id):
    """按产品ID查询"""
    db = load_db()
    results = [v for v in db["videos"] if v.get("product_id") == product_id]
    return results

def query_by_date_range(start_date, end_date):
    """按日期范围查询"""
    db = load_db()
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    results = []
    for v in db["videos"]:
        try:
            gen_date = datetime.fromisoformat(v.get("generated_at", "2000-01-01"))
            if start <= gen_date <= end:
                results.append(v)
        except:
            pass
    
    return results

def query_by_score_range(min_score, max_score):
    """按评分范围查询"""
    db = load_db()
    results = [v for v in db["videos"] 
               if min_score <= v.get("quality_score", 0) <= max_score]
    return results

def print_results(results, title="查询结果"):
    """打印结果"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print(f"  找到 {len(results)} 个结果\n")
    
    for v in results:
        print(f"  ID: {v.get('video_id')}")
        print(f"  产品: {v.get('product_id')}")
        print(f"  时间: {v.get('generated_at')}")
        print(f"  评分: {v.get('quality_score')}")
        print(f"  文件: {v.get('file_paths', {})}")
        print("-" * 40)
    
    print()

def main():
    print("=" * 60)
    print("  Query Videos - 成片查询")
    print("=" * 60)
    
    db = load_db()
    print(f"\n总视频数: {len(db['videos'])}")
    
    if len(sys.argv) < 2:
        print("\n用法:")
        print("  query_videos.py all                    # 显示全部")
        print("  query_videos.py product <id>           # 按产品ID查询")
        print("  query_videos.py date <start> <end>    # 按日期范围")
        print("  query_videos.py score <min> <max>     # 按评分范围")
        return 0
    
    cmd = sys.argv[1]
    
    if cmd == "all":
        print_results(db["videos"], "全部视频")
    
    elif cmd == "product" and len(sys.argv) > 2:
        results = query_by_product(sys.argv[2])
        print_results(results, f"产品: {sys.argv[2]}")
    
    elif cmd == "date" and len(sys.argv) > 3:
        results = query_by_date_range(sys.argv[2], sys.argv[3])
        print_results(results, f"日期: {sys.argv[2]} ~ {sys.argv[3]}")
    
    elif cmd == "score" and len(sys.argv) > 3:
        results = query_by_score_range(int(sys.argv[2]), int(sys.argv[3]))
        print_results(results, f"评分: {sys.argv[2]} ~ {sys.argv[3]}")
    
    else:
        print("未知命令")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
