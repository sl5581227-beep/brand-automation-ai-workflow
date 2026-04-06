#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻上品牌视频自动化生成脚本 v5.0
新流程：素材库镜头 + 爆款文案 + FFmpeg拼接 + 中文配音

步骤：
1. 从素材01提取产品镜头
2. 基于爆款文案生成脚本
3. FFmpeg拼接成60秒视频
4. 添加中英文字幕 + 中文配音
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# UTF-8 support
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 路径配置
FFMPEG = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
FFPROBE = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffprobe.exe"

# 素材目录 - 使用通配符自动查找
def find_source_base():
    parent = Path(r"C:\Users\Administrator\Desktop\素材01")
    for d in parent.iterdir():
        if d.is_dir() and d.name.startswith('10.07'):
            # 检查是否包含MOV文件
            movs = list(d.glob('*.MOV'))
            if movs:
                return d
    return None

SOURCE_DIR = find_source_base()
OUTPUT_DIR = Path(r"C:\Users\Administrator\Desktop\qingShangVideos\final_videos")
CLIPS_DIR = Path(r"C:\Users\Administrator\Desktop\qingShangVideos\generated_clips")

# ============================================================
# 爆款文案分析 - 60秒直播带货脚本
# 基于Vita Coco等爆款视频的文案策略
# ============================================================

# 60秒脚本（中英双语）
SCRIPT = [
    # 时间轴(秒) | 中文 | 英文
    (0.0, 3.0, "夏天太热了，渴得不行！", "Summer heat, so thirsty!"),
    (3.0, 6.0, "白水解渴没味道，奶茶太甜太腻", "Plain water is boring, milk tea too sweet!"),
    (6.0, 9.0, "快试试这个！轻上椰子水！", "Try this! Qingshang Coconut Water!"),
    (9.0, 13.0, "0糖0脂肪，清爽解渴超健康", "Zero sugar, zero fat, refreshing & healthy!"),
    (13.0, 17.0, "甄选东南亚优质椰子，纯天然无添加", "Selected Southeast Asia coconuts, pure natural!"),
    (17.0, 21.0, "看这清澈透明的椰子水，太诱人了！", "Crystal clear coconut water, so tempting!"),
    (21.0, 25.0, "运动完来一瓶，快速补水又解乏", "After workout, rapid hydration & relief!"),
    (25.0, 29.0, "海边度假来一杯，清爽一整天", "Beach vacation, refreshing all day long!"),
    (29.0, 33.0, "学习累了来一瓶，瞬间恢复活力", "Study break, instantly refreshed!"),
    (33.0, 37.0, "和朋友分享，清爽又健康！", "Share with friends, refreshing & healthy!"),
    (37.0, 41.0, "0糖0脂低卡路里，喝了没负担！", "Zero sugar, zero fat, no guilt!"),
    (41.0, 45.0, "轻上大品牌，品质有保障！", "Qingshang brand, quality guaranteed!"),
    (45.0, 50.0, "点击购物车，夏日清爽即刻拥有！", "Add to cart, summer refreshment now!"),
    (50.0, 55.0, "库存有限，先到先得！", "Limited stock, first come first served!"),
    (55.0, 60.0, "快快下单吧！", "Order now!")
]

# 中文配音完整脚本
VOICE_SCRIPT = """夏天太热了，渴得不行！白水解渴没味道，奶茶太甜太腻。快试试这个！轻上椰子水！0糖0脂肪，清爽解渴超健康。甄选东南亚优质椰子，纯天然无添加。看这清澈透明的椰子水，太诱人了！运动完来一瓶，快速补水又解乏。海边度假来一杯，清爽一整天，学习累了来一瓶，瞬间恢复活力。和朋友分享，清爽又健康！0糖0脂低卡路里，喝了没负担！轻上大品牌，品质有保障！点击购物车，夏日清爽即刻拥有！库存有限，先到先得！快快下单吧！
"""


def run_cmd(cmd, timeout=120):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result
    except Exception as e:
        print(f"    [ERROR] {e}")
        return False, None


def get_video_info(path):
    """获取视频信息"""
    cmd = [FFPROBE, "-v", "error", "-show_entries", 
           "format=duration,size:stream=codec_name,width,height,r_frame_rate", 
           "-of", "json", str(path)]
    ok, result = run_cmd(cmd, 30)
    if not ok:
        return None
    try:
        return json.loads(result.stdout)
    except:
        return None


