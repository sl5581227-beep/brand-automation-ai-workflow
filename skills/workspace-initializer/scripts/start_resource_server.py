#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared Resource Server - 本地资源浏览服务器
提供简单的 Web 界面浏览和下载 shared_library 中的资源
"""

import os
import sys
import json
import mimetypes
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# UTF-8 support
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SHARED_LIB = Path(__file__).parent.parent.parent.parent / "knowledge_base" / "shared_library"
PORT = 8080

# HTML 模板
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shared Resource Library - 共享资源库</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .info {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .folder {{
            background: #fff;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .folder-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #4CAF50;
            margin-bottom: 10px;
        }}
        .file {{
            padding: 8px 10px;
            margin: 5px 0;
            background: #fafafa;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .file:hover {{
            background: #e8f5e9;
        }}
        .file-name {{
            flex: 1;
        }}
        .file-size {{
            color: #666;
            font-size: 0.9em;
            margin-right: 15px;
        }}
        .file-link {{
            color: #2196F3;
            text-decoration: none;
            padding: 5px 15px;
            background: #e3f2fd;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .file-link:hover {{
            background: #bbdefb;
        }}
        .meta {{
            color: #666;
            font-size: 0.85em;
            margin-top: 5px;
        }}
        .back-link {{
            color: #666;
            text-decoration: none;
            margin-bottom: 20px;
            display: inline-block;
        }}
        .back-link:hover {{
            color: #4CAF50;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }}
        .stat {{
            background: #4CAF50;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>📁 Shared Resource Library - 共享资源库</h1>
    
    <div class="info">
        <strong>资源库路径:</strong> {shared_lib_path}<br>
        <strong>服务器时间:</strong> {server_time}<br>
        <div class="stats">
            <span class="stat">📹 视频: {video_count} 个</span>
            <span class="stat">📝 热词: {hotspot_count} 个</span>
            <span class="stat">📄 脚本: {script_count} 个</span>
        </div>
    </div>
    
    <a href="/" class="back-link">← 刷新</a>
    
    <h2>📂 目录结构</h2>
    {content}
    
    <hr>
    <footer style="color:#666;text-align:center;margin-top:30px;">
        <p>Shared Resource Library v4.2 | Powered by OpenClaw</p>
        <p>仅限本地访问 (127.0.0.1)</p>
    </footer>
</body>
</html>
"""


class ResourceHandler(SimpleHTTPRequestHandler):
    """自定义请求处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SHARED_LIB), **kwargs)
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == "/" or self.path == "/index.html":
            self.send_html_index()
        elif self.path.startswith("/download/"):
            # 文件下载
            filepath = self.path.replace("/download/", "")
            self.send_file_download(filepath)
        else:
            # 其他静态文件
            super().do_GET()
    
    def send_html_index(self):
        """发送 HTML 索引页面"""
        content = self.generate_index_html()
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))
    
    def send_file_download(self, filepath):
        """发送文件下载"""
        full_path = SHARED_LIB / filepath
        
        if not full_path.exists():
            self.send_error(404, "File not found")
            return
        
        # 检测 MIME 类型
        mime_type, _ = mimetypes.guess_type(str(full_path))
        if mime_type is None:
            mime_type = "application/octet-stream"
        
        # 如果是 JSON，设置为下载
        if filepath.endswith(".json"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{full_path.name}"')
            with open(full_path, 'rb') as f:
                content = f.read()
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
            return
        
        # 否则发送静态文件
        super().path = f"/{filepath}"
        super().do_GET()
    
    def generate_index_html(self):
        """生成索引 HTML"""
        # 统计
        video_count = len(list((SHARED_LIB / "trending_videos").rglob("*.mp4")))
        hotspot_count = len(list((SHARED_LIB / "hotspots").rglob("*.json")))
        script_count = len(list((SHARED_LIB / "script_templates").rglob("*.md")))
        
        # 生成目录内容
        content_parts = []
        
        folders = [
            ("trending_videos", "📹", "爆款视频", "mp4,webm"),
            ("hotspots", "📝", "热词库", "json"),
            ("script_templates", "📄", "脚本模板", "md,json"),
            ("product_anchors", "🖼️", "产品视觉锚点", "png,jpg"),
            ("sample_clips", "🎬", "示例片段", "mp4"),
        ]
        
        for folder_name, icon, title, extensions in folders:
            folder_path = SHARED_LIB / folder_name
            
            if folder_path.exists():
                files_html = ""
                files = sorted(folder_path.rglob("*"))
                
                for f in files:
                    if f.is_file():
                        size = f.stat().st_size
                        if size > 1024 * 1024:
                            size_str = f"{size / (1024*1024):.1f} MB"
                        elif size > 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        else:
                            size_str = f"{size} B"
                        
                        rel_path = str(f.relative_to(SHARED_LIB))
                        ext = f.suffix.lower()
                        
                        if ext in [".mp4", ".webm"]:
                            type_icon = "🎬"
                        elif ext in [".json"]:
                            type_icon = "📋"
                        elif ext in [".md"]:
                            type_icon = "📝"
                        elif ext in [".png", ".jpg", ".jpeg"]:
                            type_icon = "🖼️"
                        else:
                            type_icon = "📄"
                        
                        files_html += f"""
                        <div class="file">
                            <span class="file-name">{type_icon} {f.name}</span>
                            <span class="file-size">{size_str}</span>
                            <a href="/{rel_path}" class="file-link">查看</a>
                        </div>
                        """
                
                if not files_html:
                    files_html = "<p style='color:#999'>暂无文件</p>"
                
                content_parts.append(f"""
                <div class="folder">
                    <div class="folder-name">{icon} {title}</div>
                    {files_html}
                </div>
                """)
        
        # 渲染模板
        html = HTML_TEMPLATE.format(
            shared_lib_path=str(SHARED_LIB),
            server_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            video_count=video_count,
            hotspot_count=hotspot_count,
            script_count=script_count,
            content="\n".join(content_parts)
        )
        
        return html.encode("utf-8")
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[ResourceServer] {args[0]}")


def start_server(port=PORT):
    """启动服务器"""
    server = HTTPServer(("127.0.0.1", port), ResourceHandler)
    print("=" * 60)
    print("  Shared Resource Library Server")
    print("=" * 60)
    print(f"  Listening on: http://127.0.0.1:{port}")
    print(f"  Resource path: {SHARED_LIB}")
    print()
    print("  ⚠️  Only accessible from localhost")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Shared Resource Library Server")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port to listen on (default: {PORT})")
    args = parser.parse_args()
    
    if not SHARED_LIB.exists():
        print(f"[WARN] Shared library not found: {SHARED_LIB}")
        print("[WARN] Run init_workspace.py first to create the directory structure.")
    
    start_server(args.port)
