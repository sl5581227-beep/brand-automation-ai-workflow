---
name: FFmpeg-QC
description: 使用FFmpeg对视频片段和成片进行6项质量检测：错误检测、分辨率、黑屏、冻结帧、音频音量、文件大小。任何一项不通过则判定为FAIL，是进入剪辑流程的前置条件。
trigger: FFmpeg检测|视频质量检测|片段QC|ffmpeg检查
---

# FFmpeg-QC v4.0

## 🔴 绝对项

> **⚠️ 每个片段必须通过FFmpeg全检才能进入剪辑**

```
片段生成 → 产品外观核验 → FFmpeg-QC → 通过 → 剪辑
                            ↓
                        FAIL → 重新生成该片段
```

---

## 6项检测标准

| # | 检测项 | 命令 | 通过标准 |
|---|--------|------|---------|
| 1 | 错误检测 | `ffmpeg -v error -i input.mp4 -f null -` | 无 error 输出 |
| 2 | 分辨率 | `ffprobe -select_streams v:0 -show_entries stream=width,height` | **竖屏9:16**: width ≥ 720 AND height ≥ 1280<br>**横屏16:9**: width ≥ 1280 AND height ≥ 720 |
| 3 | 黑屏检测 | `ffmpeg -i input.mp4 -vf "blackdetect=d=0.1:pix_th=0.00"` | 无 black_start:black_end |
| 4 | 冻结帧检测 | `ffmpeg -i input.mp4 -vf "freezedetect=n=-30dB:d=0.1"` | 无 frozen 区域 |
| 5 | 音频音量 | `ffmpeg -i input.mp4 -af volumedetect` | mean_volume: -23 ~ -14 LUFS |
| 6 | 文件大小 | `ls -l input.mp4` | 非0字节 |

---

## 检测脚本

```python
# scripts/ffmpeg_qc.py
import subprocess
import json
import os

FFMPEG = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
FFPROBE = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffprobe.exe"

def run_ffmpeg_qc(video_path: str) -> dict:
    """
    对视频进行6项FFmpeg质量检测
    
    Returns:
        {
            "status": "PASS/FAIL",
            "checks": {
                "error_check": {"status": "PASS/FAIL", "details": "..."},
                "resolution": {"status": "PASS/FAIL", "width": int, "height": int},
                "blackdetect": {"status": "PASS/FAIL", "details": "..."},
                "freezedetect": {"status": "PASS/FAIL", "details": "..."},
                "volume": {"status": "PASS/FAIL", "mean_volume_lufs": float},
                "file_size": {"status": "PASS/FAIL", "size_bytes": int}
            },
            "failed_checks": []
        }
    """
    
    results = {
        "video_path": video_path,
        "status": "PASS",
        "checks": {},
        "failed_checks": []
    }
    
    # 1. 文件存在检查
    if not os.path.exists(video_path):
        results["status"] = "FAIL"
        results["failed_checks"].append("file_not_found")
        return results
    
    # 2. 文件大小检查
    file_size = os.path.getsize(video_path)
    results["checks"]["file_size"] = {
        "status": "PASS" if file_size > 0 else "FAIL",
        "size_bytes": file_size
    }
    if file_size == 0:
        results["status"] = "FAIL"
        results["failed_checks"].append("file_size_zero")
    
    # 3. 错误检测
    error_result = subprocess.run(
        [FFMPEG, "-v", "error", "-i", video_path, "-f", "null", "-"],
        capture_output=True, text=True
    )
    has_error = "error" in error_result.stderr.lower()
    results["checks"]["error_check"] = {
        "status": "FAIL" if has_error else "PASS",
        "details": error_result.stderr[:200] if has_error else "No errors found"
    }
    if has_error:
        results["status"] = "FAIL"
        results["failed_checks"].append("error_check")
    
    # 4. 分辨率检测
    probe_result = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "json", video_path],
        capture_output=True, text=True
    )
    try:
        probe_data = json.loads(probe_result.stdout)
        streams = probe_data.get("streams", [{}])
        if streams:
            width = streams[0].get("width", 0)
            height = streams[0].get("height", 0)
            resolution_ok = width >= 1280 and height >= 720
            results["checks"]["resolution"] = {
                "status": "PASS" if resolution_ok else "FAIL",
                "width": width,
                "height": height
            }
            if not resolution_ok:
                results["status"] = "FAIL"
                results["failed_checks"].append("resolution")
        else:
            results["checks"]["resolution"] = {"status": "FAIL", "error": "No video stream found"}
            results["status"] = "FAIL"
            results["failed_checks"].append("resolution")
    except Exception as e:
        results["checks"]["resolution"] = {"status": "FAIL", "error": str(e)}
        results["status"] = "FAIL"
        results["failed_checks"].append("resolution")
    
    # 5. 黑屏检测
    black_result = subprocess.run(
        [FFMPEG, "-i", video_path, "-vf", "blackdetect=d=0.1:pix_th=0.00", "-f", "null", "-"],
        capture_output=True, text=True
    )
    has_black = "black_start" in black_result.stderr
    results["checks"]["blackdetect"] = {
        "status": "FAIL" if has_black else "PASS",
        "details": black_result.stderr[:200] if has_black else "No black frames detected"
    }
    if has_black:
        results["status"] = "FAIL"
        results["failed_checks"].append("blackdetect")
    
    # 6. 冻结帧检测
    freeze_result = subprocess.run(
        [FFMPEG, "-i", video_path, "-vf", "freezedetect=n=-30dB:d=0.1", "-f", "null", "-"],
        capture_output=True, text=True
    )
    has_freeze = "frozen" in freeze_result.stderr
    results["checks"]["freezedetect"] = {
        "status": "FAIL" if has_freeze else "PASS",
        "details": freeze_result.stderr[:200] if has_freeze else "No frozen frames detected"
    }
    if has_freeze:
        results["status"] = "FAIL"
        results["failed_checks"].append("freezedetect")
    
    # 7. 音频音量检测
    volume_result = subprocess.run(
        [FFMPEG, "-i", video_path, "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True
    )
    try:
        # 提取 mean_volume (单位dB，需要转换)
        stderr_lines = volume_result.stderr.split("\n")
        mean_vol_db = None
        for line in stderr_lines:
            if "mean_volume" in line:
                # 格式: [Parsed_volumedetect_0 @ xxx] mean_volume: -18.5 dBFS
                parts = line.split("mean_volume:")
                if len(parts) > 1:
                    mean_vol_db = float(parts[1].strip().split()[0].replace("dBFS", ""))
        
        if mean_vol_db is not None:
            # dBFS转LUFS近似（dBFS - 0 ≈ LUFS for typical content）
            mean_vol_lufs = mean_vol_db
            volume_ok = -23 <= mean_vol_lufs <= -14
            results["checks"]["volume"] = {
                "status": "PASS" if volume_ok else "FAIL",
                "mean_volume_lufs": mean_vol_lufs
            }
            if not volume_ok:
                results["status"] = "FAIL"
                results["failed_checks"].append("volume")
        else:
            results["checks"]["volume"] = {"status": "FAIL", "error": "Could not detect volume"}
            results["status"] = "FAIL"
            results["failed_checks"].append("volume")
    except Exception as e:
        results["checks"]["volume"] = {"status": "FAIL", "error": str(e)}
        results["status"] = "FAIL"
        results["failed_checks"].append("volume")
    
    return results


def qc_passed(results: dict) -> bool:
    """检查是否所有检测都通过"""
    return results.get("status") == "PASS"


def print_qc_report(results: dict):
    """打印检测报告"""
    print(f"\n{'='*50}")
    print(f"FFmpeg QC Report: {results['video_path']}")
    print(f"{'='*50}")
    print(f"Overall Status: {results['status']}")
    print()
    
    for check_name, check_result in results["checks"].items():
        status = check_result.get("status", "UNKNOWN")
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"  {status_icon} {check_name}: {status}")
        for key, value in check_result.items():
            if key != "status":
                print(f"      {key}: {value}")
    
    if results.get("failed_checks"):
        print(f"\nFailed Checks: {', '.join(results['failed_checks'])}")
    
    print(f"{'='*50}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ffmpeg_qc.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    results = run_ffmpeg_qc(video_path)
    print_qc_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if results["status"] == "PASS" else 1)
```

