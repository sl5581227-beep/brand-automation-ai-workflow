---
name: Script-Writer
description: 基于故事板生成细致化视频脚本。每个镜头包含：画面描述（精确到颜色/光影/动作/产品角度）、对应台词、预估时长（3-8秒不固定）、需要的产品图片角度。将画面描述转换为MiniMax Hailuo API的详细提示词（≥50词）。
trigger: 生成故事板|详细脚本|写视频脚本|爆款脚本|细致化脚本
---

## 重大升级：从"镜头秒数"到"故事板"

**旧方式**：
```
镜头1：产品特写，3秒
镜头2：场景展示，5秒
```

**新方式（故事板）**：
```
镜头1 (0-4.5s)
├─ 画面：近景特写，白色圆柱形瓶身，透明清澈液体，瓶身有水珠凝结
│   光线：左侧窗边自然光，柔和暖色调，背景虚化
│   角度：45度俯拍，产品占画面60%
├─ 台词：「夏天最渴的时候怎么办？」
├─ 时长：4.5秒（根据配音节奏调整）
├─ 参考角度：产品手册-正面45度
└─ 提示词：...
```

## 输入

1. **产品信息**：来自 Brand-Analyzer
2. **热点信息**：来自 Trend-Searcher
3. **竞品分析**：来自 Competitor-Viral-Analyst（热词库+脚本库）
4. **产品视觉锚点**：来自 Product-Visual-Anchor

## 脚本结构

### 故事板JSON格式

```json
{
  "id": "storyboard_20260404_coconut",
  "product": "轻上椰子水245mL",
  "total_duration_est": 65,
  "target_duration": 55,
  "template": "痛点引入型",
  "hotwords_used": ["清爽", "0糖", "夏日必备", "解渴"],
  
  "shots": [
    {
      "shot_id": 1,
      "time_range": "0.0-4.5",
      "scene_name": "开场吸引",
      "scene_desc": "近景特写，白色圆柱形瓶身，透明清澈液体，瓶身有水珠凝结",
      "lighting": "左侧窗边自然光，柔和暖色调，背景虚化",
      "camera_angle": "45度俯拍，产品占画面60%",
      "color_theme": ["白色", "透明", "绿色点缀"],
      "actions": ["瓶子缓缓进入画面", "镜头缓慢推进"],
      "voiceover": "夏天最渴的时候怎么办？",
      "en_voiceover": "What do you drink when you're most thirsty in summer?",
      "duration_est": 4.5,
      "product_angle_required": "正面45度俯拍",
      "visual_elements": ["水珠特写", "透明液体", "清爽感"],
      "prompt_for_api": "close-up product shot of cylindrical white bottle with clear transparent liquid inside, condensation droplets on bottle surface, 45-degree top angle, soft natural window light from left side, warm tones, bokeh background, product occupies 60% of frame, slow push-in movement, summer refreshing vibe, 4K cinematic quality, realistic photography"
    },
    {
      "shot_id": 2,
      "time_range": "4.5-12.0",
      "scene_name": "痛点引入",
      "scene_desc": "年轻女性在办公室工作，表情疲惫，桌面杂乱",
      "lighting": "室内人工光，冷色调，显得沉闷",
      "camera_angle": "中景，平视，肩部以上",
      "color_theme": ["灰色", "冷色", "沉闷"],
      "actions": ["皱眉，看电脑，喝水动作被饮料瓶挡住"],
      "voiceover": "白水没味道，奶茶太甜太腻...",
      "en_voiceover": "Plain water is boring, milk tea is too sweet...",
      "duration_est": 7.5,
      "product_angle_required": "无产品",
      "visual_elements": ["疲惫表情", "办公场景", "对比感"],
      "prompt_for_api": "medium shot of tired young woman working at messy office desk, forehead slightly furrowed, looking at computer screen, feeling bored, cold indoor artificial lighting, dull color tones, shoulder-up framing, realistic lifestyle cinematography, natural expressions"
    }
  ],
  
  "product_reference_images": {
    "front_45": "knowledge_base/products/轻上椰子水/anchors/front_45.png",
    "side": "knowledge_base/products/轻上椰子水/anchors/side.png"
  },
  
  "assembly_notes": "开头用特写吸引注意，中间快切切换场景，结尾慢镜头营造氛围"
}
```

