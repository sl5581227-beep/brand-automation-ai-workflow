---
name: Clip-Generator
description: 使用即梦AI生成视频镜头(6-10秒)，绝对禁止使用已有素材。每个片段必须通过产品外观核验和FFmpeg质量检测，不合格则重新生成（最多3次）。
trigger: 生成镜头|生成视频片段|制作镜头|AI生成视频|即梦生成
---

# Clip-Generator v4.0

## 🔴 绝对项

> **⚠️ 禁止使用已有素材，必须使用即梦AI生成全新片段**

```
❌ 错误流程：
即梦AI生成失败 → 降级使用现有素材切割

✅ 正确流程：
即梦AI生成失败 → 重试（最多3次） → 仍失败 → 标记并等待
                → 不得降级使用现有素材
```

---

## Instructions

### 1. 接收输入
- 提示词（英文）：描述画面内容、动作、光线、风格（≥50词）
- 产品参考图：来自素材01的产品标准图
- 时长：默认6秒，可选10秒
- 分辨率：1080p (1920x1080)

### 2. 调用即梦AI生成片段

**使用已登录的即梦AI**：
```bash
# 即梦AI登录状态：已登录（dreamina-login.json有效）
C:\Users\Administrator\bin\dreamina.exe generate \
    --prompt "your English prompt here" \
    --reference "path/to/product_image.png" \
    --duration 6 \
    --output "generated_clips/{product}_{date}/clip_{n}.mp4"
```

### 3. 等待生成完成
- 轮询任务状态（每30秒）
- 超时：5分钟/片段
- 重试次数：最多3次

### 4. 下载视频
- 保存到 `generated_clips/{产品名}_{日期}/clip_{n}.mp4`

### 5. 【片段QC - 第一道关】产品外观初步检查
- 快速检查片段是否包含正确的产品外观
- 如明显不符 → 直接判定FAIL（不浪费后续检测时间）

### 6. 【片段QC - 第二道关】FFmpeg质量检测
必须执行6项检测（见 ffmpeg-qc 技能），任何一项不通过 → FAIL

### 7. 【片段QC - 第三道关】质量评分
- 调用评估API
- 质量分数<60或存在明显瑕疵 → 丢弃 → 重试

### 8. 记录元数据
- 计算MD5哈希作为镜头ID
- 更新 `lens_db.json`

### 9. 输出
```
✅ 片段生成成功

**文件路径：** generated_clips/{产品名}_{日期}/clip_{n}.mp4
**镜头ID：** md5_hash
**质量分数：** 85/100
**FFmpeg检测：** 全部通过 ✅
**产品外观：** 通过 ✅
**状态：** 合格，可进入剪辑
```

---

## 质量评估标准

| 维度 | 要求 |
|------|------|
| 清晰度 | 无严重模糊 |
| 闪烁 | 无明显闪烁 |
| 连贯性 | 动作流畅 |
| 内容匹配 | 符合提示词描述 |
| **产品外观** | 必须与素材01产品标准匹配 |
| **FFmpeg检测** | 6项全部通过 |

---

## 重试机制

```
第1次生成 → QC检测 → 不合格 → 重试(1/3)
    ↓合格
记录元数据 → 返回成功
    ↓不合格(3次后)
返回失败，标记该片段不可用
```

---

## 禁止行为

- ❌ 使用已有视频素材切割
- ❌ 手动插入现成镜头
- ❌ 生成失败后降级使用现有素材
- ❌ 跳过FFmpeg检测
- ❌ 跳过产品外观核验

---

## 元数据结构 (lens_db.json)

```json
{
  "lenses": [
    {
      "id": "md5_hash_of_video_file",
      "prompt": "original prompt text",
      "created_at": "2026-04-04T10:00:00Z",
      "file_path": "generated_clips/{产品名}_{日期}/clip_{n}.mp4",
      "quality_score": 85,
      "ffmpeg_checks": {
        "error_check": "PASS",
        "resolution": "1920x1080",
        "blackdetect": "PASS",
        "freezedetect": "PASS",
        "volume": "-18 LUFS",
        "file_size": "8.2MB"
      },
      "appearance_check": "PASS",
      "is_usable": true,
      "used_in_final": false,
      "final_video_id": null
    }
  ]
}
```

---

## 使用示例

**用户：** "生成一个椰子水产品特写镜头"

**执行：**
```
🔄 正在调用即梦AI生成镜头...
📋 提示词：close-up of transparent coconut water bottle, cylindrical white bottle, morning natural light, realistic product photography style, showing clear liquid inside, 4K high quality...
📦 参考图：C:\Users\Administrator\Desktop\素材01\...\coconut_product.png

⏳ 等待AI生成（预计30秒）...
✅ 片段生成成功

**文件：** generated_clips/轻上椰子水_20260404/clip_01.mp4
**ID：** a3f2b8c1d4e5f6a7
**FFmpeg检测：** 全部通过 ✅
**产品外观：** 通过 ✅
**质量：** 88/100 ✅
```

---

## 集成到流程

```
Script-Writer → Clip-Generator(生成) → Product-Appearance-Check(核验) → FFmpeg-QC(检测)
                                                    ↓                       ↓
                                              FAIL → 重新生成            FAIL → 重新生成
                                                    ↓                       ↓
                                              PASS → 保存到generated_clips
```
