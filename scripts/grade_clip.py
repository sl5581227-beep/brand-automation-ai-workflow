#!/usr/bin/env python3
"""
clip_grader.py - AI镜头质量评分系统
对生成的视频镜头进行多维度评分，判断是否合格
"""
import cv2
import numpy as np
import json
import os
import sys

# 产品标准色（HSV范围）
PRODUCT_COLORS = {
    "QSYZ-001": {  # 椰子水 - 清澈透明/淡黄
        "name": "椰子水",
        "hsv_low": np.array([0, 0, 150]),     # 高亮度，低饱和度（透明感）
        "hsv_high": np.array([45, 50, 255]),   # 淡黄到白色范围
        "description": "清澈透明液体",
        "banned_colors": ["白色乳浊液"],  # 乳白色是违规的
    },
    "QSXM-001": {  # 零糖生椰 - 乳白色
        "name": "零糖生椰",
        "hsv_low": np.array([0, 0, 220]),     # 高亮度白色
        "hsv_high": np.array([30, 15, 255]),   # 暖白色/米白色
        "description": "乳白色液体",
    },
    "QSXM-002": {  # 西梅汁 - 深紫红色
        "name": "西梅汁",
        "hsv_low": np.array([120, 30, 30]),   # 紫色范围
        "hsv_high": np.array([170, 200, 120]), # 深紫色
        "description": "深紫红色液体",
    }
}


def extract_frames(video_path, num_frames=5):
    """从视频提取关键帧"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    
    frames = []
    for i in range(num_frames):
        frame_idx = int((i / num_frames) * total_frames)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    
    cap.release()
    return frames


def analyze_frame_color(frame):
    """分析单帧颜色分布，返回颜色特征"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 计算颜色统计
    h, s, v = cv2.split(hsv)
    
    # 高亮度低饱和度像素比例（判断透明/清澈程度）
    bright_transparent = np.sum((v > 180) & (s < 30)) / (v.size) * 100
    
    # 暗色像素比例（判断是否有深色液体）
    dark_pixels = np.sum(v < 80) / (v.size) * 100
    
    # 白色像素（判断是否有乳白/浓稠效果）
    white_pixels = np.sum((v > 220) & (s < 20)) / (v.size) * 100
    
    return {
        "bright_transparent_pct": bright_transparent,
        "dark_pixels_pct": dark_pixels,
        "white_pixels_pct": white_pixels,
        "avg_saturation": np.mean(s),
        "avg_brightness": np.mean(v)
    }


def check_product_color_match(frames, product_id):
    """
    检查视频中的液体颜色是否符合产品标准
    
    返回：
        match_score: 0-30分
        details: 详细分析
    """
    if product_id not in PRODUCT_COLORS:
        return 15, {"error": "未知产品ID"}
    
    product = PRODUCT_COLORS[product_id]
    all_stats = [analyze_frame_color(f) for f in frames]
    
    avg_transparent = np.mean([s["bright_transparent_pct"] for s in all_stats])
    avg_white = np.mean([s["white_pixels_pct"] for s in all_stats])
    avg_sat = np.mean([s["avg_saturation"] for s in all_stats])
    
    details = {
        "avg_transparency": avg_transparent,
        "avg_white": avg_white,
        "avg_saturation": avg_sat,
        "product_expected": product["description"]
    }
    
    if product_id == "QSYZ-001":
        # 椰子水应该是清澈透明的
        if avg_transparent > 30 and avg_sat < 30:
            score = 30
            details["verdict"] = "[OK] Clear transparent liquid matches coconut water"
        elif avg_transparent > 20 and avg_white < 20:
            score = 20
            details["verdict"] = "[WARN] Liquid is clear but may not be transparent enough"
        else:
            score = 5
            details["verdict"] = "[FAIL] Liquid is not transparent, may not be coconut water"
    
    elif product_id == "QSXM-001":
        # 生椰应该是乳白色的
        if avg_white > 25:
            score = 30
            details["verdict"] = "[OK] Milky white liquid matches coconut milk"
        elif avg_white > 15:
            score = 20
            details["verdict"] = "[WARN] Has white but not creamy enough"
        else:
            score = 5
            details["verdict"] = "[FAIL] No milky white color, may be other product"
    
    elif product_id == "QSXM-002":
        # 西梅汁应该是深紫色的
        if avg_sat > 40 and avg_transparent < 30:
            score = 30
            details["verdict"] = "[OK] Deep purple liquid matches prune juice"
        elif avg_sat > 25:
            score = 20
            details["verdict"] = "[WARN] Purple detected but saturation low"
        else:
            score = 5
            details["verdict"] = "[FAIL] No purple liquid detected"
    
    else:
        score = 15
    
    return score, details


