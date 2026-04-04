#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4.5 产品外观引导测试脚本
关键：在prompt中详细描述产品外观（因为图生视频CLI有bug）
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
import time

# UTF-8 support
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 路径配置
DREAMINA = r"C:\Users\Administrator\bin\dreamina.exe"
FFMPEG = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
FFPROBE = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffprobe.exe"

BASE = Path(r"C:\Users\Administrator\Desktop\qingShangVideos")
CLIPS_DIR = BASE / "generated_clips"
FINAL_DIR = BASE / "final_videos"

# ============================================================
# 核心：产品外观详细描述（用于替代图片参考）
# ============================================================
PRODUCT_APPEARANCE = "transparent cylindrical plastic bottle, showing clear colorless coconut water inside, white bottle body with green bamboo leaf label, white screw cap, the product is Qingshang Coconut Water 245mL"

# 统一人像描述
UNIFIED_CHARACTER = "young beautiful Chinese woman, 25 years old, long black hair, oval face, fair skin, natural makeup"

# ============================================================
# 11个片段配置
# 关键：每个prompt都包含产品外观描述，确保AI生成正确的产品
# ============================================================
SHOTS = [
    {"id": 1, "scene": "hot_office", "prompt": f"{UNIFIED_CHARACTER} sitting at modern office desk, visibly hot and thirsty, wiping sweat from forehead, frustrated expression, {PRODUCT_APPEARANCE} on desk, natural sunlight through window, professional attire, realistic lifestyle, 4K quality"},
    {"id": 2, "scene": "product_closeup", "prompt": f"close-up product photography, {PRODUCT_APPEARANCE} on wooden desk, transparent bottle clearly showing clear coconut water, white label with green bamboo branding, natural desk lamp lighting, clean minimalist background, premium beverage photography, 4K cinematic"},
    {"id": 3, "scene": "open_bottle", "prompt": f"{UNIFIED_CHARACTER} opening {PRODUCT_APPEARANCE} at desk, twist-off white cap being removed, her elegant hands with jade bracelet, natural indoor lighting, close-up on her action, professional beauty commercial style, 4K"},
    {"id": 4, "scene": "pour_water", "prompt": f"slow motion close-up, {PRODUCT_APPEARANCE} pouring into elegant glass, clear coconut water with tiny bubbles rising, condensation on glass surface, soft natural window lighting, ASMR style, professional food cinematography, 4K quality"},
    {"id": 5, "scene": "first_sip", "prompt": f"{UNIFIED_CHARACTER} taking first refreshing sip from glass of coconut water from {PRODUCT_APPEARANCE}, eyes closed with satisfaction, subtle smile, soft natural lighting, healthy glowing skin, shallow depth of field, intimate food commercial, 4K cinematic"},
    {"id": 6, "scene": "workout_after", "prompt": f"{UNIFIED_CHARACTER} finishing workout at modern gym, {PRODUCT_APPEARANCE} in her hand, wiping sweat with towel, breathing heavily but smiling, gym interior with large windows, golden hour sunlight, healthy lifestyle, fitness influencer style, 4K"},
    {"id": 7, "scene": "beach_refresh", "prompt": f"{UNIFIED_CHARACTER} standing on sandy beach holding {PRODUCT_APPEARANCE}, looking at camera and smiling, ocean waves behind, tropical vibe, bright sunny day, palm trees, fresh and healthy lifestyle, golden hour lighting, travel influencer aesthetic, 4K cinematic"},
    {"id": 8, "scene": "study_break", "prompt": f"{UNIFIED_CHARACTER} taking break from studying at wooden desk, {PRODUCT_APPEARANCE} beside laptop and books, afternoon sunlight through window, cozy home study environment, relaxed atmosphere, lifestyle vlog style, natural lighting, 4K quality"},
    {"id": 9, "scene": "friend_share", "prompt": f"{UNIFIED_CHARACTER} at trendy cafe with friends, {PRODUCT_APPEARANCE} on table, pouring coconut water into glasses for friends, laughing and chatting, modern minimalist interior with plants, warm ambient lighting, social lifestyle moment, cinematic documentary, 4K"},
    {"id": 10, "scene": "label_show", "prompt": f"product detail shot, {PRODUCT_APPEARANCE} rotating slowly on white marble surface, label clearly showing zero sugar zero fat claim and green bamboo branding, nutritional facts visible, e-commerce product photography style, soft studio lighting, 4K"},
    {"id": 11, "scene": "park_final", "prompt": f"{UNIFIED_CHARACTER} walking through sunny park path holding {PRODUCT_APPEARANCE}, looking at camera and smiling, light breeze moving her long black hair, lush green trees, fresh and healthy lifestyle feeling, warm golden hour lighting, inspiring finale, cinematic closing, 4K quality"}
]

