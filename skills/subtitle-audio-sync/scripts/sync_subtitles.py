#!/usr/bin/env python3
"""
subtitle-audio-sync 核心脚本
精准同步字幕与配音：使用Whisper获取精确时间戳，烧录硬字幕
"""

import os
import sys
import json
import time
import subprocess
import tempfile
from pathlib import Path
from datetime import timedelta

# ============== 配置 ==============
PROJECT_ROOT = Path(__file__).parent.parent.parent
FFMPEG_BIN = Path(os.environ.get(
    "FFMPEG_PATH",
    r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
))

# ============== 依赖检查 ==============
def check_dependencies():
    """检查必要依赖"""
    missing = []

    # 检查 FFmpeg
    if not FFMPEG_BIN.exists():
        missing.append(f"FFmpeg not found at: {FFMPEG_BIN}")

    # 检查 Whisper
    try:
        import whisper
    except ImportError:
        try:
            import faster_whisper
        except ImportError:
            missing.append("whisper or faster-whisper not installed")

    # 检查 MoviePy
    try:
        from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
    except ImportError:
        missing.append("moviepy not installed")

    if missing:
        print("⚠️  缺少依赖:")
        for m in missing:
            print(f"  - {m}")
        print("\n安装命令:")
        print("  pip install faster-whisper moviepy")
        return False
    return True


def transcribe_with_word_timestamps(audio_path: str, model_name: str = "base") -> dict:
    """使用Whisper转写音频，获取精确时间戳"""
    try:
        import whisper
    except ImportError:
        import faster_whisper

        # 使用 faster-whisper (更快)
        model = faster_whisper.CtmModel(model_name.replace("-", "_"))
        segments, info = model.transcribe(
            audio_path,
            word_timestamps=True,
            language="zh"
        )

        result = {"segments": [], "language": info.language}
        for seg in segments:
            words = []
            if seg.words:
                for w in seg.words:
                    words.append({
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "probability": getattr(w, "probability", 1.0)
                    })
            result["segments"].append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "words": words
            })
        return result

    # 使用 openai-whisper
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, word_timestamps=True)

    return result


def generate_srt(subtitle_data: dict, output_path: str = None) -> str:
    """生成SRT字幕文件（精确到毫秒）"""
    segments = subtitle_data.get("segments", [])

    if not segments:
        print("⚠️  没有检测到字幕段")
        return None

    srt_lines = []
    for i, seg in enumerate(segments, 1):
        start = seg["start"]
        end = seg["end"]
        text = seg["text"].strip()

        # 转换为 SRT 时间格式: HH:MM:SS,mmm
        def fmt_time(t):
            td = timedelta(seconds=t)
            hours = td.seconds // 3600
            minutes = (td.seconds % 3600) // 60
            seconds = td.seconds % 60
            millis = td.microseconds // 1000
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

        srt_lines.append(f"{i}")
        srt_lines.append(f"{fmt_time(start)} --> {fmt_time(end)}")
        srt_lines.append(text)
        srt_lines.append("")

    srt_content = "\n".join(srt_lines)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"✅ SRT字幕已生成: {output_path}")

    return srt_content


def burn_subtitles_with_ffmpeg(video_path: str, srt_path: str, output_path: str = None) -> str:
    """使用FFmpeg烧录硬字幕（ASS格式效果更好）"""
    if not output_path:
        output_path = str(Path(video_path).with_name(
            Path(video_path).stem + "_subtitled.mp4"
        ))

    # FFmpeg 烧录字幕
    # 使用 copy 编解码器避免重编码（但硬字幕需要重新编码）
    cmd = [
        str(FFMPEG_BIN),
        "-y",
        "-i", video_path,
        "-vf", f"subtitles='{srt_path}'",
        "-c:a", "copy",
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd)
        print(f"✅ 硬字幕视频已生成: {output_path}")
        return output_path
    except subprocess.TimeoutExpired:
        print("⚠️ FFmpeg 超时，尝试替代方案...")
        return None


