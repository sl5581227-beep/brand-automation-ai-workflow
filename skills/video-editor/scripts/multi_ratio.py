#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Ratio Video Converter - 多比例输出
支持 9:16, 1:1, 16:9 三种比例
"""

import os
import sys
import subprocess
from pathlib import Path

FFMPEG = Path(r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe")

def convert_to_1x1(input_path, output_path):
    """9:16 -> 1:1 (1080x1080)"""
    # 从9:16中心裁剪上方区域（保持产品主体）
    # 9:16 = 1080x1920, 1:1 = 1080x1080
    # 裁剪中间1080x1080区域
    cmd = [
        str(FFMPEG), "-y", "-i", str(input_path),
        "-vf", "crop=1080:1080:0:360",  # 从y=360开始裁剪（居中偏上）
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0

def convert_to_16x9(input_path, output_path):
    """9:16 -> 16:9 (1920x1080)"""
    # 上下加黑边
    cmd = [
        str(FFMPEG), "-y", "-i", str(input_path),
        "-vf", "scale=1920:1920:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0

def upscale_to_1080(input_path, output_path):
    """升频到1080p"""
    cmd = [
        str(FFMPEG), "-y", "-i", str(input_path),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0

def generate_multi_ratio(input_path, output_dir, base_name):
    """生成多比例版本"""
    print(f"  [Multi-Ratio] 输入: {input_path}")
    
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # 1. 9:16 原版（已处理）
    path_9x16 = Path(output_dir) / f"{base_name}_9x16.mp4"
    if input_path != str(path_9x16):
        import shutil
        shutil.copy2(input_path, path_9x16)
    results["9x16"] = str(path_9x16)
    print(f"    9:16 -> {path_9x16.name}")
    
    # 2. 1:1 版本
    path_1x1 = Path(output_dir) / f"{base_name}_1x1.mp4"
    if convert_to_1x1(input_path, path_1x1):
        results["1x1"] = str(path_1x1)
        print(f"    1:1 -> {path_1x1.name}")
    else:
        print(f"    [WARN] 1:1 转换失败")
        results["1x1"] = None
    
    # 3. 16:9 版本
    path_16x9 = Path(output_dir) / f"{base_name}_16x9.mp4"
    if convert_to_16x9(input_path, path_16x9):
        results["16x9"] = str(path_16x9)
        print(f"    16:9 -> {path_16x9.name}")
    else:
        print(f"    [WARN] 16:9 转换失败")
        results["16x9"] = None
    
    return results

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: multi_ratio.py <input> <output_dir> <base_name>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    base_name = sys.argv[3]
    
    results = generate_multi_ratio(input_path, output_dir, base_name)
    print(f"\n结果: {results}")