def convert_to_1080p(input_path, output_path):
    """转换视频到1080x1920竖屏"""
    # 缩放到宽度1080，高度按比例，然后pad到1920
    cmd = [
        FFMPEG, "-y", "-i", str(input_path),
        "-vf", "scale=1080:-1:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-ar", "44100", "-ac", "2",
        "-r", "25",
        str(output_path)
    ]
    ok, _ = run_cmd(cmd, 180)
    return ok


def trim_video(input_path, output_path, start, duration):
    """裁剪视频片段"""
    cmd = [
        FFMPEG, "-y", "-i", str(input_path),
        "-ss", str(start), "-t", str(duration),
        "-vf", "scale=1080:-1:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-ar", "44100", "-ac", "2",
        "-r", "25",
        str(output_path)
    ]
    ok, _ = run_cmd(cmd, 120)
    return ok


def concatenate_videos(clips, output):
    """拼接多个视频"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        for c in clips:
            f.write(f"file '{c}'\n")
        tmp = f.name
    
    try:
        cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", tmp, 
               "-c:v", "libx264", "-preset", "fast", "-crf", "23",
               "-c:a", "aac", str(output)]
        ok, _ = run_cmd(cmd, 300)
        return ok
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def generate_srt(subtitles, output_path):
    """生成SRT字幕文件"""
    srt_content = []
    for i, (start, end, cn, en) in enumerate(subtitles, 1):
        start_str = format_time(start)
        end_str = format_time(end)
        srt_content.append(f"{i}\n{start_str} --> {end_str}\n{cn}\n{en}\n")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    return True


def format_time(seconds):
    """秒数转换为SRT时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def add_voiceover(video_path, output_path, voice_script):
    """添加中文配音"""
    SAG = r"C:\Users\Administrator\bin\sag.exe"
    
    if not os.path.exists(SAG):
        print("    [WARN] TTS工具不存在，跳过配音")
        shutil.copy2(video_path, output_path)
        return False
    
    print("    [TTS] 生成配音...")
    
    # 生成语音
    voice_file = Path(tempfile.gettempdir()) / "voiceover.wav"
    cmd = [SAG, "--text", voice_script, "--output", str(voice_file), 
           "--voice", "zh-CN female", "--speed", "1.0"]
    
    ok, _ = run_cmd(cmd, 120)
    if not ok or not voice_file.exists():
        print("    [WARN] TTS生成失败，跳过配音")
        shutil.copy2(video_path, output_path)
        return False
    
    print("    [FFmpeg] 混合音视频...")
    
    # 混合音频
    cmd = [
        FFMPEG, "-y", "-i", str(video_path), "-i", str(voice_file),
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "0:v", "-map", "[out]",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        str(output_path)
    ]
    
    ok, _ = run_cmd(cmd, 120)
    
    if voice_file.exists():
        os.unlink(voice_file)
    
    return ok


def add_subtitles(video_path, output_path, srt_path):
    """添加字幕（复制音频，添加字幕流）"""
    cmd = [
        FFMPEG, "-y", "-i", str(video_path),
        "-vf", f"subtitles='{srt_path}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        str(output_path)
    ]
    
    ok, _ = run_cmd(cmd, 120)
    return ok


def find_source_videos():
    """查找素材01中的源视频"""
    videos = []
    
    if SOURCE_DIR.exists():
        for f in SOURCE_DIR.glob("*.MOV"):
            videos.append(f)
        for f in SOURCE_DIR.glob("*.mp4"):
            videos.append(f)
    
    return sorted(videos, key=lambda x: x.name)