# 53秒字幕
SUBTITLES = [
    (0.0, 4.0, "夏天太热了，渴得不行！", "Summer is so hot, I'm so thirsty!"),
    (4.0, 8.0, "白水解渴没味道，奶茶太甜太腻", "Plain water is boring, milk tea is too sweet..."),
    (8.0, 12.0, "快试试这个！轻上椰子水！", "Try this! Qingshang Coconut Water!"),
    (12.0, 16.0, "0糖0脂肪，清爽解渴超健康", "Zero sugar, zero fat, refreshing!"),
    (16.0, 20.0, "甄选东南亚优质椰子，纯天然无添加", "Selected coconuts, pure natural..."),
    (20.0, 25.0, "看这清澈透明的椰子水，太诱人了！", "Crystal clear coconut water!"),
    (25.0, 29.0, "运动完来一瓶，快速补水又解乏", "After workout, rapid hydration!"),
    (29.0, 33.0, "海边度假来一杯，清爽一整天", "Beach vacation, refreshing all day!"),
    (33.0, 37.0, "学习累了来一瓶，瞬间恢复活力", "Study break, instantly refreshed!"),
    (37.0, 41.0, "和朋友分享，清爽又健康！", "Share with friends!"),
    (41.0, 45.0, "0糖0脂低卡路里，喝了没负担！", "Zero sugar, zero fat, no guilt!"),
    (45.0, 49.0, "轻上大品牌，品质有保障！", "Qingshang brand, quality guaranteed!"),
    (49.0, 53.0, "点击购物车，夏日清爽即刻拥有！", "Add to cart now!")
]

VOICE_SCRIPT = """夏天太热了，渴得不行！白水解渴没味道，奶茶太甜太腻。快试试这个！轻上椰子水！0糖0脂肪，清爽解渴超健康。甄选东南亚优质椰子，纯天然无添加。看这清澈透明的椰子水，太诱人了！运动完来一瓶，快速补水又解乏。海边度假来一杯，清爽一整天，学习累了来一瓶，瞬间恢复活力。和朋友分享，清爽又健康！0糖0脂低卡路里，喝了没负担！轻上大品牌，品质有保障！点击购物车，夏日清爽即刻拥有！
"""


def run_cmd(cmd, timeout=60):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result
    except:
        return False, None


def generate_clip(prompt, duration=5):
    """使用text2video生成片段（prompt中包含产品外观）"""
    print(f"    提交...")
    
    cmd = [DREAMINA, "text2video", "--prompt", prompt, "--duration", str(duration), 
           "--ratio", "9:16", "--model_version", "seedance2.0fast", "--poll", "0"]
    
    ok, result = run_cmd(cmd, 30)
    
    if not ok:
        return None
    
    try:
        data = json.loads(result.stdout)
        submit_id = data.get("submit_id")
        print(f"    ID: {submit_id}")
        return submit_id
    except:
        return None


def poll_result(submit_id, max_wait=180):
    """轮询等待结果"""
    waited = 0
    while waited < max_wait:
        time.sleep(10)
        cmd = [DREAMINA, "query_result", "--submit_id", submit_id]
        ok, result = run_cmd(cmd, 30)
        
        if ok and result and "success" in result.stdout:
            try:
                data = json.loads(result.stdout)
                videos = data.get("result_json", {}).get("videos", [])
                if videos:
                    return videos[0].get("video_url")
            except:
                pass
        
        if result and "fail" in result.stdout:
            return None
        
        waited += 10
        print(f"    等待... ({waited}s)")
    
    return None


def download_video(url, output):
    cmd = [FFMPEG, "-y", "-i", url, "-c", "copy", str(output)]
    ok, _ = run_cmd(cmd, 60)
    return ok