def burn_subtitles_with_moviepy(video_path: str, subtitle_data: dict, output_path: str = None) -> str:
    """使用MoviePy烧录字幕（备用方案）"""
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

    if not output_path:
        output_path = str(Path(video_path).with_name(
            Path(video_path).stem + "_subtitled.mp4"
        ))

    try:
        video = VideoFileClip(video_path)
        txt_clips = []

        for seg in subtitle_data["segments"]:
            start = seg["start"]
            end = seg["end"]
            text = seg["text"].strip()

            if not text:
                continue

            txt_clip = TextClip(
                text,
                font="C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                font_size=video.h // 16,  # 根据视频高度自适应
                color="white",
                stroke_color="black",
                stroke_width=2,
                method="center",
                align="center",
                duration=end - start
            ).set_start(start).set_position(("center", "bottom"))

            txt_clips.append(txt_clip)

        final = CompositeVideoClip([video] + txt_clips)
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=tempfile.mktemp(suffix=".m4a"),
            remove_temp=True,
            threads=4,
            fps=30
        )
        print(f"✅ MoviePy字幕视频已生成: {output_path}")
        return output_path

    except Exception as e:
        print(f"⚠️ MoviePy方案失败: {e}")
        return None


def sync_subtitles(video_path: str, audio_path: str = None, model: str = "base",
                   subtitle_path: str = None, output_path: str = None) -> dict:
    """
    主流程：精准同步字幕与配音

    Args:
        video_path: 视频文件路径
        audio_path: 配音文件路径（如果为None，从视频提取）
        model: Whisper模型（tiny/base/small/medium/large）
        subtitle_path: 外部字幕文件（可选，用于验证）
        output_path: 输出视频路径

    Returns:
        包含各文件路径和同步精度的字典
    """
    print(f"🎬 开始字幕同步: {video_path}")
    start_time = time.time()

    # Step 1: 提取音频（如果只提供视频）
    if audio_path is None:
        print("📢 从视频提取音频...")
        temp_audio = tempfile.mktemp(suffix=".wav")
        cmd = [
            str(FFMPEG_BIN),
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            temp_audio
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        audio_path = temp_audio

    # Step 2: Whisper转写（获取精确时间戳）
    print(f"🎙️ 正在转写音频（模型: {model}）...")
    subtitle_data = transcribe_with_word_timestamps(audio_path, model)
    print(f"📝 检测到 {len(subtitle_data['segments'])} 个字幕段")

    # Step 3: 生成SRT字幕文件
    srt_path = subtitle_path or str(Path(video_path).with_suffix(".srt"))
    generate_srt(subtitle_data, srt_path)

    # Step 4: 烧录硬字幕到视频
    print("🎞️ 正在烧录字幕...")

    # 优先使用 FFmpeg（更快）
    final_video = burn_subtitles_with_ffmpeg(video_path, srt_path, output_path)

    # 备用 MoviePy 方案
    if not final_video:
        final_video = burn_subtitles_with_moviepy(video_path, subtitle_data, output_path)

    elapsed = time.time() - start_time
    print(f"\n✅ 字幕同步完成！耗时: {elapsed:.1f}秒")

    return {
        "original_video": video_path,
        "final_video": final_video,
        "srt_path": srt_path,
        "subtitle_data": subtitle_data,
        "elapsed_seconds": elapsed,
        "segments_count": len(subtitle_data["segments"])
    }


def main():
    """命令行入口"""
    if not check_dependencies():
        sys.exit(1)

    if len(sys.argv) < 2:
        print("""用法:
  python sync_subtitles.py <视频路径> [配音路径] [输出路径]

示例:
  python sync_subtitles.py final_video.mp4 voiceover.wav output_subtitled.mp4
  python sync_subtitles.py final_video.mp4  # 自动从视频提取音频
""")
        sys.exit(1)

    video_path = sys.argv[1]
    audio_path = sys.argv[2] if len(sys.argv) > 2 else None
    output_path = sys.argv[3] if len(sys.argv) > 3 else None

    result = sync_subtitles(video_path, audio_path, output_path=output_path)
    print(f"\n输出视频: {result['final_video']}")
    print(f"SRT字幕: {result['srt_path']}")


if __name__ == "__main__":
    main()
