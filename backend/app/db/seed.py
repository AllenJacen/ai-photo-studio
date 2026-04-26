"""Seed script: creates tables and inserts initial scenes + AI model configs."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import engine, SessionLocal, Base
import app.models  # noqa: F401 — ensure all models are registered
from app.models.scene import Scene
from app.models.ai_model import AIModelConfig


SCENES = [
    # ── 婚纱系列 ──
    {
        "id": "wedding-garden", "name": "浪漫花园婚纱", "category": "wedding",
        "description": "在阳光照耀的玫瑰花园中，捕捉爱情最美好的瞬间",
        "thumbnail_url": "",
        "prompt_template": "wedding photography, romantic rose garden ceremony, golden hour sunlight, bokeh background, white wedding dress, bridal bouquet of roses, professional DSLR photography, 8K resolution, detailed",
        "negative_prompt": "deformed, blurry, bad anatomy, extra limbs, cartoon, unrealistic proportions, low quality, text, watermark",
        "recommended_model": "nano_banana", "supported_models": ["nano_banana", "flux_kontext", "seedream_4"],
        "credit_cost": 1, "is_premium": False, "sort_order": 1,
        "tags": ["热门", "情侣"], "default_params": {"aspect_ratio": "3:4", "style_strength": 7},
    },
    {
        "id": "wedding-castle", "name": "城堡宫廷婚纱", "category": "wedding",
        "description": "欧式古堡前，穿越时空的浪漫誓言",
        "thumbnail_url": "",
        "prompt_template": "wedding photography, medieval european castle, grand stone architecture, soft natural light, elegant white wedding gown, long veil, luxury romantic atmosphere, professional portrait photography, 8K",
        "negative_prompt": "deformed, blurry, bad anatomy, modern elements, cartoon, low quality",
        "recommended_model": "flux_kontext", "supported_models": ["flux_kontext", "nano_banana", "kling_image"],
        "credit_cost": 1, "is_premium": False, "sort_order": 2,
        "tags": ["热门"], "default_params": {"aspect_ratio": "3:4", "style_strength": 7},
    },
    {
        "id": "wedding-beach", "name": "海边日落婚纱", "category": "wedding",
        "description": "夕阳下的沙滩，海风吹起的白色婚纱",
        "thumbnail_url": "",
        "prompt_template": "beach wedding photography, sunset golden hour, ocean waves, white sandy beach, flowing wedding dress, barefoot, silhouette against sunset, warm romantic light, 8K professional photography",
        "negative_prompt": "deformed, blurry, bad anatomy, cartoon, low quality, dark",
        "recommended_model": "nano_banana", "supported_models": ["nano_banana", "flux_kontext", "seedream_4"],
        "credit_cost": 1, "is_premium": False, "sort_order": 3,
        "tags": ["新上线"], "default_params": {"aspect_ratio": "16:9", "style_strength": 6},
    },
    {
        "id": "wedding-chinese", "name": "中式红妆婚纱", "category": "wedding",
        "description": "传统中式婚礼，凤冠霞帔，百年好合",
        "thumbnail_url": "",
        "prompt_template": "traditional chinese wedding photography, red qipao dress, phoenix crown headdress, ornate gold jewelry, red lanterns, festive red background, chinese cultural elements, professional portrait, 8K",
        "negative_prompt": "deformed, blurry, western elements, modern, cartoon, low quality",
        "recommended_model": "seedream_4", "supported_models": ["seedream_4", "nano_banana", "qwen_image"],
        "credit_cost": 1, "is_premium": False, "sort_order": 4,
        "tags": ["热门"], "default_params": {"aspect_ratio": "3:4", "style_strength": 8},
    },
    # ── 时尚写真 ──
    {
        "id": "portrait-ins", "name": "ins 清新写真", "category": "portrait",
        "description": "清新自然的 ins 风，简约美学极致表达",
        "thumbnail_url": "",
        "prompt_template": "instagram style portrait photography, clean minimalist aesthetic, soft pastel tones, natural light, casual chic fashion, lifestyle photography, bokeh background, high fashion editorial, 4K",
        "negative_prompt": "deformed, blurry, cluttered, dark, moody, cartoon, low quality",
        "recommended_model": "nano_banana", "supported_models": ["nano_banana", "flux_kontext", "kling_image"],
        "credit_cost": 1, "is_premium": False, "sort_order": 5,
        "tags": ["热门", "新上线"], "default_params": {"aspect_ratio": "3:4", "style_strength": 6},
    },
    {
        "id": "portrait-magazine", "name": "杂志封面大片", "category": "portrait",
        "description": "高端杂志封面风格，时尚感爆棚",
        "thumbnail_url": "",
        "prompt_template": "high fashion magazine cover photography, editorial style, dramatic lighting, couture fashion, professional makeup, studio background, Vogue style, luxury brand aesthetic, 8K ultra high resolution",
        "negative_prompt": "deformed, blurry, casual, low quality, cartoon, amateur",
        "recommended_model": "kling_image", "supported_models": ["kling_image", "flux_kontext", "mj_v7"],
        "credit_cost": 2, "is_premium": True, "sort_order": 6,
        "tags": ["会员专享"], "default_params": {"aspect_ratio": "3:4", "style_strength": 8},
    },
    {
        "id": "portrait-cyberpunk", "name": "赛博朋克都市", "category": "portrait",
        "description": "未来感十足的赛博朋克霓虹世界",
        "thumbnail_url": "",
        "prompt_template": "cyberpunk portrait photography, neon lights, futuristic city, rain-soaked streets, high tech fashion, glowing elements, blade runner aesthetic, dramatic blue and pink lighting, 4K cinematic",
        "negative_prompt": "deformed, blurry, soft, natural, daytime, cartoon, low quality",
        "recommended_model": "gpt_image_1", "supported_models": ["gpt_image_1", "mj_v7", "flux_kontext"],
        "credit_cost": 1, "is_premium": False, "sort_order": 7,
        "tags": ["热门"], "default_params": {"aspect_ratio": "3:4", "style_strength": 9},
    },
    # ── 中国风 ──
    {
        "id": "chinese-hanfu", "name": "汉服古风写真", "category": "chinese_style",
        "description": "身着汉服，穿越千年古风，诗意东方美",
        "thumbnail_url": "",
        "prompt_template": "traditional hanfu photography, ancient chinese garden, bamboo forest, elegant silk robes, flowing sleeves, classical chinese beauty, poetry aesthetic, soft warm light, cherry blossoms, 8K",
        "negative_prompt": "deformed, blurry, modern, western, cartoon, low quality",
        "recommended_model": "seedream_4", "supported_models": ["seedream_4", "qwen_image", "nano_banana"],
        "credit_cost": 1, "is_premium": False, "sort_order": 8,
        "tags": ["热门", "新上线"], "default_params": {"aspect_ratio": "3:4", "style_strength": 8},
    },
    {
        "id": "chinese-dunhuang", "name": "敦煌飞天", "category": "chinese_style",
        "description": "敦煌壁画风格，飞天仙女降临人间",
        "thumbnail_url": "",
        "prompt_template": "dunhuang flying apsaras art style, ancient chinese murals, flowing scarves, lotus flowers, golden halo, vibrant mineral pigments, spiritual atmosphere, chinese heritage art, 8K detailed",
        "negative_prompt": "deformed, blurry, modern, realistic photo, cartoon, low quality",
        "recommended_model": "mj_v7", "supported_models": ["mj_v7", "gpt_image_1", "seedream_4"],
        "credit_cost": 2, "is_premium": True, "sort_order": 9,
        "tags": ["会员专享"], "default_params": {"aspect_ratio": "3:4", "style_strength": 9},
    },
    # ── 艺术风格 ──
    {
        "id": "art-oilpainting", "name": "古典油画写真", "category": "artistic",
        "description": "伦勃朗风格光影，古典油画质感人像",
        "thumbnail_url": "",
        "prompt_template": "oil painting portrait in the style of Rembrandt, classical chiaroscuro lighting, rich warm tones, visible brushstrokes, old master technique, museum quality, detailed fabric textures, 8K",
        "negative_prompt": "deformed, bad anatomy, modern style, photography, cartoon, low quality",
        "recommended_model": "gpt_image_1", "supported_models": ["gpt_image_1", "mj_v7"],
        "credit_cost": 1, "is_premium": False, "sort_order": 10,
        "tags": ["热门"], "default_params": {"aspect_ratio": "3:4", "style_strength": 9},
    },
    {
        "id": "art-watercolor", "name": "水彩插画风格", "category": "artistic",
        "description": "梦幻水彩插画，轻盈如诗的艺术写真",
        "thumbnail_url": "",
        "prompt_template": "watercolor illustration portrait, soft pastel colors, flowing paint edges, dreamy translucent washes, botanical elements, whimsical fairy tale atmosphere, professional illustration, 4K",
        "negative_prompt": "deformed, photorealistic, dark, harsh, cartoon, low quality",
        "recommended_model": "gpt_image_1", "supported_models": ["gpt_image_1", "seedream_4", "mj_v7"],
        "credit_cost": 1, "is_premium": False, "sort_order": 11,
        "tags": ["新上线"], "default_params": {"aspect_ratio": "3:4", "style_strength": 9},
    },
    # ── 奇幻主题 ──
    {
        "id": "fantasy-forest", "name": "精灵森林仙境", "category": "fantasy",
        "description": "踏入神秘精灵森林，感受奇幻魔法世界",
        "thumbnail_url": "",
        "prompt_template": "fantasy forest portrait, magical glowing mushrooms, ethereal light rays through ancient trees, fairy wings, mystical atmosphere, bioluminescent plants, enchanted woodland, 8K cinematic",
        "negative_prompt": "deformed, blurry, realistic, urban, modern, cartoon, low quality",
        "recommended_model": "mj_v7", "supported_models": ["mj_v7", "gpt_image_1", "flux_kontext"],
        "credit_cost": 1, "is_premium": False, "sort_order": 12,
        "tags": ["热门"], "default_params": {"aspect_ratio": "3:4", "style_strength": 9},
    },
    # ── 商务证件 ──
    {
        "id": "professional-headshot", "name": "商务职业头像", "category": "professional",
        "description": "专业商务形象，LinkedIn / 简历首选",
        "thumbnail_url": "",
        "prompt_template": "professional business headshot photography, clean white background, confident expression, business attire, studio lighting, sharp focus, corporate portrait style, LinkedIn profile photo, 4K",
        "negative_prompt": "deformed, blurry, casual, colorful background, cartoon, low quality",
        "recommended_model": "nano_banana", "supported_models": ["nano_banana", "flux_kontext"],
        "credit_cost": 1, "is_premium": False, "sort_order": 13,
        "tags": ["实用"], "default_params": {"aspect_ratio": "1:1", "style_strength": 5},
    },
]

AI_MODELS = [
    {
        "id": "cogview_3_flash",
        "display_name": "智谱 CogView-3-Flash(免费)",
        "description": "智谱 AI 完全免费图像生成模型,无 token 限制,出图速度快,推荐首选",
        "provider": "zhipu",
        "model_type": "text2image",
        "capabilities": ["chinese_aesthetics", "free", "fast"],
        "credit_multiplier": 0.0,
        "avg_generation_time_s": 8,
        "max_resolution": "1792x1024",
        "is_active": True,
        "status": "available",
    },
    {
        "id": "cogview_4",
        "display_name": "智谱 CogView-4",
        "description": "智谱 AI 旗舰图像模型,质量更高,新用户送大额免费额度",
        "provider": "zhipu",
        "model_type": "text2image",
        "capabilities": ["chinese_aesthetics", "ultra_quality", "high_res"],
        "credit_multiplier": 1.0,
        "avg_generation_time_s": 15,
        "max_resolution": "2048x2048",
        "is_active": True,
        "status": "available",
    },
    {
        "id": "nano_banana",
        "display_name": "Nano Banana(Gemini 2.5 Flash Image)",
        "description": "Google 出品，人脸一致性极强、出图飞快，默认主力模型",
        "provider": "google",
        "model_type": "image2image",
        "capabilities": ["face_preservation", "fast", "img2img", "editing"],
        "credit_multiplier": 1.0,
        "avg_generation_time_s": 12,
        "max_resolution": "2048x2048",
        "is_active": True,
        "status": "available",
    },
    {
        "id": "seedream_4",
        "display_name": "豆包 Seedream 4.0",
        "description": "字节跳动出品，中式婚纱、汉服国风、东方人像首选",
        "provider": "bytedance",
        "model_type": "text2image",
        "capabilities": ["chinese_aesthetics", "portrait", "high_res"],
        "credit_multiplier": 1.0,
        "avg_generation_time_s": 20,
        "max_resolution": "4096x4096",
        "is_active": True,
        "status": "available",
    },
    {
        "id": "flux_kontext",
        "display_name": "Flux Kontext Pro",
        "description": "Black Forest Labs 出品，写实婚纱质感天花板，img2img 编辑能力强",
        "provider": "bfl",
        "model_type": "image2image",
        "capabilities": ["face_preservation", "ultra_quality", "img2img"],
        "credit_multiplier": 2.0,
        "avg_generation_time_s": 35,
        "max_resolution": "2048x2048",
        "is_active": True,
        "status": "available",
    },
    {
        "id": "gpt_image_1",
        "display_name": "GPT Image 1",
        "description": "OpenAI 上一代图像模型,艺术风格化 + 文字渲染",
        "provider": "openai",
        "model_type": "text2image",
        "capabilities": ["creative", "artistic", "text_rendering"],
        "credit_multiplier": 2.0,
        "avg_generation_time_s": 25,
        "max_resolution": "1536x1536",
        "is_active": True,
        "status": "available",
    },
    {
        "id": "gpt_image_2",
        "display_name": "OpenAI Image 2.0(GPT Image 2)",
        "description": "OpenAI 2026/04 最新旗舰,4K 出图、原生推理、99% 文字精度",
        "provider": "openai",
        "model_type": "text2image",
        "capabilities": ["creative", "reasoning", "text_rendering", "ultra_quality", "4k"],
        "credit_multiplier": 3.0,
        "avg_generation_time_s": 30,
        "max_resolution": "4096x4096",
        "is_active": True,
        "status": "available",
    },
    {
        "id": "qwen_image",
        "display_name": "通义 Qwen-Image-Edit",
        "description": "阿里出品,图生图模式,把你上传的人脸照换装到新场景,人脸保持强,国内直连",
        "provider": "alibaba",
        "model_type": "image2image",
        "capabilities": ["face_preservation", "img2img", "chinese_aesthetics"],
        "credit_multiplier": 1.0,
        "avg_generation_time_s": 20,
        "max_resolution": "2048x2048",
        "is_active": True,
        "status": "available",
    },
    {
        "id": "kling_image",
        "display_name": "可灵图像",
        "description": "快手出品，影视级人像质感，皮肤/发丝细节出色",
        "provider": "kuaishou",
        "model_type": "image2image",
        "capabilities": ["cinematic", "portrait", "skin_detail"],
        "credit_multiplier": 3.0,
        "avg_generation_time_s": 40,
        "max_resolution": "2048x2048",
        "is_active": True,
        "status": "available",
    },
    {
        "id": "mj_v7",
        "display_name": "Midjourney V7",
        "description": "艺术质感天花板，会员专享高端选项",
        "provider": "midjourney",
        "model_type": "text2image",
        "capabilities": ["artistic", "premium", "stylized"],
        "credit_multiplier": 3.0,
        "avg_generation_time_s": 50,
        "max_resolution": "2048x2048",
        "is_active": True,
        "status": "available",
    },
]


def seed():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Upsert scenes (update existing rows so model lists stay current)
        for s in SCENES:
            existing = db.query(Scene).filter(Scene.id == s["id"]).first()
            if existing:
                for k, v in s.items():
                    setattr(existing, k, v)
                print(f"  ~ Scene: {s['name']}")
            else:
                db.add(Scene(**s))
                print(f"  + Scene: {s['name']}")

        # Drop legacy AI model rows that aren't in the new spec
        valid_ids = {m["id"] for m in AI_MODELS}
        for old in db.query(AIModelConfig).all():
            if old.id not in valid_ids:
                db.delete(old)
                print(f"  - Removed legacy model: {old.id}")

        # Upsert AI models
        for m in AI_MODELS:
            existing = db.query(AIModelConfig).filter(AIModelConfig.id == m["id"]).first()
            if existing:
                for k, v in m.items():
                    setattr(existing, k, v)
                print(f"  ~ Model: {m['display_name']}")
            else:
                db.add(AIModelConfig(**m))
                print(f"  + Model: {m['display_name']}")

        db.commit()
        print(f"Seeded {len(SCENES)} scenes and {len(AI_MODELS)} AI models.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
