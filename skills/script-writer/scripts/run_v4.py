#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4.1 Master Workflow Script - 完整视频生产流程

整合了:
- product-scanner: 启动时检查产品清单
- generate_clip: 重试逻辑 + 缓存
- clip_cache: 片段缓存复用
- cost_tracker: 成本跟踪
- multi_ratio: 多比例输出
- evaluate_final: 质量评估 + UUID记录
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

# Paths
DREAMINA = r"C:\Users\Administrator\bin\dreamina.exe"
FFMPEG = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
FFPROBE = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffprobe.exe"

BASE = Path(r"C:\Users\Administrator\Desktop\qingShangVideos")
CLIPS_DIR = BASE / "generated_clips"
FINAL_DIR = BASE / "final_videos"
LOGS_DIR = BASE / "logs"
MANIFEST = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\knowledge_base\products_manifest.json")
SCAN_SCRIPT = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\skills\product-scanner\scripts\scan_products.py")
CACHE_SCRIPT = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\skills\clip-generator\scripts\clip_cache.py")
GENERATE_SCRIPT = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\skills\clip-generator\scripts\generate_clip.py")
COST_SCRIPT = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\skills\cost_manager\scripts\cost_tracker.py")
MULTI_RATIO_SCRIPT = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\skills\video-editor\scripts\multi_ratio.py")
EVALUATE_SCRIPT = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\skills\final-qc\scripts\evaluate_final.py")
QUERY_SCRIPT = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\skills\final-qc\scripts\query_videos.py")

sys.path.insert(0, str(GENERATE_SCRIPT.parent))
sys.path.insert(0, str(COST_SCRIPT.parent))
sys.path.insert(0, str(CACHE_SCRIPT.parent))

# Import modules
from generate_clip import generate_clip, download_clip
from cost_tracker import CostTracker, check_quota, record_clip_cost, print_cost_report
from clip_cache import check_cache, add_to_cache

