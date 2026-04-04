---
name: Video-Editor
description: 使用FFmpeg将多个视频片段拼接，添加转场和背景音乐，输出最终成片。
trigger: 剪辑视频|拼接镜头|制作成片|合并视频
---

## Instructions

1. **接收输入**
   - 镜头文件列表（按顺序）
   - 可选：背景音乐路径
   - 可选：转场效果（默认无转场，直接切）

2. **生成filelist.txt**
   ```
   file 'clip1.mp4'
   file 'clip2.mp4'
   file 'clip3.mp4'
   ```

3. **FFmpeg拼接**
   ```bash
   ffmpeg -y -f concat -safe 0 -i filelist.txt -c copy combined.mp4
   ```

4. **混音（如有背景音乐）**
   ```bash
   ffmpeg -y -i combined.mp4 -i music.mp3 -c:v copy -c:a aac -shortest final.mp4
   ```

5. **输出成片**
   - 保存到 `final_videos/final_{timestamp}_{uuid}.mp4`
   - 计算MD5作为唯一追踪码

6. **更新元数据**
   - 将使用的镜头标记 `used_in_final=true`
   - 记录 `final_video_id` 到各镜头

7. **输出**
   ```
   ✅ 视频剪辑完成
   
   **成片路径：** final_videos/final_20260403_xyz789.mp4
   **追踪码：** md5_hash
   **使用镜头：** [clip_id_1, clip_id_2, ...]
   **时长：** 22秒
   **分辨率：** 1080x1920
   ```

## FFmpeg路径

```
C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe
```

## 转场效果（可选）

如需转场，在filelist中使用：
```
file 'clip1.mp4'
file 'transition.mp4'
file 'clip2.mp4'
```

或使用FFmpeg filter：
```bash
ffmpeg -i clip1.mp4 -i clip2.mp4 -filter_complex "[0:v][1:v]xfade" -c copy output.mp4
```

## 成片元数据 (final_db.json)

```json
{
  "finals": [
    {
      "id": "md5_hash_of_final_video",
      "created_at": "2026-04-03T10:30:00Z",
      "file_path": "final_videos/final_xxx.mp4",
      "duration": 22,
      "resolution": "1080x1920",
      "lens_ids": ["lens_1_id", "lens_2_id", ...],
      "script_path": "metadata/scripts/xxx_script.json",
      "quality_score": null,
      "status": "pending_qc"
    }
  ]
}
```

## 使用示例

**用户：** "把 clip1.mp4、clip2.mp4、clip3.mp4 拼接成片，加上背景音乐 bgm.mp3"

**输出：**
```
🔄 开始剪辑...
✅ 拼接完成：3个镜头 → combined.mp4
🔊 混音完成：添加背景音乐
💾 成片已保存：final_videos/final_20260403_xyz789.mp4
**追踪码：** a3f2b8c1d4e5f6a7b8c9d0
**时长：** 22秒
```
