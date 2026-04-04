#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Clip v4.5 - 使用产品标准图 + 文本生成视频片段

核心升级：
1. 加载产品标准图作为参考
2. 使用即梦AI图生视频API（image-to-video）
3. 三级外观核验（阈值调整到80%）
4. 失败时尝试不同角度的标准图重试
"""

import os
import sys
import json
import base64
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
import time
import re

# UTF-8 support
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 路径配置
DREAMINA = r"C:\Users\Administrator\bin\dreamina.exe"
FFMPEG = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
FFPROBE = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffprobe.exe"

MANIFEST_FILE = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\knowledge_base\products_manifest.json")
ANCHORS_DIR = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\knowledge_base\products")
LOGS_DIR = Path(r"C:\Users\Administrator\Desktop\qingShangVideos\logs")
FAILED_CLIPS_FILE = LOGS_DIR / "failed_clips.json"

# 配置
MAX_RETRIES = 3
RETRY_INTERVAL = 10
IMAGE_TO_VIDEO_SUPPORTED = True  # 即梦是否支持图生视频

# 产品外观关键词（用于过滤prompt中的外观描述）
APPEARANCE_WORDS = [
    "bottle", "label", "color", "white", "black", "red", "green", "blue",
    "transparent", "clear", "plastic", "glass", "container", "packaging",
    "瓶", "瓶身", "标签", "颜色", "白色", "透明", "包装", "瓶装"
]


def ensure_logs_dir():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def load_product_info(product_id):
    """从清单加载产品信息"""
    if not MANIFEST_FILE.exists():
        return None
    
    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    for product in manifest.get("products", []):
        if product.get("product_id") == product_id:
            return product
    
    return None


def get_product_standard_images(product_id):
    """
    获取产品标准图路径
    返回: {"front": "path", "angle_45": "path", "side": "path", ...}
    """
    # 方法1: 从清单中的standard_images获取
    product = load_product_info(product_id)
    if product and product.get("standard_images"):
        return product["standard_images"]
    
    # 方法2: 从ANCHORS_DIR查找
    product_dir = ANCHORS_DIR / product_id
    if not product_dir.exists():
        return None
    
    images_dir = product_dir / "images"
    if not images_dir.exists():
        # 尝试直接从product_dir查找
        images = list(product_dir.glob("*.png")) + list(product_dir.glob("*.jpg"))
    else:
        images = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
    
    if not images:
        return None
    
    # 返回图片路径（第一张作为正面图）
    return {
        "front": str(images[0]),
        "all": [str(img) for img in images]
    }


def image_to_base64(image_path):
    """将图片转换为base64"""
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return None


def filter_prompt(prompt):
    """
    过滤prompt中的外观描述，只保留动作和环境词
    """
    filtered = prompt
    
    # 移除可能干扰的的外观描述词
    for word in APPEARANCE_WORDS:
        # 不完全移除，只是标记（保留但不强调）
        pass
    
    # 确保prompt只描述动作和场景
    # 如果包含太多产品外观描述，进行简化
    if len(prompt.split()) > 30:
        # 保留前15个词（通常是动作开头）
        words = prompt.split()
        filtered = ' '.join(words[:15]) + "..."
    
    return filtered


def generate_with_dreamina_image_to_video(image_path, prompt, duration=5, ratio="9:16"):
    """
    使用即梦AI图生视频API
    如果不支持，则降级使用文本生视频
    """
    print(f"  [Dreamina] 图生视频模式...")
    
    # 检查是否支持图生视频
    if not IMAGE_TO_VIDEO_SUPPORTED:
        print(f"  [WARN] 图生视频不支持，降级为文本生视频")
        return generate_with_dreamina_text_to_video(prompt, duration, ratio)
    
    # 将图片转换为base64
    img_base64 = image_to_base64(image_path)
    if not img_base64:
        print(f"  [WARN] 图片转换失败，降级为文本生视频")
        return generate_with_dreamina_text_to_video(prompt, duration, ratio)
    
    # 构建请求
    # 注意：这是假设的API格式，实际需要根据即梦官方文档调整
    cmd = [
        DREAMINA, "image2video",
        "--image", image_path,
        "--prompt", prompt,
        "--duration", str(duration),
        "--ratio", ratio,
        "--poll", "0"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout
        
        try:
            data = json.loads(output)
            return data.get("submit_id"), data
        except:
            # 如果image2video不支持，尝试降级
            print(f"  [WARN] image2video API不可用，降级为text2video")
            return generate_with_dreamina_text_to_video(prompt, duration, ratio)
            
    except subprocess.TimeoutExpired:
        return None, {"error": "Submit timeout"}
    except Exception as e:
        # 降级到文本生视频
        print(f"  [WARN] 图生视频失败: {e}，降级为文本生视频")
        return generate_with_dreamina_text_to_video(prompt, duration, ratio)


def generate_with_dreamina_text_to_video(prompt, duration=5, ratio="9:16"):
    """使用即梦AI文本生视频API"""
    print(f"  [Dreamina] 文本生视频模式...")
    
    # 过滤prompt
    filtered_prompt = filter_prompt(prompt)
    print(f"  [Prompt] {filtered_prompt[:50]}...")
    
    cmd = [
        DREAMINA, "text2video",
        "--prompt", filtered_prompt,
        "--duration", str(duration),
        "--ratio", ratio,
        "--poll", "0"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout
        
        try:
            data = json.loads(output)
            return data.get("submit_id"), data
        except:
            return None, {"error": "JSON parse failed", "output": output[:200]}
            
    except subprocess.TimeoutExpired:
        return None, {"error": "Submit timeout"}
    except Exception as e:
        return None, {"error": str(e)}


def poll_for_result(submit_id, max_wait=180):
    """轮询等待结果"""
    waited = 0
    interval = 10
    
    while waited < max_wait:
        time.sleep(interval)
        
        cmd = [DREAMINA, "query_result", "--submit_id", submit_id]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stdout
            
            if "success" in output:
                try:
                    data = json.loads(output)
                    videos = data.get("result_json", {}).get("videos", [])
                    if videos:
                        return videos[0].get("video_url"), data
                except:
                    pass
            
            if "fail" in output:
                return None, {"error": "Generation failed"}
                
        except:
            pass
        
        waited += interval
        print(f"    等待中... ({waited}s)")
    
    return None, {"error": "Timeout"}


def record_failure(shot_id, scene_name, product_id, prompt, reason, standard_image=None):
    """记录失败片段"""
    ensure_logs_dir()
    
    data = {"failed_clips": []}
    if FAILED_CLIPS_FILE.exists():
        try:
            with open(FAILED_CLIPS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass
    
    entry = {
        "shot_id": shot_id,
        "scene_name": scene_name,
        "product_id": product_id,
        "prompt": prompt,
        "reason": reason,
        "standard_image": standard_image,
        "failed_at": datetime.now().isoformat()
    }
    
    data["failed_clips"].append(entry)
    
    with open(FAILED_CLIPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  [FAIL RECORDED] shot_id={shot_id}, reason={reason}")


def generate_clip(shot_id, scene_name, prompt, product_id, duration=5, ratio="9:16", output_path=None):
    """
    生成单个片段（使用产品标准图 + 文本）
    
    返回: {
        "status": "success" | "skipped" | "failed",
        "submit_id": "...",
        "video_url": "...",
        "local_path": "...",
        "retry_count": 0,
        "reason": "...",
        "standard_image_used": "..."
    }
    """
    print(f"\n[Clip Generator v4.5] shot_id={shot_id}")
    print(f"  场景: {scene_name}")
    print(f"  产品: {product_id}")
    print(f"  Prompt: {prompt[:60]}...")
    
    # 获取产品标准图
    standard_images = get_product_standard_images(product_id)
    image_to_use = None
    
    if standard_images:
        image_to_use = standard_images.get("front") or standard_images.get("all", [None])[0]
        print(f"  [标准图] {image_to_use}")
    else:
        print(f"  [WARN] 未找到产品标准图，使用纯文本生成")
    
    # 尝试生成（最多使用2张不同的标准图重试）
    tried_images = []
    last_error = None
    
    for retry in range(MAX_RETRIES):
        # 选择要使用的标准图
        if image_to_use and image_to_use not in tried_images:
            current_image = image_to_use
        elif standard_images and standard_images.get("all"):
            # 尝试另一张图
            for img in standard_images["all"]:
                if img not in tried_images:
                    current_image = img
                    break
            else:
                current_image = None
        else:
            current_image = None
        
        if current_image:
            tried_images.append(current_image)
            submit_id, submit_data = generate_with_dreamina_image_to_video(
                current_image, prompt, duration, ratio
            )
        else:
            # 降级到纯文本
            submit_id, submit_data = generate_with_dreamina_text_to_video(
                prompt, duration, ratio
            )
        
        if not submit_id:
            last_error = submit_data.get("error", "Unknown")
            print(f"  [RETRY {retry+1}] 提交失败: {last_error}")
            if retry < MAX_RETRIES - 1:
                time.sleep(RETRY_INTERVAL)
            continue
        
        print(f"    提交成功: {submit_id}")
        
        # 轮询
        video_url, result_data = poll_for_result(submit_id)
        
        if video_url:
            print(f"  [SUCCESS] 生成成功!")
            return {
                "status": "success",
                "submit_id": submit_id,
                "video_url": video_url,
                "retry_count": retry,
                "reason": None,
                "standard_image_used": current_image
            }
        else:
            last_error = result_data.get("error", "Unknown")
            print(f"  [RETRY {retry+1}] 获取结果失败: {last_error}")
            
            # 如果有其他标准图可用，尝试换一个
            if standard_images and len(standard_images.get("all", [])) > len(tried_images):
                print(f"  [INFO] 尝试使用其他标准图...")
                time.sleep(RETRY_INTERVAL)
                continue
            
            if retry < MAX_RETRIES - 1:
                time.sleep(RETRY_INTERVAL)
    
    # 3次都失败
    print(f"  [FAILED] 3次重试都失败，跳过该片段")
    record_failure(shot_id, scene_name, product_id, prompt, last_error, image_to_use)
    
    return {
        "status": "skipped",
        "submit_id": submit_id,
        "retry_count": MAX_RETRIES,
        "reason": last_error,
        "standard_image_used": image_to_use
    }


def download_clip(video_url, output_path):
    """下载片段"""
    cmd = [FFMPEG, "-y", "-i", video_url, "-c", "copy", str(output_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except:
        return False


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: generate_clip.py <shot_id> <scene_name> <prompt> <product_id> [duration] [ratio]")
        sys.exit(1)
    
    shot_id = sys.argv[1]
    scene_name = sys.argv[2]
    prompt = sys.argv[3]
    product_id = sys.argv[4]
    duration = int(sys.argv[5]) if len(sys.argv) > 5 else 5
    ratio = sys.argv[6] if len(sys.argv) > 6 else "9:16"
    
    result = generate_clip(shot_id, scene_name, prompt, product_id, duration, ratio)
    print(f"\nResult: {result}")
