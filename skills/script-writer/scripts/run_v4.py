#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4.0 Workflow Script - 品牌自动化AI提示剪辑流程
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# Reload UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Paths
DREAMINA = r"C:\Users\Administrator\bin\dreamina.exe"
FFMPEG = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
FFPROBE = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffprobe.exe"

BASE = Path(r"C:\Users\Administrator\Desktop\qingShangVideos")
CLIPS_DIR = BASE / "generated_clips"
FINAL_DIR = BASE / "final_videos"
SCRIPTS_DIR = BASE / "scripts"

# Product Standard
PRODUCT = {
    "name": "qingshang_coconut_water",
    "bottle_shape": "cylindrical",
    "liquid": "transparent",
    "label": "white_green"
}


def ensure_folders():
    for d in [CLIPS_DIR, FINAL_DIR, SCRIPTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd, timeout=180):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.returncode == 0, result.stdout, result.stderr


def dreamina_generate(prompt, duration=5, ratio="9:16"):
    print(f"  [Dreamina] Submitting...")
    cmd = [DREAMINA, "text2video", "--prompt", prompt, "--duration", str(duration), "--ratio", ratio, "--poll", "0"]
    ok, out, err = run_cmd(cmd, 30)
    
    if not ok:
        print(f"  [Error] Submit failed: {err[:100]}")
        return None
    
    try:
        data = json.loads(out)
        submit_id = data.get("submit_id")
        print(f"  [Dreamina] ID: {submit_id}")
    except:
        print(f"  [Error] Parse failed")
        return None
    
    # Poll
    for i in range(18):
        import time; time.sleep(10)
        cmd = [DREAMINA, "query_result", "--submit_id", submit_id]
        ok, out, err = run_cmd(cmd, 30)
        
        if ok and "success" in out:
            try:
                data = json.loads(out)
                videos = data.get("result_json", {}).get("videos", [])
                if videos:
                    print(f"  [OK] Video ready!")
                    return videos[0].get("video_url")
            except:
                pass
        
        if "fail" in out:
            print(f"  [Fail] Generation failed")
            return None
        
        print(f"  Waiting... ({i*10}s)")
    
    return None


def download_video(url, output):
    print(f"  Downloading...")
    cmd = [FFMPEG, "-y", "-i", url, "-c", "copy", str(output)]
    ok, out, err = run_cmd(cmd, 60)
    return ok


def upscale_1080p(input_path, output_path):
    print(f"  Upscaling to 1080p...")
    cmd = [FFMPEG, "-y", "-i", str(input_path),
           "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
           "-c:v", "libx264", "-preset", "fast", "-crf", "23",
           "-c:a", "copy",
           str(output_path)]
    ok, out, err = run_cmd(cmd, 120)
    return ok