def grade_clip(video_path, product_id, verbose=True):
    """
    对单个视频镜头评分
    
    返回：评分结果字典
    """
    product = PRODUCT_COLORS.get(product_id, {})
    
    # 提取帧
    frames = extract_frames(video_path, num_frames=5)
    if not frames:
        return {"error": "无法读取视频", "total_score": 0, "pass": False}
    
    # 1. 产品颜色匹配度 (30分)
    color_score, color_details = check_product_color_match(frames, product_id)
    
    # 2. 卖点呈现 (25分) - 通过帧分析估算
    # 简单判断：视频明亮、清晰
    frame = frames[len(frames)//2]
    brightness = np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    if brightness > 100:
        selling_score = 20
    elif brightness > 70:
        selling_score = 15
    else:
        selling_score = 8
    
    # 3. 画面质量 (20分)
    # 清晰度通过边缘检测估算
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var > 500:
        quality_score = 18
    elif laplacian_var > 200:
        quality_score = 14
    else:
        quality_score = 8
    
    # 4. 品牌识别 (15分) - 简化版，实际需要OCR
    # 暂时给一个基础分
    brand_score = 10
    
    # 5. 创意价值 (10分) - 简化版
    creative_score = 7
    
    # 总分
    total = color_score + selling_score + quality_score + brand_score + creative_score
    
    result = {
        "total_score": round(total, 1),
        "pass": total >= 70,
        "dimensions": {
            "product_match": {"score": color_score, "max": 30, "details": color_details},
            "selling_point": {"score": selling_score, "max": 25},
            "visual_quality": {"score": quality_score, "max": 20, "note": f"laplacian_var={laplacian_var:.0f}"},
            "brand_recognition": {"score": brand_score, "max": 15},
            "creative_value": {"score": creative_score, "max": 10}
        },
        "product_id": product_id,
        "product_name": product.get("name", "未知")
    }
    
    if verbose:
        status = "PASS" if result["pass"] else "FAIL"
        print(f"\n[GRADE] Video: {os.path.basename(video_path)}")
        print(f"[GRADE] Product: {product.get('name', 'Unknown')} ({product_id})")
        print(f"[GRADE] Score: {total:.0f}/100 - {status}")
        print(f"  Product Match: {color_score}/30 - {color_details.get('verdict', '')}")
        print(f"  Selling Point: {selling_score}/25")
        print(f"  Visual Quality: {quality_score}/20")
        print(f"  Brand Recognition: {brand_score}/15")
        print(f"  Creative Value: {creative_score}/10")
    
    return result


def grade_batch(clips_dir, product_id):
    """批量评分"""
    results = []
    for fname in sorted(os.listdir(clips_dir)):
        if fname.endswith(('.mp4', '.avi', '.mov')):
            fpath = os.path.join(clips_dir, fname)
            r = grade_clip(fpath, product_id, verbose=True)
            r["file"] = fname
            results.append(r)
    
    # 统计
    passed = sum(1 for r in results if r.get("pass", False))
    avg_score = np.mean([r["total_score"] for r in results])
    
    print(f"\n[BATCH] Total: {len(results)} clips")
    print(f"[BATCH] Passed: {passed} ({passed/len(results)*100:.0f}%)")
    print(f"[BATCH] Average Score: {avg_score:.1f}/100")
    
    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python grade_clip.py <视频路径> <产品ID>")
        print("产品ID: QSYZ-001=椰子水, QSXM-001=零糖生椰, QSXM-002=西梅汁")
        sys.exit(1)
    
    video_path = sys.argv[1]
    product_id = sys.argv[2]
    
    if not os.path.exists(video_path):
        print(f"文件不存在: {video_path}")
        sys.exit(1)
    
    result = grade_clip(video_path, product_id)
    
    # 保存结果
    output = video_path.replace(".mp4", "_grade.json")
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[SAVE] Grade saved: {output}")
