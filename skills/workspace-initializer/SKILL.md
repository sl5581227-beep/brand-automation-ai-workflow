---
name: Workspace-Initializer
description: 新部署龙虾自动初始化工具。检测首次运行，自动创建共享资源库目录结构，同步基础资源，检查依赖完整性。
trigger: 初始化工作区|首次运行|初始化|工作区设置|workspace init
---

# Workspace-Initializer v4.2

## 功能

1. **首次运行检测**：通过 `~/.openclaw/init_done` 标记文件判断是否首次部署
2. **自动创建目录结构**：在 `knowledge_base/shared_library/` 下创建完整目录
3. **同步基础资源**：从 GitHub 仓库下载基础资源包
4. **依赖检查**：验证 FFmpeg、Python 库是否完整
5. **初始化完成标记**：避免重复初始化

## 目录结构

```
knowledge_base/shared_library/
├── trending_videos/           # 爆款视频
│   ├── tiktok/
│   ├── youtube/
│   ├── douyin/
│   └── metadata.json
├── hotspots/                 # 热词库
├── script_templates/         # 脚本模板（Markdown格式）
├── product_anchors/         # 产品视觉锚点
├── sample_clips/            # 示例片段
└── README.md                # 说明文档
```

## 使用方式

### 自动调用（主控脚本启动时）
```python
from workspace_initializer import WorkspaceInitializer
initializer = WorkspaceInitializer()
if not initializer.is_initialized():
    initializer.initialize()
```

### 手动调用
```bash
python skills/workspace-initializer/scripts/init_workspace.py
```

## 初始化流程

1. 检查 `~/.openclaw/init_done` 是否存在
2. 如果不存在，执行初始化：
   - 创建目录结构
   - 下载基础资源（从 GitHub）
   - 检查 FFmpeg
   - 创建标记文件
3. 输出初始化报告

## 资源服务器

初始化完成后，员工可通过 Web 界面浏览资源：

```bash
python skills/workspace-initializer/scripts/start_resource_server.py --port 8080
```

访问地址：`http://localhost:8080`