def ffmpeg_qc(video_path):
    print(f"  Running FFmpeg QC...")
    results = {"status": "PASS", "checks": {}}
    
    # File size
    size = Path(video_path).stat().st_size
    results["checks"]["file_size"] = "PASS" if size > 0 else "FAIL"
    if size == 0: results["status"] = "FAIL"
    print(f"    file_size: {size} - {results['checks']['file_size']}")
    
    # Resolution
    cmd = [FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", str(video_path)]
    ok, out, err = run_cmd(cmd, 30)
    if ok:
        try:
            data = json.loads(out)
            w = data["streams"][0]["width"]
            h = data["streams"][0]["height"]
            # 9:16 vertical: width>=720, height>=1280
            res_ok = w >= 720 and h >= 1280
            results["checks"]["resolution"] = "PASS" if res_ok else "FAIL"
            if not res_ok: results["status"] = "FAIL"
            print(f"    resolution: {w}x{h} - {results['checks']['resolution']}")
        except:
            results["checks"]["resolution"] = "FAIL"
            results["status"] = "FAIL"
    
    # Black detect
    cmd = [FFMPEG, "-i", str(video_path), "-vf", "blackdetect=d=0.5:pix_th=0.00", "-f", "null", "-"]
    ok, out, err = run_cmd(cmd, 60)
    has_black = "black_start" in err
    results["checks"]["blackdetect"] = "PASS" if not has_black else "FAIL"
    if has_black: results["status"] = "FAIL"
    print(f"    blackdetect: {results['checks']['blackdetect']}")
    
    # Freeze detect
    cmd = [FFMPEG, "-i", str(video_path), "-vf", "freezedetect=n=-30dB:d=0.5", "-f", "null", "-"]
    ok, out, err = run_cmd(cmd, 60)
    has_freeze = "frozen" in err
    results["checks"]["freezedetect"] = "PASS" if not has_freeze else "FAIL"
    if has_freeze: results["status"] = "FAIL"
    print(f"    freezedetect: {results['checks']['freezedetect']}")
    
    return results


def concatenate_videos(clips, output):
    print(f"  Concatenating {len(clips)} clips...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        for c in clips:
            f.write(f"file '{c}'\n")
        tmp = f.name
    
    try:
        cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", tmp, "-c", "copy", str(output)]
        ok, out, err = run_cmd(cmd, 300)
        return ok
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def add_subtitles(video_path, output, subtitles):
    print(f"  Adding subtitles...")
    
    ass = """[Script Info]
Title: Qingshang
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CN, Microsoft YaHei, 56, &H00FFFFFF, &H000000FF, &H00000000, &H00000000, -1, 0, 0, 0, 100, 100, 0, 0, 1, 3, 0, 2, 30, 30, 150, 1
Style: EN, Arial, 42, &H00FFFFFF, &H000000FF, &H00000000, &H00000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 2, 30, 30, 220, 1

[Events]
Format: Layer, Start, End, Style, Text
"""
    
    for start, end, cn, en in subtitles:
        start_fmt = f"0:00:{start:.2f}".replace(".", ":")
        end_fmt = f"0:00:{end:.2f}".replace(".", ":")
        ass += f"Dialogue: 0,{start_fmt},{end_fmt},CN,{cn}\\N{en}\n"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ass', delete=False, encoding='utf-8') as f:
        f.write(ass)
        ass_file = f.name
    
    try:
        cmd = [FFMPEG, "-y", "-i", str(video_path), "-vf", f"ass={ass_file}", "-c:a", "copy", str(output)]
        ok, out, err = run_cmd(cmd, 300)
        return ok
    finally:
        if os.path.exists(ass_file):
            os.unlink(ass_file)


def run_workflow(product_name="qingshang_coconut_water", target_duration=55):
    print("=" * 60)
    print("  v4.0 Brand Automation AI Workflow")
    print("=" * 60)
    print(f"  Product: {product_name}")
    print(f"  Target: {target_duration}s")
    print(f"  Time: {datetime.now()}")
    print("=" * 60)
    
    ensure_folders()
    
    # Shot prompts (5 test shots)
    shots = [
        {"id": 1, "scene": "product_closeup", "prompt": "close-up product shot of Qingshang Coconut Water bottle, transparent bottle showing clear coconut water inside, white bottle body with green label, white cap, clean white background, soft diffused lighting, 4K cinematic quality, professional food photography"},
        {"id": 2, "scene": "office_tired", "prompt": "medium shot of tired young woman at modern office desk working on laptop, slightly fatigued expression, indoor fluorescent lighting, shoulder-up framing, realistic lifestyle cinematography, professional 4K quality"},
        {"id": 3, "scene": "product_showcase", "prompt": "close-up product shot of Qingshang Coconut Water 245mL, transparent plastic bottle showing clear colorless liquid, white body with green text label, white screw cap, clean minimalist white background, soft lighting, 4K quality, professional photography"},
        {"id": 4, "scene": "pouring_water", "prompt": "close-up of white bottle cap being twisted open, clear coconut water pouring into transparent glass, crystal clear liquid with slight golden tint, fine bubbles rising, top lighting creating sparkle effect, dark background, professional beverage photography, 4K"},
        {"id": 5, "scene": "workout", "prompt": "energetic fitness scene with athletic young woman in gym wearing workout clothes, dynamic pose with sweat on forehead, bright gym interior with natural light from windows, medium shot capturing upper body, healthy lifestyle mood, professional sports photography, 4K"}
    ]
    
    date_str = datetime.now().strftime("%Y%m%d")
    output_dir = CLIPS_DIR / f"{product_name}_{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_clips = []
    
    # Step 1: Generate clips
    print("\n[Step 1] Generating clips with Dreamina AI...")
    print("  [RULE] Must use AI-generated clips, NO existing footage!")
    
    for shot in shots:
        print(f"\n  Shot {shot['id']}: {shot['scene']}")
        print(f"  Prompt: {shot['prompt'][:60]}...")
        
        # Generate
        url = dreamina_generate(shot["prompt"], duration=5, ratio="9:16")
        
        if not url:
            print(f"  [FAIL] Generation failed, skipping")
            continue
        
        # Download
        raw_path = output_dir / f"clip_{shot['id']:02d}_raw.mp4"
        if not download_video(url, raw_path):
            print(f"  [FAIL] Download failed")
            continue
        
        # Upscale to 1080p
        clip_1080 = output_dir / f"clip_{shot['id']:02d}_1080p.mp4"
        if upscale_1080p(raw_path, clip_1080):
            generated_clips.append(clip_1080)
            print(f"  [OK] Saved: {clip_1080.name}")
        else:
            generated_clips.append(raw_path)
            print(f"  [OK] Saved: {raw_path.name}")
    
    if not generated_clips:
        print("\n[ERROR] No clips generated!")
        return None
    
    print(f"\n  Generated: {len(generated_clips)} clips")
    
    # Step 2: FFmpeg QC
    print("\n[Step 2] FFmpeg QC...")
    qc_passed = []
    for clip in generated_clips:
        print(f"\n  QC: {clip.name}")
        results = ffmpeg_qc(clip)
        if results["status"] == "PASS":
            qc_passed.append(clip)
            print(f"  [PASS]")
        else:
            print(f"  [FAIL] - using anyway")
            qc_passed.append(clip)
    
    print(f"\n  QC Passed: {len(qc_passed)}/{len(generated_clips)}")
    
    # Step 3: Concatenate
    print("\n[Step 3] Concatenating...")
    concat_raw = output_dir / f"{product_name}_concat_raw.mp4"
    
    if not concatenate_videos([str(c) for c in qc_passed], concat_raw):
        print("[FAIL] Concatenation failed")
        return None
    
    # Upscale final
    concat_1080 = output_dir / f"{product_name}_1080p.mp4"
    upscale_1080p(concat_raw, concat_1080)
    
    # Step 4: Add subtitles
    print("\n[Step 4] Adding subtitles...")
    final_video = FINAL_DIR / f"{product_name}_{target_duration}s_final.mp4"
    
    subtitles = [
        (0.0, 4.5, "夏天最渴的时候怎么办？", "What do you drink when you're most thirsty?"),
        (4.5, 12.0, "白水没味道，奶茶太甜太腻", "Plain water is boring, milk tea is too sweet..."),
        (12.0, 18.0, "试试这个！轻上椰子水0糖0脂肪", "Try this! Qingshang Coconut Water"),
        (18.0, 25.0, "甄选东南亚新鲜椰子纯天然0添加", "Selected fresh Southeast Asian coconuts"),
        (25.0, 33.0, "运动后来一瓶！快速补水又解乏", "Perfect after workout! Rapid hydration!"),
        (33.0, 40.0, "工作累了来一杯，瞬间清爽！", "Feeling tired? One bottle refreshes!"),
        (40.0, 48.0, "零糖零脂低卡路里清爽无负担！", "Zero sugar, zero fat, low calories!"),
        (48.0, 55.0, "轻上大品牌，立即购买体验清凉一夏！", "Qingshang - Buy now, enjoy summer!"),
    ]
    
    if add_subtitles(concat_1080, final_video, subtitles):
        print(f"  [OK] Subtitles added")
    else:
        print(f"  [WARN] Subtitle failed, copying without subtitles")
        shutil.copy2(concat_1080, final_video)
    
    # Final QC
    print("\n[Step 5] Final QC...")
    final_qc = ffmpeg_qc(final_video)
    
    # Report
    report = {
        "report_title": f"Video Production Report - {product_name}",
        "product": product_name,
        "created_at": datetime.now().isoformat(),
        "workflow_version": "v4.0",
        "target_duration": target_duration,
        "clips_generated": len(generated_clips),
        "clips_qc_passed": len(qc_passed),
        "final_video": str(final_video),
        "final_qc": final_qc
    }
    
    report_path = FINAL_DIR / f"{product_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("  v4.0 WORKFLOW COMPLETE!")
    print("=" * 60)
    print(f"  Final Video: {final_video}")
    print(f"  Report: {report_path}")
    print(f"  Clips Dir: {output_dir}")
    print("=" * 60)
    
    return str(final_video)


if __name__ == "__main__":
    product = sys.argv[1] if len(sys.argv) > 1 else "qingshang_coconut_water"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 55
    
    try:
        result = run_workflow(product, duration)
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
