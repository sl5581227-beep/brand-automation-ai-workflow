#!/usr/bin/env python3
"""
Product-Visual-Anchor 核心脚本
从产品手册中提取视觉锚点，建立标准外观数据库
"""

import os
import sys
import json
import zipfile
import shutil
import subprocess
from pathlib import Path
from PIL import Image
import hashlib

PROJECT_ROOT = Path(__file__).parent.parent.parent
FFMPEG_BIN = Path(os.environ.get(
    "FFMPEG_PATH",
    r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
))

# 产品手册目录
MANUAL_DIRS = [
    r"C:\Users\Administrator\Desktop\素材01",
    r"C:\Users\Administrator\Desktop\轻上跨境计划"
]

# 知识库基础路径
KB_BASE = PROJECT_ROOT / "knowledge_base" / "products"


def extract_images_from_pptx(pptx_path: str, output_dir: Path) -> list:
    """从PPTX文件中提取所有图片"""
    images = []
    try:
        with zipfile.ZipFile(pptx_path, 'r') as z:
            for name in z.namelist():
                if name.startswith('ppt/media/') and (name.endswith('.png') or name.endswith('.jpg') or name.endswith('.jpeg')):
                    # 提取文件
                    safe_name = name.replace('/', '_').replace('\\', '_')
                    out_path = output_dir / safe_name
                    with z.open(name) as src, open(out_path, 'wb') as dst:
                        dst.write(z.read(name))
                    images.append(str(out_path))
                    print(f"  Extracted: {safe_name}")
    except Exception as e:
        print(f"  Error extracting from {pptx_path}: {e}")
    return images


