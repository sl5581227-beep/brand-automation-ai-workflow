---
name: Product-Appearance-Check
description: 核验视频中产品外观与素材01产品资料库是否一致。75%门槛，每个片段必须检查，绝对禁止跳过检查进入剪辑。
trigger: 产品外观检查|核对产品|产品一致|验证产品外观|产品图片核对
---

# Product-Appearance-Check v4.0

## 🔴 绝对项

> **⚠️ 75%门槛，每个片段必须检查，绝对禁止跳过**

```
片段生成 → Product-Appearance-Check → PASS → FFmpeg-QC → 剪辑
                            ↓
                        FAIL → 重新生成（最多3次）
                            ↓
                      仍FAIL → 跳过该片段，生成替代片段
```

---

## 核心要求

### 1. 产品资料库位置
```
C:\Users\Administrator\Desktop\素材01\
├── product_catalog.txt
├── 全部商品手册 1.8.pptx
├── 商品手册 - 0902.pptx
├── 竞品分析视频.csv
└── 竞品分析视频.xlsx
```

### 2. 产品外观标准（示例：轻上椰子水245mL）

```json
{
  "轻上椰子水245mL": {
    "bottle_shape": "圆柱形纤细瓶",
    "bottle_color": "透明",
    "label_color": "白底绿字",
    "liquid_color": "清澈透明",
    "cap_color": "白色塑料盖",
    "prohibited_features": [
      "椰肉颗粒（这是生椰）",
      "浑浊液体",
      "粉色包装",
      "金属罐",
      "深色液体"
    ]
  }
}
```

---

## 执行步骤

### Step 1: 提取视频帧

```python
# 从视频中提取6个关键帧进行比对
timestamps = [1s, 5s, 10s, 15s, 20s, 25s]

ffmpeg -i clip.mp4 -ss {timestamp} -frames:v 1 frame_{n}.jpg
```

### Step 2: 分析每帧产品外观

检测内容：
- **瓶身形状**：圆柱形 vs 其他（非圆柱 = FAIL）
- **液体颜色**：透明清澈 vs 浑浊/深色/紫色
- **标签颜色**：白底绿字 vs 其他颜色
- **禁止特征**：椰肉/粉色/金属罐

### Step 3: 计算相似度

```python
# 综合评分
base_score = 100

# 液体颜色异常
if "紫色" in detected_colors:
    base_score -= 40
if "浑浊" in liquid_state:
    base_score -= 30
if "深色" in liquid_color:
    base_score -= 35

# 禁止特征
if "椰肉颗粒" in features:
    base_score -= 50  # 这是生椰的特征，不是椰子水
if "金属罐" in bottle_type:
    base_score -= 50

# 瓶身形状错误
if "非圆柱形" in bottle_shape:
    base_score -= 30

passed = base_score >= 75
```

### Step 4: 保存检查结果（必须）

**通过检查**：
```
C:\Users\Administrator\Desktop\qingShangVideos\generated_clips\{产品名}_{日期}\
├── clip_01_checked_passed.mp4
├── clip_02_checked_passed.mp4
└── ...
```

**拒绝检查**：
```
C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\rejected\{产品名}_{日期}\
├── clip_05_rejected_appearance.mp4
└── clip_05_rejected_report.json
```

### Step 5: 返回结果

```json
{
  "clip_id": "clip_05",
  "clip_path": "generated_clips/{产品名}_{日期}/clip_05.mp4",
  "status": "PASS/FAIL",
  "score": 82,
  "issues_found": [],
  "local_saved_path": "...",
  "checked_at": "2026-04-04T13:00:00Z"
}
```

---

## 检查清单

生成镜头时必须确认：
- [ ] 瓶身形状：圆柱形纤细瓶 ✓
- [ ] 液体颜色：透明清澈（非紫色/非浑浊）✓
- [ ] 标签颜色：白底绿字 ✓
- [ ] 无禁止特征（椰肉/浑浊/粉色/金属罐）✓
- [ ] **相似度 ≥ 75%** ✓

---

## 错误处理

| 情况 | 处理方式 |
|------|----------|
| 第1次检查FAIL | 重新生成该片段（1/3） |
| 第2次检查FAIL | 重新生成该片段（2/3） |
| 第3次检查FAIL | 跳过该片段，生成替代片段 |
| 无法提取帧 | 标记警告，人工确认 |

---

## 禁止行为

- ❌ 跳过产品外观检查直接进入剪辑
- ❌ 降低75%门槛
- ❌ 使用未通过检查的片段进行剪辑
- ❌ 修改检查标准以让片段通过

---

## 集成到流程

```
Clip-Generator 生成镜头
        ↓
Product-Appearance-Check（必须，75%门槛）
        ↓
    ┌── PASS ──→ 保存到generated_clips ──→ FFmpeg-QC
    │
    └── FAIL ──→ 保存到rejected ──→ 重新生成镜头（最多3次）
                                            ↓
                                      仍FAIL → 跳过该片段
```
