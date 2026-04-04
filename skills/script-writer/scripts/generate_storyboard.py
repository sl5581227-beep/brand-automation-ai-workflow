#!/usr/bin/env python3
"""
Script-Writer 核心脚本
基于故事板生成细致化视频脚本
- 每个镜头包含：画面描述、台词、时长、角度、提示词
- 提示词≥50词，符合MiniMax Hailuo API要求
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
METADATA_DIR = PROJECT_ROOT / "metadata" / "scripts"
HOTSPOT_DIR = PROJECT_ROOT / "knowledge_base" / "hotspots"


# 热词视觉映射
HOTWORD_VISUAL_MAP = {
    "清爽": ["condensation droplets on bottle", "ice cubes clinking", "cold refreshing tones", "crystal clear liquid"],
    "0糖": ["zero sugar label close-up", "sugar-free badge clearly visible", "nutrition facts display"],
    "天然": ["tropical coconut grove background", "fresh coconut ingredients", "green organic aesthetic"],
    "电解质": ["sweat droplets during workout", "energetic fitness movements", "gym scene"],
    "补水": ["hydrated skin glow", "water droplets", "cool refreshing sensation"],
    "夏日必备": ["beach tropical scene", "bright sunny weather", "tropical plants background"],
    "解渴": ["satisfying drinking expression", "thirst quenching moment", "refreshing relief"],
    "健康": ["green wellness theme", "natural ingredients", "healthy lifestyle"],
    "活力": ["energetic young people", "vibrant movements", "positive mood"],
    "椰香": ["coconut milk white color", "creamy coconut texture", "tropical coconut aroma"]
}


# 镜头提示词模板（≥50词）
SHOT_PROMPT_TEMPLATES = {
    "product_closeup": """close-up product shot of {bottle_desc}, {liquid_desc} inside, {surface_effect}, {angle_desc}, {lighting_desc}, {background_desc}, product occupies {frame_pct}% of frame, {movement_desc}, {vibe_desc}, 4K cinematic quality, {style_desc}""",

    "scene_med": """medium shot of {subject_desc}, {expression_desc}, {setting_desc}, {lighting_desc}, {framing_desc}, {mood_desc}, {camera_movement_desc}, realistic {genre_desc} cinematography, natural {emotion_desc}""",

    "lifestyle": """lifestyle scene showing {activity_desc}, {subject_desc} with {product_desc}, {setting_desc}, {lighting_desc}, {composition_desc}, warm inviting atmosphere, {camera_movement_desc}, {style_desc}""",

    "pour_drink": """macro close-up shot of {action_desc}, {liquid_color_desc}, {container_desc}, {sparkle_effect}, {speed_desc}, {lighting_desc}, background shows {bg_desc}, {camera_angle_desc}, 4K quality, {mood_desc}"""
}


def load_hotspot_library(product_name: str) -> dict:
    """加载热词库"""
    # 查找最新的热词库文件
    hotspot_files = list(HOTSPOT_DIR.glob(f"{product_name}*hotspots.json"))
    if hotspot_files:
        with open(hotspot_files[-1], "r", encoding="utf-8") as f:
            return json.load(f)
    
    # 返回默认热词
    return {
        "hotwords": [
            {"word": "清爽", "visual": "condensation droplets, cold refreshing"},
            {"word": "0糖", "visual": "zero sugar label"},
            {"word": "夏日必备", "visual": "beach, tropical"},
            {"word": "解渴", "visual": "refreshing thirst quenching"}
        ]
    }


def load_visual_anchors(product_name: str) -> dict:
    """加载产品视觉锚点"""
    kb_dir = PROJECT_ROOT / "knowledge_base" / "products"
    for product_dir in kb_dir.glob("*"):
        if product_dir.is_dir() and product_name[:4] in str(product_dir):
            anchor_file = product_dir / "anchors" / "visual_anchor_report.json"
            if anchor_file.exists():
                with open(anchor_file, "r", encoding="utf-8") as f:
                    return json.load(f)
    
    return {
        "visual_anchors": {
            "primary_colors": ["white", "green", "transparent"],
            "primary_shapes": ["圆柱形"]
        }
    }


def expand_prompt(prompt: str, min_words: int = 50) -> str:
    """确保提示词≥50个词"""
    words = prompt.split()
    if len(words) >= min_words:
        return prompt
    
    # 扩充词汇
    fillers = [
        "professional photography", "high detail", "premium quality", 
        "cinematic rendering", "vibrant colors", "natural lighting",
        "soft focus", "sharp details", "studio quality", "commercial grade"
    ]
    
    while len(words) < min_words:
        words.extend(fillers[:min_words - len(words)])
    
    return " ".join(words)


def generate_product_shot_prompt(shot_data: dict, visual_anchors: dict, hotwords: list) -> str:
    """为产品镜头生成详细提示词"""
    # 基础描述
    bottle_desc = "white cylindrical Qingshang coconut water bottle, sleek minimalist design, transparent bottle body showing clear liquid inside"
    liquid_desc = "crystal clear coconut water, pure natural, slight golden tint from椰子 essence"
    surface_effect = "fine condensation water droplets on cool bottle surface, catching soft light reflections"
    angle_desc = "45-degree top angle showing bottle front and side simultaneously"
    lighting_desc = "soft diffused natural light from upper left window, gentle highlights on bottle, subtle shadow on right"
    background_desc = "soft creamy bokeh with tropical green tones, suggesting coconut grove atmosphere"
    frame_pct = "65-70"
    movement_desc = "subtle slow push-in movement, camera逐渐逼近产品"
    vibe_desc = "premium healthy beverage aesthetic, summer refreshing vibe, clean modern feel"
    style_desc = "realistic food photography, commercial quality"
    
    prompt = SHOT_PROMPT_TEMPLATES["product_closeup"].format(
        bottle_desc=bottle_desc,
        liquid_desc=liquid_desc,
        surface_effect=surface_effect,
        angle_desc=angle_desc,
        lighting_desc=lighting_desc,
        background_desc=background_desc,
        frame_pct=frame_pct,
        movement_desc=movement_desc,
        vibe_desc=vibe_desc,
        style_desc=style_desc
    )
    
    # 融入热词视觉
    for hw in hotwords[:2]:
        if hw["word"] in HOTWORD_VISUAL_MAP:
            visual = HOTWORD_VISUAL_MAP[hw["word"]]
            prompt += f", {', '.join(visual[:2])}"
    
    return expand_prompt(prompt)


def generate_scene_shot_prompt(shot_data: dict, hotwords: list) -> str:
    """为场景镜头生成详细提示词"""
    scene = shot_data.get("scene_name", "")
    
    if "办公室" in scene or "办公" in scene:
        prompt = """medium shot of tired young woman sitting at modern office desk working on laptop computer, slightly fatigued expression with subtle stress, natural indoor fluorescent lighting with slightly cool tones, shoulder-up framing showing upper body, messy desk with scattered papers and coffee cup in background, realistic lifestyle cinematography, authentic tired office worker emotion, professional 4K quality"""
    elif "运动" in scene or "健身" in scene:
        prompt = """energetic fitness scene showing athletic person in modern gym setting wearing workout clothes, energetic dynamic pose with glistening sweat on forehead, bright airy gym interior with large windows showing natural light, camera at medium distance capturing full upper body movement, vibrant healthy lifestyle mood, fast-paced dynamic editing style, professional sports photography"""
    elif "海边" in scene or "沙滩" in scene:
        prompt = """tropical beach scene with crystal clear blue ocean water, white sandy beach, bright sunny day with gentle sea breeze, palm trees swaying in background, young beautiful person in summer outfit enjoying refreshing drink, warm golden hour lighting creating dreamy atmosphere, wide cinematic framing showing person and paradise setting, vacation vibes, professional travel photography quality"""
    elif "家庭" in scene or "室内" in scene:
        prompt = """cozy modern interior living room with large windows showing natural daylight streaming in, stylish minimalist decor with plants, young person relaxing on comfortable sofa holding a refreshing beverage, warm inviting home atmosphere, soft diffused lighting from windows, medium shot framing cozy lifestyle moment, peaceful relaxed mood, professional lifestyle photography"""
    else:
        prompt = f"""medium shot showing {scene}, natural ambient lighting, comfortable atmosphere, realistic lifestyle cinematography, professional quality"""
    
    # 融入热词
    for hw in hotwords[:2]:
        if hw["word"] in HOTWORD_VISUAL_MAP:
            prompt += f", {', '.join(HOTWORD_VISUAL_MAP[hw['word']][:2])}"
    
    return expand_prompt(prompt)


def generate_storyboard(product_name: str = "轻上椰子水", 
                        product_category: str = "椰子水",
                        target_duration: int = 55,
                        template: str = "痛点引入型") -> dict:
    """生成完整故事板"""
    print(f"Generating storyboard for: {product_name}")
    print(f"Target duration: {target_duration}s, Template: {template}")
    
    # 加载数据
    hotwords_data = load_hotspot_library(product_name)
    hotwords = hotwords_data.get("hotwords", [])[:6]  # 取TOP6热词
    visual_anchors = load_visual_anchors(product_name)
    
    print(f"Loaded {len(hotwords)} hotwords")
    
    # 热词列表
    hotword_list = [hw["word"] for hw in hotwords]
    print(f"Hotwords: {hotword_list}")
    
    # 故事板镜头
    shots = [
        {
            "shot_id": 1,
            "time_range": "0.0-4.5",
            "scene_name": "开场产品特写",
            "scene_desc": "近景特写，白色圆柱形瓶身，透明清澈椰子水，瓶身有细密水珠凝结，光线从左侧窗边射入柔和暖调，背景虚化为奶油色热带绿植感",
            "lighting": "左侧窗边自然光，柔和暖色调，背景虚化",
            "camera_angle": "45度俯拍，产品占画面65%",
            "color_theme": ["白色瓶身", "透明液体", "绿色点缀"],
            "actions": ["瓶身缓缓入画", "镜头缓慢推进"],
            "voiceover": "夏天最渴的时候怎么办？",
            "en_voiceover": "What do you drink when you're most thirsty in summer?",
            "duration_est": 4.5,
            "product_angle_required": "正面45度俯拍",
            "visual_elements": ["水珠凝结", "透明液体光泽", "清爽感"]
        },
        {
            "shot_id": 2,
            "time_range": "4.5-12.0",
            "scene_name": "痛点引入",
            "scene_desc": "年轻女性在现代办公室工作，表情略显疲惫，眉头微皱，桌面散落文件和咖啡杯，室内冷色调日光灯显得沉闷",
            "lighting": "室内日光灯，冷色调，显得沉闷",
            "camera_angle": "中景平视，肩部以上",
            "color_theme": ["灰色办公桌", "冷色光源", "沉闷感"],
            "actions": ["皱眉看电脑", "拿起饮料瓶又放下"],
            "voiceover": "白水没味道，奶茶太甜太腻，饮料糖分又太高...",
            "en_voiceover": "Plain water has no taste, milk tea is too sweet, drinks have too much sugar...",
            "duration_est": 7.5,
            "product_angle_required": "无产品入镜",
            "visual_elements": ["疲惫表情", "办公场景", "对比反差"]
        },
        {
            "shot_id": 3,
            "time_range": "12.0-18.0",
            "scene_name": "产品展示",
            "scene_desc": "特写展示轻上椰子水245mL瓶身，透明瓶身可见清澈液体，白底绿字标签，金色椰子图案，产品批号清晰",
            "lighting": "柔和顶光，产品有轻微高光，背景纯净白色",
            "camera_angle": "正面平视，产品占画面80%",
            "color_theme": ["白色标签", "绿色品牌色", "透明液体"],
            "actions": ["产品360度旋转展示", "标签信息逐一出镜"],
            "voiceover": "试试这个！轻上椰子水，0糖0脂肪，清爽无负担！",
            "en_voiceover": "Try this! Qingshang Coconut Water - zero sugar, zero fat, refreshing with no guilt!",
            "duration_est": 6.0,
            "product_angle_required": "正面平视/360度旋转",
            "visual_elements": ["产品全貌", "标签特写", "透明液体"]
        },
        {
            "shot_id": 4,
            "time_range": "18.0-25.0",
            "scene_name": "开瓶倒水特写",
            "scene_desc": "特写开瓶盖动作，白色塑料盖被拧开，清澈椰子水缓缓倒入透明玻璃杯，液体有轻微光泽感，气泡缓缓上升",
            "lighting": "顶光+侧光，液体有透亮感，深色背景突出产品",
            "camera_angle": "俯拍角度，玻璃杯占画面50%",
            "color_theme": ["奶白色液体", "透明玻璃", "深色背景"],
            "actions": ["拧开瓶盖", "倒水入杯", "气泡上升"],
            "voiceover": "甄选东南亚新鲜椰子，纯天然0添加，每天一瓶补充电解质",
            "en_voiceover": "Selected fresh Southeast Asian coconuts, 100% natural, daily electrolyte补充",
            "duration_est": 7.0,
            "product_angle_required": "产品开瓶/液体特写",
            "visual_elements": ["开瓶动作", "液体色泽", "清澈透明"]
        },
        {
            "shot_id": 5,
            "time_range": "25.0-33.0",
            "scene_name": "运动场景",
            "scene_desc": "健身房里年轻女性刚完成运动，额头有细密汗珠，表情满足阳光，拿起椰子水饮用，背景是现代明亮健身房",
            "lighting": "自然采光从大窗户射入，活力动感氛围",
            "camera_angle": "中近景，35度侧拍",
            "color_theme": ["活力橙色", "健康绿色", "阳光暖调"],
            "actions": ["运动后补水", "表情满足", "大口饮用"],
            "voiceover": "运动后来一瓶！快速补水又解乏，瞬间恢复满满活力！",
            "en_voiceover": "Perfect after workout! Rapid hydration and refreshment, instant energy recovery!",
            "duration_est": 8.0,
            "product_angle_required": "产品使用中",
            "visual_elements": ["运动汗水", "健身场景", "活力健康"]
        },
        {
            "shot_id": 6,
            "time_range": "33.0-40.0",
            "scene_name": "办公场景",
            "scene_desc": "现代办公室白领女性下午茶时间，阳光从窗户斜射进来，她手持椰子水表情轻松愉悦，背景是简洁办公桌和绿色盆栽",
            "lighting": "午后斜阳暖调，自然光从窗户进入，温馨氛围",
            "camera_angle": "中景平视，自然舒适",
            "color_theme": ["暖黄色阳光", "绿色植物", "清爽白色"],
            "actions": ["下午茶放松", "享受清凉饮品", "看窗外放空"],
            "voiceover": "工作累了来一杯，瞬间清爽恢复好状态！",
            "en_voiceover": "Feeling tired at work? One bottle instantly refreshes and restores good condition!",
            "duration_est": 7.0,
            "product_angle_required": "产品与人物结合",
            "visual_elements": ["办公场景", "下午茶感", "轻松愉悦"]
        },
        {
            "shot_id": 7,
            "time_range": "40.0-48.0",
            "scene_name": "卖点强调",
            "scene_desc": "分屏展示：左侧是产品瓶身和新鲜椰子原料，右侧是健身/办公/海边等多个使用场景，干净极简设计白色背景",
            "lighting": "双光源均匀打光，产品和场景都清晰呈现",
            "camera_angle": "分屏对称构图",
            "color_theme": ["清爽绿色", "活力橙色", "白色背景"],
            "actions": ["分屏切换展示", "卖点图标动画"],
            "voiceover": "零糖零脂低卡路里，清爽无负担，爱美人士的最爱！",
            "en_voiceover": "Zero sugar, zero fat, low calories - refreshing without the guilt! A favorite for beauty-conscious people!",
            "duration_est": 8.0,
            "product_angle_required": "产品+多场景",
            "visual_elements": ["分屏展示", "卖点可视化", "多场景"]
        },
        {
            "shot_id": 8,
            "time_range": "48.0-55.0",
            "scene_name": "品牌CTA",
            "scene_desc": "品牌Logo和产品瓶身特写叠加在热带海滩日落背景上，金色光芒笼罩画面，温暖又有高级感，结尾画面渐渐变亮",
            "lighting": "日落金色光芒，暖调高级感",
            "camera_angle": "产品特写居中，背景虚化",
            "color_theme": ["日落金色", "品牌绿", "高级感"],
            "actions": ["Logo呈现", "光芒效果", "画面渐亮"],
            "voiceover": "轻上大品牌，品质有保障！东南亚原装进口，立即购买体验清凉一夏！",
            "en_voiceover": "Qingshang - trusted brand! Southeast Asia imported. Buy now and enjoy a cool summer!",
            "duration_est": 7.0,
            "product_angle_required": "品牌+产品特写",
            "visual_elements": ["品牌Logo", "热带背景", "高级质感"]
        }
    ]
    
    # 生成提示词
    for shot in shots:
        if "产品" in shot["scene_name"] or "特写" in shot["scene_name"]:
            shot["prompt_for_api"] = generate_product_shot_prompt(shot, visual_anchors, hotwords)
        else:
            shot["prompt_for_api"] = generate_scene_shot_prompt(shot, hotwords)
        
        # 检查词数
        word_count = len(shot["prompt_for_api"].split())
        shot["prompt_word_count"] = word_count
        if word_count < 50:
            print(f"  Warning: Shot {shot['shot_id']} prompt only {word_count} words")
    
    # 计算总时长
    total_duration = sum(shot["duration_est"] for shot in shots)
    
    # 构建故事板
    storyboard = {
        "id": f"storyboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "product": product_name,
        "product_category": product_category,
        "total_duration_est": total_duration,
        "target_duration": target_duration,
        "template": template,
        "hotwords_used": hotword_list,
        "shots": shots,
        "product_reference": {
            "description": "轻上椰子水245mL，圆柱形白色瓶身，透明液体，白底绿字标签"
        },
        "created_at": datetime.now().isoformat()
    }
    
    return storyboard


def save_storyboard(storyboard: dict, output_dir: Path = None) -> Path:
    """保存故事板到文件"""
    if output_dir is None:
        output_dir = METADATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    product = storyboard["product"].replace(" ", "_")
    filename = f"{product}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_storyboard.json"
    filepath = output_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(storyboard, f, ensure_ascii=False, indent=2)
    
    return filepath


def main():
    """命令行入口"""
    product_name = sys.argv[1] if len(sys.argv) > 1 else "轻上椰子水"
    product_category = sys.argv[2] if len(sys.argv) > 2 else "椰子水"
    target = int(sys.argv[3]) if len(sys.argv) > 3 else 55
    
    # 生成故事板
    storyboard = generate_storyboard(product_name, product_category, target)
    
    # 保存
    filepath = save_storyboard(storyboard)
    
    print(f"\n{'='*60}")
    print("  STORYBOARD GENERATED")
    print(f"{'='*60}")
    print(f"  Product: {storyboard['product']}")
    print(f"  Duration: {storyboard['total_duration_est']}s (target: {storyboard['target_duration']}s)")
    print(f"  Shots: {len(storyboard['shots'])}")
    print(f"  Hotwords: {storyboard['hotwords_used']}")
    print(f"\n  Shot prompts word count:")
    for shot in storyboard["shots"]:
        print(f"    Shot {shot['shot_id']}: {shot['prompt_word_count']} words")
    print(f"\n  Saved: {filepath}")


if __name__ == "__main__":
    main()
