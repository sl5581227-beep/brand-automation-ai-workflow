#!/usr/bin/env python3
"""
product-image-searcher 核心脚本
精准查找产品图片：品牌官网、天猫、京东、小红书、1688
"""

import os
import json
import time
import requests
from pathlib import Path
from urllib.parse import quote
import hashlib

# ============== 配置 ==============
PRODUCTS_DIR = Path(__file__).parent.parent.parent / "knowledge_base" / "products"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

SEARCH_SOURCES = {
    "tmall": "https://s.taobao.com/search?q={q}&imgfile=&initiative_id=staobaoz&stats_click=search_radio_all:1",
    "jd": "https://search.jd.com/Search?keyword={q}&enc=utf-8",
    "xiaohongshu": "https://www.xiaohongshu.com/search_result?keyword={q}&type=51",
    "brand": "https://www.bing.com/search?q={q}+官方旗舰店+site%3A",
    "1688": "https://s.1688.com/youyuan/index.htm?tab=mallSearch&sortType=desc&pageSize=30&keywords={q}",
}


def search_image_urls(product_name: str, source: str = "all", max_images: int = 10) -> list[dict]:
    """搜索产品图片URL"""
    results = []
    query = quote(product_name)

    try:
        if source == "tmall" or source == "all":
            # 淘宝/天猫图片搜索
            url = f"https://suggest.taobao.com/sug?q={query}&code=utf-8"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            # 返回的是淘宝搜索页面，需要解析
            search_url = f"https://s.taobao.com/search?q={query}&imgfile=&initiative_id=staobaoz"
            results.append({"source": "tmall", "url": search_url, "type": "search_page"})

        if source == "jd" or source == "all":
            search_url = f"https://search.jd.com/Search?keyword={query}&enc=utf-8"
            results.append({"source": "jd", "url": search_url, "type": "search_page"})

        if source == "xiaohongshu" or source == "all":
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={quote(product_name)}&type=51"
            results.append({"source": "xiaohongshu", "url": search_url, "type": "search_page"})

        if source == "brand" or source == "all":
            # 通过必应搜索品牌官网
            search_url = f"https://www.bing.com/search?q={query}+官方网站"
            results.append({"source": "brand", "url": search_url, "type": "search_page"})

        if source == "1688" or source == "all":
            search_url = f"https://s.1688.com/youyuan/index.htm?tab=mallSearch&sortType=desc&pageSize=30&keywords={query}"
            results.append({"source": "1688", "url": search_url, "type": "search_page"})

    except Exception as e:
        print(f"搜索 {source} 时出错: {e}")

    return results


def download_image(url: str, save_path: Path, timeout: int = 15) -> bool:
    """下载单张图片"""
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        resp.raise_for_status()

        # 检查是否是图片
        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type and not url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            # 尝试从URL猜测
            pass

        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"下载失败 {url}: {e}")
        return False


def save_product_images_meta(product_name: str, images: list[dict], product_dir: Path):
    """保存产品图片元数据"""
    meta = {
        "product": product_name,
        "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "images": images
    }
    meta_path = product_dir / "images_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta_path


def main(product_name: str, output_dir: str = None, max_images: int = 10):
    """主流程：搜索并保存产品图片"""
    print(f"🔍 开始搜索产品图片: {product_name}")

    # 创建产品目录
    if output_dir:
        product_dir = Path(output_dir) / product_name
    else:
        product_dir = PRODUCTS_DIR / product_name.replace(" ", "_")

    images_dir = product_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 获取搜索结果页面列表
    search_results = search_image_urls(product_name, max_images=max_images)
    print(f"📋 获取到 {len(search_results)} 个搜索来源")

    # Step 2: 返回搜索链接，供人工确认官方产品图
    # （自动化精准查找需要人工确认，因为不同来源的图片质量差异大）
    saved_images = []

    for result in search_results:
        print(f"  [{result['source']}] {result['url']}")

    # Step 3: 用户确认后，下载产品图片
    # 返回元数据供 VideoProducer 后续使用
    meta = save_product_images_meta(product_name, search_results, product_dir)
    print(f"\n✅ 搜索结果已保存: {meta}")
    print(f"📁 图片保存目录: {images_dir}")
    print(f"\n💡 建议: 打开上述搜索链接，人工确认并下载 3-5 张高清产品图放入 {images_dir}")

    return {
        "product": product_name,
        "search_sources": search_results,
        "images_dir": str(images_dir),
        "meta_path": str(meta)
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python search_product_images.py <产品名称>")
        sys.exit(1)

    product = sys.argv[1]
    main(product)
