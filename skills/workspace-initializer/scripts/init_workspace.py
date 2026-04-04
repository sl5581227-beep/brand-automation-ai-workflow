#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workspace Initializer - 新部署自动初始化
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# UTF-8 support
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

OPENCLAW_DIR = Path.home() / ".openclaw"
INIT_DONE_FILE = OPENCLAW_DIR / "init_done"
WORKSPACE_DIR = Path(__file__).parent.parent.parent.parent / "workspace"
KNOWLEDGE_BASE = Path(__file__).parent.parent.parent.parent / "knowledge_base"
SHARED_LIB = KNOWLEDGE_BASE / "shared_library"
GITHUB_REPO = "sl5581227-beep/brand-automation-ai-workflow"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"

# 工具路径
FFMPEG = Path(r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe")
FFPROBE = Path(r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffprobe.exe")


def ensure_directory_structure():
    """创建目录结构"""
    print("[1/5] Creating directory structure...")
    
    dirs = [
        SHARED_LIB,
        SHARED_LIB / "trending_videos" / "tiktok",
        SHARED_LIB / "trending_videos" / "youtube",
        SHARED_LIB / "trending_videos" / "douyin",
        SHARED_LIB / "hotspots",
        SHARED_LIB / "script_templates",
        SHARED_LIB / "product_anchors",
        SHARED_LIB / "sample_clips",
        KNOWLEDGE_BASE / "products",
        KNOWLEDGE_BASE / "clip_cache.json".rsplit("/", 1)[0] if "clip_cache.json" in str(KNOWLEDGE_BASE) else KNOWLEDGE_BASE / "clips",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    print(f"  [OK] Created {len(dirs)} directories")
    return True


def check_dependencies():
    """检查依赖"""
    print("[2/5] Checking dependencies...")
    
    results = {}
    
    # FFmpeg
    ffmpeg_ok = FFMPEG.exists()
    results["ffmpeg"] = ffmpeg_ok
    print(f"  FFmpeg: {'OK' if ffmpeg_ok else 'NOT FOUND'}")
    
    # Python modules
    python_modules = ["requests", "PIL"]
    for module in python_modules:
        try:
            __import__(module.lower().replace("PIL", "PIL").replace("requests", "requests"))
            results[module] = True
            print(f"  {module}: OK")
        except ImportError:
            results[module] = False
            print(f"  {module}: NOT FOUND")
    
    return results


def download_base_resources():
    """从 GitHub 下载基础资源"""
    print("[3/5] Downloading base resources from GitHub...")
    
    resources = [
        "knowledge_base/hotspots/README.md",
        "knowledge_base/shared_library/README.md",
    ]
    
    downloaded = 0
    failed = []
    
    for resource in resources:
        try:
            url = f"{GITHUB_RAW_BASE}/{resource}"
            local_path = KNOWLEDGE_BASE / resource.split("/")[-1]
            
            response = requests_get(url)
            if response and response.status_code == 200:
                local_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                downloaded += 1
                print(f"  [OK] {resource}")
            else:
                failed.append(resource)
        except Exception as e:
            failed.append(f"{resource} ({e})")
    
    print(f"  Downloaded: {downloaded}/{len(resources)}")
    if failed:
        print(f"  Failed: {len(failed)} (will retry later)")
    
    return downloaded > 0


def requests_get(url, timeout=15):
    """发送 GET 请求"""
    try:
        import requests
        return requests.get(url, timeout=timeout)
    except:
        return None


def create_readme():
    """创建 README 文件"""
    print("[4/5] Creating README files...")
    
    readme_content = """# 共享资源库 (Shared Resource Library)

本目录包含所有可共享的品牌自动化资源，方便团队成员直接查看和使用。

## 目录结构

```
shared_library/
├── trending_videos/     # 爆款视频（按平台存放）
│   ├── tiktok/
│   ├── youtube/
│   ├── douyin/
│   └── metadata.json
├── hotspots/            # 热词库
├── script_templates/  # 脚本模板（Markdown格式，可直接查看）
├── product_anchors/   # 产品视觉锚点（产品标准图）
└── sample_clips/       # 示例镜头片段
```

## 使用方式

### 1. 查看爆款视频
进入 `trending_videos/{platform}/` 目录，查看 `metadata.json` 获取视频信息。

### 2. 查看热词库
进入 `hotspots/` 目录，查看热词 JSON 文件。

### 3. 查看脚本模板
进入 `script_templates/` 目录，以 Markdown 格式查看脚本模板。

### 4. 查看产品锚点
进入 `product_anchors/` 目录，查看各产品标准图。

## Web 界面

启动本地服务器浏览资源：

```bash
python skills/workspace-initializer/scripts/start_resource_server.py --port 8080
```

访问地址：http://localhost:8080

## 资源更新

资源由主控脚本自动更新：
- 新爆款视频自动下载到 `trending_videos/`
- 新热词库自动同步到 `hotspots/`
- 新脚本模板自动导出到 `script_templates/`

---
生成时间: """ + datetime.now().isoformat()
    
    readme_path = SHARED_LIB / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"  [OK] README.md created")
    return True


def mark_initialized():
    """标记初始化完成"""
    print("[5/5] Marking initialization as done...")
    
    OPENCLAW_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(INIT_DONE_FILE, 'w', encoding='utf-8') as f:
        f.write(json.dumps({
            "initialized_at": datetime.now().isoformat(),
            "version": "4.2",
            "workspace_dir": str(WORKSPACE_DIR),
            "shared_lib_dir": str(SHARED_LIB)
        }, ensure_ascii=False, indent=2))
    
    print(f"  [OK] Initialization marked")
    return True


def is_initialized():
    """检查是否已初始化"""
    return INIT_DONE_FILE.exists()


def initialize():
    """执行初始化"""
    print("=" * 60)
    print("  Workspace Initializer v4.2")
    print("=" * 60)
    print(f"  Time: {datetime.now()}")
    print(f"  User: {os.environ.get('USERNAME', 'Unknown')}")
    print("=" * 60)
    
    if is_initialized():
        print("\n[INFO] Workspace already initialized.")
        print(f"  Init file: {INIT_DONE_FILE}")
        with open(INIT_DONE_FILE, 'r', encoding='utf-8') as f:
            info = json.load(f)
            print(f"  Initialized at: {info.get('initialized_at', 'Unknown')}")
        return True
    
    print("\n[INFO] First-time setup detected. Starting initialization...")
    
    # 执行初始化步骤
    ensure_directory_structure()
    deps = check_dependencies()
    create_readme()
    
    # 下载基础资源（可选，失败不影响）
    try:
        download_base_resources()
    except:
        print("  [WARN] Could not download base resources (network issue)")
        print("  Resources will be synced when running main workflow")
    
    mark_initialized()
    
    print("\n" + "=" * 60)
    print("  INITIALIZATION COMPLETE!")
    print("=" * 60)
    print(f"\n  Shared Library: {SHARED_LIB}")
    print(f"  Trending Videos: {SHARED_LIB / 'trending_videos'}")
    print(f"  Script Templates: {SHARED_LIB / 'script_templates'}")
    print(f"  Product Anchors: {SHARED_LIB / 'product_anchors'}")
    print("\n  Dependencies:")
    print(f"    FFmpeg: {'OK' if deps.get('ffmpeg') else 'MISSING'}")
    print("\n  Next steps:")
    print("    1. Run main workflow: python run_v4.py <product>")
    print("    2. Start resource server: python start_resource_server.py --port 8080")
    print("    3. Browse resources at: http://localhost:8080")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    initialize()