---

## 快速检测命令

```bash
# 完整检测（6项）
python skills/ffmpeg-qc/scripts/ffmpeg_qc.py "generated_clips/clip_01.mp4"

# 逐项检测
ffmpeg -v error -i input.mp4 -f null - 2>&1 | findstr /C:"error"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 input.mp4
ffmpeg -i input.mp4 -vf "blackdetect=d=0.1:pix_th=0.00" -f null - 2>&1 | findstr /C:"black_start"
ffmpeg -i input.mp4 -vf "freezedetect=n=-30dB:d=0.1" -f null - 2>&1 | findstr /C:"frozen"
ffmpeg -i input.mp4 -af volumedetect -f null - 2>&1 | findstr /C:"mean_volume"
```

---

## 输出示例

### 通过
```
==================================================
FFmpeg QC Report: generated_clips/clip_01.mp4
==================================================
Overall Status: PASS

  ✅ file_size: PASS (8,256,364 bytes)
  ✅ error_check: PASS
  ✅ resolution: PASS (1080x1920)
  ✅ blackdetect: PASS
  ✅ freezedetect: PASS
  ✅ volume: PASS (-18.2 LUFS)

==================================================
```

### 失败
```
==================================================
FFmpeg QC Report: generated_clips/clip_05.mp4
==================================================
Overall Status: FAIL

  ✅ file_size: PASS (6,123,456 bytes)
  ✅ error_check: PASS
  ✅ resolution: PASS (1080x1920)
  ✅ blackdetect: PASS
  ❌ freezedetect: FAIL (frozen 1.5s at 12.3s)
  ✅ volume: PASS (-19.5 LUFS)

Failed Checks: freezedetect
==================================================
```

---

## 集成到流程

```
Clip-Generator 生成片段
        ↓
Product-Appearance-Check（75%门槛）
        ↓
    ┌── PASS ──→ FFmpeg-QC（6项全检）
    │                        ↓
    │              ┌── PASS ──→ Video-Editor剪辑
    │              │
    └── FAIL ──→ 重新生成片段
                  │
                  └── FAIL(3次) → 跳过该片段
```

---

## 禁止行为

- ❌ 跳过FFmpeg检测直接进入剪辑
- ❌ 忽略检测结果继续使用不合格片段
- ❌ 修改检测参数以让片段通过