def extract_images_from_pdf(pdf_path: str, output_dir: Path, dpi: int = 150) -> list:
    """从PDF中提取图片（使用FFmpeg）"""
    images = []
    try:
        # 使用FFmpeg从PDF提取页面为图片
        output_pattern = str(output_dir / "page_%03d.png")
        cmd = [
            str(FFMPEG_BIN), "-y",
            "-i", pdf_path,
            "-vf", f"scale={dpi}:-1",
            "-q:v", "2",
            output_pattern
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # 找到提取的图片
            for img_file in output_dir.glob("page_*.png"):
                images.append(str(img_file))
            print(f"  Extracted {len(images)} pages from PDF")
    except Exception as e:
        print(f"  Error extracting from PDF {pdf_path}: {e}")
    return images


def analyze_image(image_path: str) -> dict:
    """分析单张图片，提取视觉特征"""
    try:
        with Image.open(image_path) as img:
            # 转换为RGB
            img = img.convert('RGB')
            
            # 提取主色调（简化版：采样缩略图）
            small = img.resize((100, 100))
            pixels = list(small.getdata())
            
            # 简单的主色调提取
            r_sum = sum(p[0] for p in pixels)
            g_sum = sum(p[1] for p in pixels)
            b_sum = sum(p[2] for p in pixels)
            count = len(pixels)
            
            avg_color = f"#{r_sum//count:02x}{g_sum//count:02x}{b_sum//count:02x}"
            
            # 尺寸
            width, height = img.size
            aspect_ratio = width / height
            
            # 判断瓶形（简化）
            if aspect_ratio > 0.8 and aspect_ratio < 1.2:
                shape = "方形/圆柱形"
            elif aspect_ratio > 2:
                shape = "横版/扁平"
            elif aspect_ratio < 0.5:
                shape = "竖版/高瓶"
            else:
                shape = "异形"
            
            return {
                "path": image_path,
                "avg_color": avg_color,
                "width": width,
                "height": height,
                "aspect_ratio": round(aspect_ratio, 2),
                "shape_estimate": shape,
                "file_size": os.path.getsize(image_path)
            }
    except Exception as e:
        return {"path": image_path, "error": str(e)}


def scan_manual_directories() -> dict:
    """扫描所有产品手册目录"""
    all_files = {
        "pptx": [],
        "pdf": [],
        "images": []
    }
    
    for manual_dir in MANUAL_DIRS:
        if not os.path.exists(manual_dir):
            print(f"  Directory not found: {manual_dir}")
            continue
            
        print(f"Scanning: {manual_dir}")
        
        # 遍历目录
        for root, dirs, files in os.walk(manual_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                full_path = os.path.join(root, file)
                
                if ext == '.pptx':
                    all_files["pptx"].append(full_path)
                elif ext == '.pdf':
                    all_files["pdf"].append(full_path)
                elif ext in ['.png', '.jpg', '.jpeg']:
                    all_files["images"].append(full_path)
    
    return all_files


def build_product_anchors(product_name: str = None) -> dict:
    """构建产品视觉锚点"""
    print(f"Building visual anchors for: {product_name or 'all products'}")
    
    # Step 1: 扫描手册目录
    print("\n[1/4] Scanning manual directories...")
    all_files = scan_manual_directories()
    
    print(f"  Found: {len(all_files['pptx'])} PPTX, {len(all_files['pdf'])} PDF, {len(all_files['images'])} images")
    
    # Step 2: 创建输出目录
    if product_name:
        product_dir = KB_BASE / product_name.replace(" ", "_") / "anchors"
    else:
        product_dir = KB_BASE / "anchors"
    product_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 3: 提取图片
    print("\n[2/4] Extracting images from documents...")
    all_images = []
    
    # 从PPTX提取
    temp_dir = product_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    for pptx in all_files["pptx"]:
        print(f"  Processing: {os.path.basename(pptx)}")
        imgs = extract_images_from_pptx(pptx, temp_dir)
        all_images.extend(imgs)
    
    # 从PDF提取
    for pdf in all_files["pdf"]:
        print(f"  Processing: {os.path.basename(pdf)}")
        imgs = extract_images_from_pdf(pdf, temp_dir)
        all_images.extend(imgs)
    
    # 复制已有的图片
    for img in all_files["images"]:
        try:
            shutil.copy(img, temp_dir / os.path.basename(img))
            all_images.append(img)
        except:
            pass
    
    print(f"  Total images extracted: {len(all_images)}")
    
    # Step 4: 分析每张图片
    print("\n[3/4] Analyzing images...")
    image_analysis = []
    
    for img_path in all_images[:50]:  # 限制分析数量
        try:
            analysis = analyze_image(img_path)
            if "error" not in analysis:
                image_analysis.append(analysis)
                print(f"  {os.path.basename(img_path)}: {analysis['avg_color']}, {analysis['shape_estimate']}")
        except Exception as e:
            print(f"  Error analyzing {img_path}: {e}")
    
    # Step 5: 生成视觉锚点报告
    print("\n[4/4] Building visual anchor report...")
    
    # 聚类主色调
    color_groups = {}
    for item in image_analysis:
        color = item["avg_color"]
        if color not in color_groups:
            color_groups[color] = []
        color_groups[color].append(item)
    
    # 取最常见的颜色
    sorted_colors = sorted(color_groups.keys(), key=lambda c: len(color_groups[c]), reverse=True)
    primary_colors = sorted_colors[:5] if len(sorted_colors) >= 5 else sorted_colors
    
    # 聚类形状
    shape_groups = {}
    for item in image_analysis:
        shape = item["shape_estimate"]
        if shape not in shape_groups:
            shape_groups[shape] = []
        shape_groups[shape].append(item)
    
    sorted_shapes = sorted(shape_groups.keys(), key=lambda s: len(shape_groups[s]), reverse=True)
    primary_shapes = sorted_shapes[:3] if len(sorted_shapes) >= 3 else sorted_shapes
    
    anchor_report = {
        "product_name": product_name or "未命名产品",
        "created_at": subprocess.run(["python", "-c", "from datetime import datetime; print(datetime.now().isoformat())"], 
                                     capture_output=True, text=True).stdout.strip(),
        "source_files": {
            "pptx": all_files["pptx"],
            "pdf": all_files["pdf"],
            "images": all_files["images"]
        },
        "visual_anchors": {
            "primary_colors": primary_colors,
            "primary_shapes": primary_shapes,
            "color_distribution": {c: len(color_groups[c]) for c in primary_colors},
            "shape_distribution": {s: len(shape_groups[s]) for s in primary_shapes}
        },
        "images_analyzed": len(image_analysis),
        "image_analysis_sample": image_analysis[:10],
        "output_directory": str(product_dir)
    }
    
    # 保存报告
    report_path = product_dir / "visual_anchor_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(anchor_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Visual anchor report saved: {report_path}")
    print(f"  Primary colors: {primary_colors}")
    print(f"  Primary shapes: {primary_shapes}")
    
    # 清理临时目录
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
    
    return anchor_report


def main():
    """命令行入口"""
    product_name = sys.argv[1] if len(sys.argv) > 1 else None
    result = build_product_anchors(product_name)
    print(f"\n{json.dumps(result, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()