def upscale_1080p(input_path, output_path):
    cmd = [FFMPEG, "-y", "-i", str(input_path),
           "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
           "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "copy",
           str(output_path)]
    ok, _ = run_cmd(cmd, 120)
    return ok


def concatenate_videos(clips, output):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        for c in clips:
            f.write(f"file '{c}'\n")
        tmp = f.name
    
    try:
        cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", tmp, "-c", "copy", str(output)]
        ok, _ = run_cmd(cmd, 300)
        return ok
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def add_voice(video_path, output_path, voice_script):
    print(f"    [TTS]...")
    SAG = r"C:\Users\Administrator\bin\sag.exe"
    if not os.path.exists(SAG):
        shutil.copy2(video_path, output_path)
        return False
    
    voice_file = Path(tempfile.gettempdir()) / "voice.wav"
    cmd = [SAG, "--text", voice_script, "--output", str(voice_file), "--voice", "zh-CN female"]
    ok, _ = run_cmd(cmd, 60)
    
    if not ok or not voice_file.exists():
        shutil.copy2(video_path, output_path)
        return False
    
    cmd = [FFMPEG, "-y", "-i", str(video_path), "-i", str(voice_file),
           "-c:v", "copy", "-c:a", "aac", "-shortest", str(output_path)]
    ok, _ = run_cmd(cmd, 120)
    
    if voice_file.exists():
        os.unlink(voice_file)
    
    return ok


def run_workflow():
    print("=" * 60)
    print("  v4.5 产品外观引导测试")
    print("  关键：每个prompt包含产品外观描述")
    print("=" * 60)
    print(f"\n  产品外观描述：{PRODUCT_APPEARANCE[:60]}...")
    print("=" * 60)
    
    date_str = datetime.now().strftime("%Y%m%d")
    output_dir = CLIPS_DIR / f"qingshang_coconut_water_v4.5_{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_clips = []
    
    print(f"\n[Step 1] 生成 {len(SHOTS)} 个片段...")
    
    for shot in SHOTS:
        print(f"\n  片段 {shot['id']}/{len(SHOTS)}: {shot['scene']}")
        
        submit_id = generate_clip(shot["prompt"])
        
        if not submit_id:
            print(f"    [FAIL] 提交失败")
            continue
        
        video_url = poll_result(submit_id)
        
        if not video_url:
            print(f"    [FAIL]")
            continue
        
        raw_path = output_dir / f"clip_{shot['id']:02d}_raw.mp4"
        if not download_video(video_url, raw_path):
            print(f"    [FAIL] 下载失败")
            continue
        
        clip_1080 = output_dir / f"clip_{shot['id']:02d}_1080p.mp4"
        if upscale_1080p(raw_path, clip_1080):
            generated_clips.append(clip_1080)
            print(f"    [OK]")
        else:
            generated_clips.append(raw_path)
            print(f"    [OK] (720p)")
    
    if not generated_clips:
        print("\n[ERROR] 没有片段!")
        return None
    
    print(f"\n  成功: {len(generated_clips)}/{len(SHOTS)}")
    
    print("\n[Step 2] 拼接...")
    concat_raw = output_dir / "concat_raw.mp4"
    concatenate_videos([str(c) for c in generated_clips], concat_raw)
    
    concat_1080 = output_dir / "video_1080p.mp4"
    upscale_1080p(concat_raw, concat_1080)
    
    print("\n[Step 3] 配音...")
    with_voice = output_dir / "video_with_voice.mp4"
    add_voice(concat_1080, with_voice, VOICE_SCRIPT)
    
    print("\n[Step 4] 复制到最终目录...")
    final_video = FINAL_DIR / f"qingshang_coconut_water_v4.5_final.mp4"
    shutil.copy2(with_voice, final_video)
    
    if final_video.exists():
        size = final_video.stat().st_size
        cmd = [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(final_video)]
        ok, result = run_cmd(cmd, 30)
        duration = result.stdout.strip() if ok else "?"
        
        print(f"\n  最终: {final_video}")
        print(f"  大小: {size / (1024*1024):.2f} MB")
        print(f"  时长: {duration} 秒")
    
    print("\n" + "=" * 60)
    print("  完成!")
    print("=" * 60)
    
    return str(final_video)


if __name__ == "__main__":
    result = run_workflow()
    sys.exit(0 if result else 1)