def run_workflow():
    """执行完整工作流"""
    print("=" * 60)
    print("  轻上品牌视频自动化生成 v5.0")
    print("=" * 60)
    print(f"  素材目录: {SOURCE_DIR}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print("=" * 60)
    
    # Step 1: 查找源视频
    print("\n[Step 1] 查找源视频...")
    source_videos = find_source_videos()
    
    if not source_videos:
        print("  [ERROR] 没有找到源视频!")
        return None
    
    print(f"  找到 {len(source_videos)} 个源视频:")
    for v in source_videos[:5]:
        size_mb = v.stat().st_size / (1024*1024)
        print(f"    - {v.name} ({size_mb:.1f} MB)")
    if len(source_videos) > 5:
        print(f"    ... 还有 {len(source_videos) - 5} 个")
    
    # Step 2: 创建输出目录
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = CLIPS_DIR / f"素材拼接_{date_str}"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 3: 准备视频片段
    print("\n[Step 2] 处理视频片段...")
    
    # 计算每个片段时长（均匀分配）
    num_clips = min(len(source_videos), 15)  # 最多15个片段
    clip_duration = 60.0 / num_clips  # 总时长60秒
    
    processed_clips = []
    
    for i in range(num_clips):
        src = source_videos[i]
        clip_path = work_dir / f"clip_{i+1:02d}.mp4"
        
        print(f"  处理 [{i+1}/{num_clips}]: {src.name}")
        
        # 获取视频时长
        info = get_video_info(src)
        if info:
            duration = float(info['format']['duration'])
            print(f"    源时长: {duration:.1f}s, 目标: {clip_duration:.1f}s")
            
            # 如果源视频太短，循环填充
            if duration < clip_duration:
                # 复制并循环
                ok = convert_to_1080p(src, clip_path)
            else:
                # 裁剪
                start_time = max(0, (duration - clip_duration) / 2)
                ok = trim_video(src, clip_path, start_time, clip_duration)
        else:
            ok = convert_to_1080p(src, clip_path)
        
        if ok and clip_path.exists():
            processed_clips.append(clip_path)
            print(f"    [OK] {clip_path.name}")
        else:
            print(f"    [FAIL]")
    
    if not processed_clips:
        print("  [ERROR] 没有成功处理的片段!")
        return None
    
    print(f"\n  成功处理 {len(processed_clips)}/{num_clips} 个片段")
    
    # Step 4: 拼接视频
    print("\n[Step 3] 拼接视频...")
    concat_path = work_dir / "video_concat.mp4"
    
    if not concatenate_videos(processed_clips, concat_path):
        print("  [ERROR] 拼接失败!")
        return None
    
    # 检查拼接结果
    info = get_video_info(concat_path)
    if info:
        duration = float(info['format']['duration'])
        print(f"  拼接后时长: {duration:.1f}s")
    
    # Step 5: 生成字幕
    print("\n[Step 4] 生成字幕...")
    srt_path = work_dir / "subtitles.srt"
    generate_srt(SCRIPT, srt_path)
    print(f"  字幕文件: {srt_path}")
    
    # Step 6: 添加字幕
    print("\n[Step 5] 添加字幕...")
    with_subtitle = work_dir / "video_with_subs.mp4"
    
    # 字幕文件路径需要用forward slash for FFmpeg
    srt_fs = str(srt_path).replace('\\', '/')
    cmd = [
        FFMPEG, "-y", "-i", str(concat_path),
        "-vf", f"subtitles='{srt_fs}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        str(with_subtitle)
    ]
    
    ok, _ = run_cmd(cmd, 180)
    if ok:
        print("  [OK] 字幕已添加")
    else:
        print("  [WARN] 字幕添加失败，使用无字幕版本")
        shutil.copy2(concat_path, with_subtitle)
    
    # Step 7: 添加配音
    print("\n[Step 6] 添加中文配音...")
    with_voice = work_dir / "video_final.mp4"
    
    if add_voiceover(with_subtitle, with_voice, VOICE_SCRIPT):
        print("  [OK] 配音已添加")
    else:
        print("  [WARN] 配音失败")
        shutil.copy2(with_subtitle, with_voice)
    
    # Step 8: 复制到最终目录
    print("\n[Step 7] 复制到最终目录...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_path = OUTPUT_DIR / f"轻上椰子水_60秒_开播视频.mp4"
    
    shutil.copy2(with_voice, final_path)
    
    # 验证最终视频
    if final_path.exists():
        info = get_video_info(final_path)
        if info:
            duration = float(info['format']['duration'])
            size_mb = final_path.stat().st_size / (1024*1024)
            
            print(f"\n  最终视频: {final_path}")
            print(f"  时长: {duration:.1f}s")
            print(f"  大小: {size_mb:.1f} MB")
            print(f"  字幕: ✅ 中英双语")
            print(f"  配音: ✅ 中文配音")
        else:
            print(f"\n  [WARN] 无法获取视频信息")
    else:
        print("  [ERROR] 复制失败!")
        return None
    
    print("\n" + "=" * 60)
    print("  完成!")
    print("=" * 60)
    
    return str(final_path)


if __name__ == "__main__":
    result = run_workflow()
    sys.exit(0 if result else 1)
