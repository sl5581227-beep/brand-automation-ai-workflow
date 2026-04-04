#!/usr/bin/env python3
"""
video-watermark-remover 核心脚本
去除AI水印 + 调整画面比例为TikTok/抖音适用 (9:16 1080x1920)
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# ============== 配置 ==============
PROJECT_ROOT = Path(__file__).parent.parent.parent
FFMPEG_BIN = Path(os.environ.get(
    "FFMPEG_PATH",
    r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
))

# TikTok/抖音 标准 9:16 竖屏
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


def detect_watermark_position(video_path: str) -> dict:
    """检测水印位置（AI平台通常在右下角或角落）"""
    # 默认AI水印位置（右下角）
    return {
        "position": "bottom-right",
        "x": "W-w-20",  # 右下角偏移20px
        "y": "H-h-20",
        "width_ratio": 0.3,  # 水印占画面30%
        "height_ratio": 0.08
    }


def remove_watermark_ffmpeg(video_path: str, output_path: str = None,
                            watermark_pos: dict = None) -> str:
    """
    使用FFmpeg裁剪去除水印区域
    
    Args:
        video_path: 输入视频路径
        output_path: 输出路径（默认加_wm suffix）
        watermark_pos: 水印位置信息
    
    Returns:
        去除水印后的视频路径
    """
    if not output_path:
        p = Path(video_path)
        output_path = str(p.parent / f"{p.stem}_nowm{p.suffix}")

    if watermark_pos is None:
        watermark_pos = detect_watermark_position(video_path)

    # 获取原视频信息
    probe_cmd = [
        str(FFMPEG_BIN), "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", video_path
    ]
    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
    info = json.loads(probe_result.stdout)

    # 找到视频流
    video_stream = None
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break

    if not video_stream:
        raise ValueError(f"无法读取视频流: {video_path}")

    width = int(video_stream["width"])
    height = int(video_stream["height"])

    # 计算水印区域并裁剪掉
    # AI水印通常在右下角，我们裁剪掉右下角区域
    crop_width = int(width * 0.7)  # 保留70%宽度
    crop_height = int(height * 0.85)  # 保留85%高度

    # 从左上角开始裁剪
    crop_x = 0
    crop_y = 0

    filter_str = f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y}"

    cmd = [
        str(FFMPEG_BIN), "-y",
        "-i", video_path,
        "-vf", filter_str,
        "-c:a", "copy",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd)

    print(f"✅ 水印已去除: {output_path}")
    return output_path


def resize_to_9x16(video_path: str, output_path: str = None,
                   target_width: int = TARGET_WIDTH,
                   target_height: int = TARGET_HEIGHT) -> str:
    """
    将视频调整为9:16竖屏比例（TikTok/抖音标准）
    
    策略：
    1. 如果视频是横屏（landscape），先裁剪为竖屏比例，再缩放
    2. 如果视频是竖屏（portrait），直接缩放
    3. 填充黑色背景
    """
    if not output_path:
        p = Path(video_path)
        output_path = str(p.parent / f"{p.stem}_9x16{p.suffix}")

    # 获取视频信息
    probe_cmd = [
        str(FFMPEG_BIN), "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", video_path
    ]
    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
    info = json.loads(probe_result.stdout)

    video_stream = None
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break

    if not video_stream:
        raise ValueError(f"无法读取视频流: {video_path}")

    width = int(video_stream["width"])
    height = int(video_stream["height"])

    # 计算缩放比例
    # 目标: 1080x1920 (9:16)
    scale_width = target_width
    scale_height = target_height

    # 计算填充
    # 如果视频宽高比大于9:16，说明视频更宽，需要在左右填充
    # 如果视频宽高比小于9:16，说明视频更高，需要在上下裁剪或填充
    video_ratio = width / height
    target_ratio = target_width / target_height  # 0.5625

    if video_ratio > target_ratio:
        # 视频更宽（如横屏16:9），需要在左右填充
        # 先缩放高度到1920，宽度按比例
        scale_filter = f"scale={scale_width}:-1:flags=lanczos"
        pad_filter = f"pad={target_width}:{target_height}}:(ow-iw)/2:(oh-ih)/2:color=black"
        filter_complex = f"{scale_filter},{pad_filter}"
    else:
        # 视频更窄或已经是竖屏，直接缩放并填充
        scale_filter = f"scale=-1:{scale_height}:flags=lanczos"
        pad_filter = f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black"
        filter_complex = f"{scale_filter},{pad_filter}"

    cmd = [
        str(FFMPEG_BIN), "-y",
        "-i", video_path,
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd)

    print(f"✅ 已调整为9:16竖屏: {output_path}")
    return output_path


def process_video(video_path: str, output_dir: str = None,
                 remove_watermark: bool = True) -> dict:
    """
    完整处理流程：去水印 + 调整比例
    
    Args:
        video_path: 输入视频路径
        output_dir: 输出目录（默认与输入同目录）
        remove_watermark: 是否去除水印
    
    Returns:
        处理结果信息
    """
    print(f"🎬 开始处理视频: {video_path}")
    start_time = datetime.now()

    input_path = Path(video_path)
    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = input_path.parent

    # Step 1: 去除水印（如果需要）
    if remove_watermark:
        temp_no_wm = output_dir / f"{input_path.stem}_nowm{input_path.suffix}"
        no_wm_path = remove_watermark_ffmpeg(
            video_path,
            str(temp_no_wm),
            detect_watermark_position(video_path)
        )
    else:
        no_wm_path = video_path

    # Step 2: 调整到9:16
    final_output = output_dir / f"{input_path.stem}_9x16{input_path.suffix}"
    final_path = resize_to_9x16(no_wm_path, str(final_output))

    elapsed = (datetime.now() - start_time).total_seconds()

    return {
        "input": video_path,
        "watermark_removed": remove_watermark,
        "no_wm_path": no_wm_path if remove_watermark else None,
        "final_path": final_path,
        "target_resolution": f"{TARGET_WIDTH}x{TARGET_HEIGHT}",
        "aspect_ratio": "9:16",
        "elapsed_seconds": elapsed
    }


def batch_process(video_paths: list, output_dir: str = None) -> list:
    """批量处理多个视频"""
    results = []
    for path in video_paths:
        try:
            result = process_video(path, output_dir)
            results.append(result)
        except Exception as e:
            print(f"❌ 处理失败 {path}: {e}")
            results.append({"input": path, "error": str(e)})
    return results


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("""用法:
  python remove_watermark_and_resize.py <视频路径> [输出目录]

示例:
  # 处理单个视频
  python remove_watermark_and_resize.py clip.mp4

  # 指定输出目录
  python remove_watermark_and_resize.py clip.mp4 ./output/

  # 保留水印（只调整比例）
  python remove_watermark_and_resize.py clip.mp4 --no-watermark
""")
        sys.exit(1)

    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    remove_wm = "--no-watermark" not in sys.argv

    result = process_video(video_path, output_dir, remove_watermark=remove_wm)
    print(f"\n✅ 处理完成!")
    print(f"   输出路径: {result['final_path']}")
    print(f"   分辨率: {result['target_resolution']}")
    print(f"   耗时: {result['elapsed_seconds']:.1f}秒")


if __name__ == "__main__":
    main()
