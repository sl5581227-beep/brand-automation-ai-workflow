#!/usr/bin/env python3
"""
Subtitle-Optimizer 核心脚本
优化字幕大小和位置，确保在9:16竖屏视频中完整显示所有字幕内容
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from moviepy import VideoFileClip, TextClip, CompositeVideoClip

FFMPEG_BIN = Path(os.environ.get(
    "FFMPEG_PATH",
    r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
))


def get_video_info(video_path: str) -> dict:
    """获取视频信息"""
    import json
    cmd = [str(FFMPEG_BIN), "-v", "quiet", "-print_format", "json",
           "-show_format", "-show_streams", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            return {
                "width": int(stream["width"]),
                "height": int(stream["height"]),
                "fps": eval(stream.get("r_frame_rate", "30/1"))
            }
    return {"width": 1080, "height": 1920, "fps": 30}


def calculate_subtitle_params(video_height: int, is_9x16: bool = True) -> dict:
    """计算最优字幕参数"""
    if is_9x16 and video_height >= 1080:
        # 9:16竖屏优化参数
        font_size = video_height // 22  # 约87px for 1920p
        safe_bottom_pct = 0.15  # 底部15%为安全区
        line_spacing = 1.3
        vertical_position = 0.85  # 距顶部85%的位置
    else:
        # 默认参数
        font_size = video_height // 18
        safe_bottom_pct = 0.10
        line_spacing = 1.2
        vertical_position = 0.88

    return {
        "font_size": max(font_size, 28),  # 最小28px
        "safe_bottom_pct": safe_bottom_pct,
        "line_spacing": line_spacing,
        "vertical_position": vertical_position,
        "stroke_width": 3
    }


def optimize_subtitles_moviepy(video_path: str, output_path: str = None,
                               subtitles: list = None) -> str:
    """
    使用MoviePy重新烧录优化后的字幕

    Args:
        video_path: 输入视频路径
        output_path: 输出路径（默认加_optimized suffix）
        subtitles: 字幕列表 [(start, end, text), ...]

    Returns:
        优化后的视频路径
    """
    if not output_path:
        p = Path(video_path)
        output_path = str(p.parent / f"{p.stem}_optimized{p.suffix}")

    # 获取视频信息
    video_info = get_video_info(video_path)
    height = video_info["height"]
    is_9x16 = (height / video_info["width"]) >= 1.7  # 接近2就是竖屏

    # 计算最优字幕参数
    params = calculate_subtitle_params(height, is_9x16)

    print(f"📐 视频信息: {video_info['width']}x{height}")
    print(f"📝 字幕参数: 字体{params['font_size']}px, 位置{params['vertical_position']*100}%")

    # 默认字幕（如果没有提供）
    if subtitles is None:
        subtitles = [
            (0, 5, "夏天必备！轻上椰子水\nSummer essential! Qingshang Coconut Water"),
            (5, 15, "甄选东南亚新鲜椰子\nSelected fresh Southeast Asian coconuts"),
            (15, 25, "运动后来一瓶，快速补水\nPerfect after workout - rapid hydration!"),
            (25, 35, "零糖零脂低卡路里\nZero sugar, zero fat - refreshing!"),
            (35, 45, "轻上大品牌，品质有保障\nQingshang - trusted brand!"),
            (45, 55, "关注我们，了解更多\nFollow us for more healthy drinks!"),
        ]

    # 加载视频
    print(f"Loading video: {video_path}")
    video = VideoFileClip(video_path)

    txt_clips = []
    for start, end, text in subtitles:
        duration = end - start

        # 创建字幕
        txt_clip = (
            TextClip(
                text=text,
                font_size=params["font_size"],
                color="white",
                stroke_color="black",
                stroke_width=params["stroke_width"],
                font="C:/Windows/Fonts/msyh.ttc",
                text_align="center",
                horizontal_align="center",
                vertical_align="center",
                method="label",
                duration=duration
            )
            .with_start(start)
            .with_position(("center", params["vertical_position"]), relative=True)
        )
        txt_clips.append(txt_clip)

    # 合成
    print("Compositing video with optimized subtitles...")
    final = CompositeVideoClip([video] + txt_clips, size=video.size)

    # 输出
    print(f"Writing output: {output_path}")
    with tempfile.TemporaryDirectory() as tmpdir:
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=f"{tmpdir}/temp_audio.m4a",
            remove_temp=True,
            threads=4,
            fps=30,
            preset="fast"
        )

    video.close()
    final.close()

    print(f"✅ 字幕优化完成: {output_path}")
    return output_path


def optimize_subtitle_srt(srt_path: str, output_path: str = None,
                         font_size: int = None, margin_v: int = 20) -> str:
    """
    生成优化后的ASS字幕文件

    Args:
        srt_path: 原始SRT文件路径
        output_path: 输出ASS文件路径
        font_size: 字体大小
        margin_v: 垂直边距

    Returns:
        优化后的ASS文件路径
    """
    if not output_path:
        output_path = srt_path.replace(".srt", "_optimized.ass")

    # 生成ASS头
    ass_header = f"""[Script Info]
Title: Optimized Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
AspectRatio: 0.5625
BorderStyle: 1
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size or 44},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,3,2,20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # 读取SRT并转换
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_content = f.read()

    ass_events = []
    for block in srt_content.strip().split("\n\n"):
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            # 解析时间
            time_line = lines[1]
            start_str, end_str = time_line.split(" --> ")
            start = start_str.replace(",", ".")
            end = end_str.replace(",", ".")

            # 文字内容
            text = "\\N".join(lines[2:])  # \N 是ASS的换行符

            ass_events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    # 写入ASS文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        f.write("\n".join(ass_events))

    print(f"✅ ASS字幕优化完成: {output_path}")
    return output_path


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("""用法:
  python optimize_subtitles.py <视频路径> [输出路径]

示例:
  python optimize_subtitles.py final_video.mp4
  python optimize_subtitles.py final_video.mp4 output_optimized.mp4
""")
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    result = optimize_subtitles_moviepy(video_path, output_path)
    print(f"\n输出: {result}")


if __name__ == "__main__":
    main()