## 输出

### 保存位置
```
metadata/scripts/{product}_{timestamp}_storyboard.json
```

### 提示词要求

每个镜头的 `prompt_for_api` 必须：
1. **≥50个英文单词**
2. **包含**：
   - 镜头类型（close-up, medium shot, wide等）
   - 产品外观描述（颜色、形状、材质）
   - 光线（方向、色温、软硬）
   - 背景（虚化程度、颜色）
   - 动作/运动
   - 画质要求（4K, cinematic等）
   - 风格（realistic, vibrant等）

### 错误示例（太短）
```
"close-up of bottle"
```

### 正确示例（≥50词）
```
"close-up product shot of cylindrical white bottle with clear transparent coconut water liquid inside, condensation droplets on the cool bottle surface reflecting light, 45-degree top angle showing the minimalist white label with green Qingshang logo at center, soft natural diffused lighting from upper left creating gentle highlights on the bottle, shallow depth of field with creamy bokeh background in tropical green tones, product occupies 70% of frame, static camera slightly push-in movement, premium healthy beverage aesthetic, 4K ultra HD cinematic quality, professional food photography style, vibrant yet natural colors"
```

## 执行步骤

### Step 1: 读取输入数据

```python
# 读取所有必要数据
hotspot_lib = load_json("knowledge_base/hotspots/椰子水_hotspots.json")
script_templates = load_json("knowledge_base/hotspots/椰子水_scripts.json")
visual_anchors = load_json("knowledge_base/products/轻上椰子水/anchors/visual_anchor_report.json")
```

### Step 2: 选择脚本模板

根据热点分析和产品特性选择最合适的模板：
- 痛点引入型（适合功能性产品）
- ASMR特写型（适合展示产品质感）
- 场景演绎型（适合建立情感连接）

### Step 3: 生成故事板

为每个镜头生成：
- 精确的画面描述
- 对应的台词/旁白
- 预估时长（允许3-8秒）
- 需要的产品角度
- API提示词（≥50词）

### Step 4: 融入热词视觉元素

每个镜头必须包含≥2个热词的视觉表现：
```
热词"清爽" → 视觉元素：水珠、冷感、冰块
热词"0糖" → 视觉元素：产品标签特写、无糖标识
```

### Step 5: 转换为API提示词

将故事板中的画面描述扩展为MiniMax Hailuo API格式的详细英文提示词

## 热词视觉映射

```python
HOTWORD_VISUAL_MAP = {
    "清爽": ["水珠飞溅", "冰块碰撞", "冷色调背景", "液体光泽"],
    "0糖": ["产品标签特写", "无糖标识清晰可见", "成分表展示"],
    "天然": ["椰林背景", "新鲜椰子原料", "绿色有机感"],
    "电解质": ["运动汗水特写", "活力动作", "健身场景"],
    "补水": ["肌肤水润感", "液体特写", "清凉感"],
    "夏日必备": ["海边场景", "阳光明媚", "热带植物"]
}
```

## 时长处理

- **原始脚本**：60-90秒（允许更长）
- **目标时长**：55秒（或指定）
- **剪辑时动态卡点**：根据配音节奏调整每个镜头时长

## 集成到流程

```
Brand-Analyzer → Trend-Searcher → Competitor-Viral-Analyst
                                            ↓
                           Script-Writer（故事板生成）
                                            ↓
                                    Clip-Generator
```

## 输出示例

```
╔══════════════════════════════════════════════════════════╗
║           📝 故事板脚本已生成                          ║
╠══════════════════════════════════════════════════════════╣
║ 产品：轻上椰子水245mL | 模板：痛点引入型              ║
║ 预估时长：65秒 | 目标时长：55秒                      ║
║ 热词融入：清爽、0糖、夏日必备、解渴                   ║
╠══════════════════════════════════════════════════════════╣
║ 镜头数量：8个 | 镜头范围：3.5s - 8s                 ║
║ 提示词平均长度：68词（均≥50词✓）                    ║
╚══════════════════════════════════════════════════════════╝
```
