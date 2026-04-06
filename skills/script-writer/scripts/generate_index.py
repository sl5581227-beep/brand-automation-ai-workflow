#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, shutil, subprocess, tempfile, re
from pathlib import Path

os.environ['HF_HOME'] = 'D:/AI Models/HuggingFace'
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

VIDEO_DIR = Path(r"C:\Users\Administrator\Desktop\素材01")
FFPROBE = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffprobe.exe"
FFMPEG = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"

model = None
tokenizer = None

def load_model():
    global model, tokenizer
    if model is None:
        print("Loading Qwen-VL...")
        from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            'Qwen/Qwen2-VL-2B-Instruct', device_map='auto')
        tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2-VL-2B-Instruct')
        print("Model loaded!")
    return model, tokenizer

def get_duration(path):
    try:
        r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", 
                          "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except:
        return 0

def extract_frames(video_path, out_dir, n=3):
    frames = []
    total = get_duration(video_path)
    if total <= 0:
        return frames
    for i in range(n):
        ts = total * (i + 1) / (n + 1)
        fp = out_dir / f"frame_{i}.jpg"
        subprocess.run([FFMPEG, "-y", "-ss", str(ts), "-i", str(video_path),
                       "-vframes", "1", "-q:v", "2", str(fp)],
                      capture_output=True, timeout=30)
        if fp.exists():
            frames.append(fp)
    return frames

def analyze_frame(fp, model, tokenizer):
    try:
        from PIL import Image
        img = Image.open(fp).convert('RGB')
        q = "Describe this product image. Output JSON: {product, action, tags, quality}"
        msgs = [{"role": "user", "content": [{"type": "image", "image": str(fp)}, {"type": "text", "text": q}]}]
        text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text=[text], images=[img], return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        out = model.generate(**inputs, max_new_tokens=128)
        resp = tokenizer.decode(out[0], skip_special_tokens=True)
        m = re.search(r'\{.*?\}', resp, re.DOTALL)
        if m:
            return json.loads(m.group(0).replace("'", '"'))
    except Exception as e:
        print(f"Error: {e}")
    return {"product": "unknown", "action": "unknown", "tags": "", "quality": "normal"}

def main():
    print("="*60)
    print("v5.1 Video Material Index Generator")
    print("="*60)
    
    temp = Path(tempfile.gettempdir()) / "vganalysis"
    temp.mkdir(exist_ok=True)
    
    video_dir = None
    for d in VIDEO_DIR.iterdir():
        if d.is_dir():
            if list(d.glob("*.MOV")) or list(d.glob("*.mp4")):
                video_dir = d
                break
    
    if not video_dir:
        print("Video dir not found")
        return
    
    videos = sorted(video_dir.glob("*.MOV")) + sorted(video_dir.glob("*.mp4"))
    print(f"Found {len(videos)} videos")
    
    load_model()
    results = []
    
    for i, v in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] {v.name[:40]}...")
        vt = temp / f"v{i}"
        vt.mkdir(exist_ok=True)
        
        frames = extract_frames(v, vt)
        if frames:
            r = analyze_frame(frames[0], model, tokenizer)
            r["file"] = v.name
            r["duration"] = round(get_duration(v), 1)
            results.append(r)
            print(f"  -> {r.get('product', '?')} / {r.get('action', '?')}")
        
        shutil.rmtree(vt, ignore_errors=True)
    
    if results:
        jp = video_dir.parent / f"{video_dir.name}_material.json"
        with open(jp, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nSaved: {jp}")
    
    print("="*60)
    print(f"Done! {len(results)} videos analyzed")
    print("="*60)

if __name__ == "__main__":
    main()