def ensure_folders():
    for d in [CLIPS_DIR, FINAL_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def check_product_manifest(product_id):
    """检查产品清单，必要时扫描"""
    if not MANIFEST.exists():
        print(f"\n[Product-Scanner] 产品清单不存在，开始扫描...")
        return scan_products()
    
    with open(MANIFEST, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    # 检查当前产品是否在清单中
    found = any(p.get('product_id') == product_id for p in manifest.get('products', []))
    
    if not found:
        print(f"\n[Product-Scanner] 产品 {product_id} 不在清单中，开始扫描...")
        return scan_products()
    
    return True

def scan_products():
    """运行产品扫描"""
    print(f"\n[Product-Scanner] 运行扫描脚本...")
    result = subprocess.run([sys.executable, str(SCAN_SCRIPT)], 
                          capture_output=True, text=True)
    print(result.stdout)
    return result.returncode == 0

def run_workflow(product_id, target_duration=55, hot_topic="", concurrency=1):
    """运行单个任务"""
    print("=" * 60)
    print(f"  v4.1 Workflow: {product_id}")
    print(f"  目标时长: {target_duration}s")
    print(f"  时间: {datetime.now()}")
    print("=" * 60)
    
    # Step 0: 检查产品清单
    print("\n[Step 0] 检查产品清单...")
    check_product_manifest(product_id)
    
    # Step 0.5: 检查配额
    print("\n[Step 0.5] 检查成本配额...")
    if not check_quota():
        print("[WARN] 超出配额，继续执行...")
    
    # 初始化成本跟踪器
    cost_tracker = CostTracker()
    
    # Step 1: 生成片段
    print("\n[Step 1] 生成片段...")
    date_str = datetime.now().strftime("%Y%m%d")
    output_dir = CLIPS_DIR / f"{product_id}_{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 片段配置
    shots = [
        {"id": 1, "scene": "product_closeup", "prompt": "close-up product shot of Qingshang Coconut Water bottle, transparent bottle showing clear coconut water inside, white bottle body with green label, white cap, clean white background, soft diffused lighting, 4K cinematic quality"},
        {"id": 2, "scene": "office_tired", "prompt": "medium shot of tired young woman at office desk working, slightly fatigued expression, indoor fluorescent lighting, shoulder-up framing, realistic lifestyle cinematography, professional 4K quality"},
        {"id": 3, "scene": "product_showcase", "prompt": "close-up product shot of Qingshang Coconut Water 245mL, transparent plastic bottle showing clear colorless liquid, white body with green text label, white screw cap, clean minimalist white background, soft lighting, 4K quality"},
        {"id": 4, "scene": "pouring_water", "prompt": "close-up of white bottle cap being twisted open, clear coconut water pouring into transparent glass, crystal clear liquid with slight golden tint, bubbles rising, top lighting, dark background, professional beverage photography, 4K"},
        {"id": 5, "scene": "workout", "prompt": "energetic fitness scene with athletic young woman in gym, dynamic pose with sweat on forehead, bright gym interior with natural light, medium shot capturing upper body, healthy lifestyle mood, professional sports photography, 4K"}
    ]
    
    generated_clips = []
    skipped_clips = []
    failed_count = 0
    
    for shot in shots:
        print(f"\n  处理镜头 {shot['id']}/{len(shots)}...")
        
        # 检查缓存
        cache_result = check_cache(product_id, shot["scene"])
        if cache_result.get("hit"):
            cached_file = cache_result.get("cached_file")
            print(f"    [CACHE HIT] 复用: {cached_file}")
            clip_path = output_dir / f"clip_{shot['id']:02d}_cached.mp4"
            shutil.copy2(cached_file, clip_path)
            generated_clips.append(clip_path)
            continue
        
        # 生成新片段（带重试）
        result = generate_clip(shot["id"], shot["scene"], shot["prompt"], duration=5, ratio="9:16")
        
        if result.get("status") == "success":
            # 下载
            video_url = result.get("video_url")
            clip_path = output_dir / f"clip_{shot['id']:02d}_raw.mp4"
            clip_1080 = output_dir / f"clip_{shot['id']:02d}_1080p.mp4"
            
            if download_clip(video_url, clip_path):
                # 升频
                if upscale_1080p(clip_path, clip_1080):
                    generated_clips.append(clip_1080)
                    # 添加到缓存
                    add_to_cache(product_id, shot["scene"], str(clip_1080), 75)
                    # 记录成本
                    cost_tracker.record(product_id, 5, 120)
                else:
                    generated_clips.append(clip_path)
            print(f"    [OK] clip_{shot['id']}")
        else:
            skipped_clips.append({
                "shot_id": shot["id"],
                "scene": shot["scene"],
                "reason": result.get("reason", "unknown")
            })
            failed_count += 1
            print(f"    [SKIP] 跳过: {result.get('reason')}")
    
    print(f"\n  生成结果: {len(generated_clips)} 成功, {len(skipped_clips)} 跳过")
    
    if not generated_clips:
        print("[ERROR] 没有成功生成的片段!")
        return None
    
    # Step 2: 拼接
    print("\n[Step 2] 拼接片段...")
    concat_raw = output_dir / f"{product_id}_concat_raw.mp4"
    if concatenate_videos([str(c) for c in generated_clips], concat_raw):
        print(f"    [OK] 拼接成功")
    else:
        print("[ERROR] 拼接失败")
        return None
    
    # 升频
    concat_1080 = output_dir / f"{product_id}_1080p.mp4"
    upscale_1080p(concat_raw, concat_1080)
    
    # Step 3: 多比例输出
    print("\n[Step 3] 多比例输出...")
    multi_results = generate_multi_ratio(concat_1080, output_dir, product_id)
    
    # Step 4: 评估
    print("\n[Step 4] 质量评估...")
    primary_video = multi_results.get("9x16") or str(concat_1080)
    
    eval_result = evaluate_video(primary_video, product_id, hot_topic)
    
    # Step 5: 复制到最终目录
    print("\n[Step 5] 保存到最终目录...")
    final_video = FINAL_DIR / f"{product_id}_{target_duration}s_final.mp4"
    shutil.copy2(primary_video, final_video)
    
    # 成本报告
    print("\n[Step 6] 成本统计...")
    cost_tracker.print_session_report()
    print_cost_report()
    
    # 生成报告
    report = {
        "product_id": product_id,
        "created_at": datetime.now().isoformat(),
        "workflow_version": "v4.1",
        "target_duration": target_duration,
        "clips_generated": len(generated_clips),
        "clips_skipped": len(skipped_clips),
        "final_video": str(final_video),
        "multi_ratio": multi_results,
        "evaluation": eval_result,
        "skipped_clips": skipped_clips
    }
    
    report_path = FINAL_DIR / f"{product_id}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("  v4.1 流程完成!")
    print("=" * 60)
    print(f"  成功片段: {len(generated_clips)}")
    print(f"  跳过片段: {len(skipped_clips)}")
    print(f"  最终视频: {final_video}")
    print("=" * 60)
    
    return str(final_video)

def upscale_1080p(input_path, output_path):
    """升频到1080p"""
    cmd = [FFMPEG, "-y", "-i", str(input_path),
           "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
           "-c:v", "libx264", "-preset", "fast", "-crf", "23",
           "-c:a", "copy",
           str(output_path)]
    ok, out, err = run_subprocess(cmd, 120)
    return ok

def concatenate_videos(clips, output):
    """拼接视频"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        for c in clips:
            f.write(f"file '{c}'\n")
        tmp = f.name
    
    try:
        cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", tmp, "-c", "copy", str(output)]
        ok, out, err = run_subprocess(cmd, 300)
        return ok
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def generate_multi_ratio(input_path, output_dir, base_name):
    """多比例输出"""
    result = subprocess.run(
        [sys.executable, str(MULTI_RATIO_SCRIPT), str(input_path), str(output_dir), base_name],
        capture_output=True, text=True
    )
    # 返回结果
    return {
        "9x16": str(output_dir / f"{base_name}_9x16.mp4"),
        "1x1": str(output_dir / f"{base_name}_1x1.mp4"),
        "16x9": str(output_dir / f"{base_name}_16x9.mp4")
    }

def evaluate_video(video_path, product_id, hot_topic):
    """评估视频"""
    result = subprocess.run(
        [sys.executable, str(EVALUATE_SCRIPT), str(video_path), product_id, hot_topic],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except:
        return {"status": "unknown"}

def run_subprocess(cmd, timeout=60):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stderr
    except:
        return False, ""

def run_task_file(task_file):
    """运行任务文件"""
    print("=" * 60)
    print(f"  v4.1 批量任务模式")
    print(f"  任务文件: {task_file}")
    print("=" * 60)
    
    with open(task_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    print(f"\n共 {len(tasks)} 个任务\n")
    
    results = []
    for i, task in enumerate(tasks):
        print(f"\n{'='*60}")
        print(f"  任务 {i+1}/{len(tasks)}")
        print(f"{'='*60}")
        
        product_id = task.get("product_id", "unknown")
        duration = task.get("duration", 55)
        topic = task.get("topic", "")
        
        try:
            result = run_workflow(product_id, duration, topic)
            results.append({
                "task": task,
                "status": "success" if result else "failed"
            })
        except Exception as e:
            print(f"[ERROR] 任务失败: {e}")
            results.append({
                "task": task,
                "status": "failed",
                "error": str(e)
            })
    
    # 汇总报告
    print("\n" + "=" * 60)
    print("  批量任务完成报告")
    print("=" * 60)
    success = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - success
    print(f"  成功: {success}")
    print(f"  失败: {failed}")
    print("=" * 60)
    
    return results

def main():
    """命令行入口"""
    # 解析参数
    task_file = None
    product_id = "qingshang_coconut_water"
    duration = 55
    concurrency = 1
    
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            if arg.startswith("--task_file="):
                task_file = arg.split("=", 1)[1]
            elif arg.startswith("--product="):
                product_id = arg.split("=", 1)[1]
            elif arg.startswith("--duration="):
                duration = int(arg.split("=", 1)[1])
            elif arg.startswith("--concurrency="):
                concurrency = int(arg.split("=", 1)[1])
    
    ensure_folders()
    
    if task_file:
        return run_task_file(task_file)
    else:
        result = run_workflow(product_id, duration, concurrency=concurrency)
        return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())
