#!/usr/bin/env python3
"""
视频拼接脚本
- 使用 FFmpeg concat 拼接多个视频
- 可选添加背景音乐
- 输出最终成片
"""
import os
import sys
import json
import uuid
import hashlib
import subprocess
import tempfile
from datetime import datetime

# FFmpeg 路径
FFMPEG = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
BASE_DIR = r"C:\Users\Administrator\workspace\video_production"
FINAL_DIR = os.path.join(BASE_DIR, "final_videos")
META_DIR = os.path.join(BASE_DIR, "metadata")
LENS_DB = os.path.join(META_DIR, "lens_db.json")
FINAL_DB = os.path.join(META_DIR, "final_db.json")

def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def concatenate_videos(video_paths, output_path, music_path=None):
    """使用FFmpeg拼接视频"""
    # 创建临时filelist
    fd, filelist_path = tempfile.mkstemp(suffix='.txt', text=True)
    with os.fdopen(fd, 'w') as f:
        for video in video_paths:
            f.write(f"file '{video}'\n")
    
    try:
        # 拼接视频
        print("🔄 拼接视频...")
        result = subprocess.run([
            FFMPEG, '-y',
            '-f', 'concat', '-safe', '0',
            '-i', filelist_path,
            '-c', 'copy',
            output_path.replace('.mp4', '_combined.mp4')
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"拼接失败: {result.stderr[-500:]}")
        
        combined = output_path.replace('.mp4', '_combined.mp4')
        
        # 混音（如果有背景音乐）
        if music_path and os.path.exists(music_path):
            print("🔊 添加背景音乐...")
            result = subprocess.run([
                FFMPEG, '-y',
                '-i', combined,
                '-i', music_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                output_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"混音失败: {result.stderr[-500:]}")
            
            os.remove(combined)
        else:
            os.rename(combined, output_path)
        
        return True
        
    finally:
        os.remove(filelist_path)

def get_video_info(video_path):
    """获取视频信息（时长、分辨率）"""
    cmd = [
        FFMPEG.replace('ffmpeg', 'ffprobe'),
        '-v', 'error',
        '-show_entries', 'stream=width,height:format=duration',
        '-of', 'json',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        import json
        data = json.loads(result.stdout)
        streams = data.get('streams', [{}])
        format_info = data.get('format', {})
        duration = float(format_info.get('duration', 0))
        if streams:
            w = streams[0].get('width', 0)
            h = streams[0].get('height', 0)
            return duration, f"{w}x{h}"
    return 0, "unknown"

def main(video_paths, music_path=None, output_filename=None):
    """主函数"""
    print("=" * 60)
    print("视频剪辑")
    print("=" * 60)
    
    if not video_paths:
        print("❌ 没有提供视频文件")
        return None
    
    print(f"📹 输入: {len(video_paths)} 个镜头")
    
    # 生成输出文件名
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clip_id = str(uuid.uuid4())[:6]
        output_filename = f"final_{timestamp}_{clip_id}.mp4"
    
    os.makedirs(FINAL_DIR, exist_ok=True)
    output_path = os.path.join(FINAL_DIR, output_filename)
    
    # 拼接
    try:
        concatenate_videos(video_paths, output_path, music_path)
    except Exception as e:
        print(f"❌ {e}")
        return None
    
    # 计算MD5
    with open(output_path, 'rb') as f:
        tracking_id = hashlib.md5(f.read()).hexdigest()
    
    # 获取视频信息
    duration, resolution = get_video_info(output_path)
    
    # 更新镜头元数据
    lens_db = load_json(LENS_DB, {"lenses": []})
    for path in video_paths:
        with open(path, 'rb') as f:
            clip_hash = hashlib.md5(f.read()).hexdigest()
        
        for lens in lens_db.get("lenses", []):
            if lens.get("id") == clip_hash:
                lens["used_in_final"] = True
                lens["final_video_id"] = tracking_id
                print(f"  更新镜头: {clip_hash[:12]}...")
    
    save_json(LENS_DB, lens_db)
    
    # 记录成片
    final_db = load_json(FINAL_DB, {"finals": []})
    final_record = {
        "id": tracking_id,
        "created_at": datetime.now().isoformat(),
        "file_path": output_path,
        "duration": round(duration, 1),
        "resolution": resolution,
        "lens_ids": [hashlib.md5(open(p, 'rb').read()).hexdigest() for p in video_paths],
        "quality_score": None,
        "status": "pending_qc"
    }
    final_db["finals"].append(final_record)
    save_json(FINAL_DB, final_db)
    
    print(f"\n✅ 剪辑完成！")
    print(f"   输出: {output_path}")
    print(f"   追踪码: {tracking_id}")
    print(f"   时长: {duration:.1f}秒")
    print(f"   分辨率: {resolution}")
    
    return final_record

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python concatenate_videos.py <视频1.mp4> [视频2.mp4] ... [选项]")
        print("选项: --music <背景音乐.mp3>")
        sys.exit(1)
    
    video_paths = []
    music_path = None
    
    for arg in sys.argv[1:]:
        if arg == '--music' and music_path is None:
            continue
        elif arg == '--music':
            music_path = sys.argv[sys.argv.index(arg) + 1]
        else:
            video_paths.append(arg)
    
    main(video_paths, music_path)
