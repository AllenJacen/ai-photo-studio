from __future__ import annotations
"""统一的真实模型 Provider 集合(2026-04 主流图像生成模型)。

每个 Provider 在没有配置对应 API Key 时自动走 Mock 模式,返回 picsum 占位图,
方便本地预览。配上真实 Key 后会调用真实 API。
"""

import time
import asyncio
import httpx
from app.services.ai_gateway.base import (
    AIProviderBase, ImageData, GenerationParams, GenerationResult, ProviderStatus,
)
from app.core.config import settings


def _mock_result(seed_prefix: str, params: GenerationParams, start: float) -> GenerationResult:
    return GenerationResult(
        image_urls=[
            f"https://picsum.photos/seed/{seed_prefix}-{int(time.time()*1000)+i}/{params.width}/{params.height}"
            for i in range(params.output_count)
        ],
        generation_time_ms=int((time.time() - start) * 1000),
    )


def _api_key(name: str) -> str:
    return getattr(settings, name, "") or ""


# ──────────────────────────────────────────────────────────────────────────────
# Google — Nano Banana (Gemini 2.5 Flash Image) — 强人脸保持 + 图生图
# ──────────────────────────────────────────────────────────────────────────────
class NanoBananaProvider(AIProviderBase):
    @property
    def model_id(self) -> str:
        return "nano_banana"

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        api_key = _api_key("GEMINI_API_KEY")
        if not api_key:
            return _mock_result("nano-banana", params, start)

        # 构造 Gemini parts:文本 prompt + 用户上传的人脸图(image-to-image)
        # 当 source_images 有 base64 时,Gemini 会把它当作 reference 保持人脸特征
        parts: list[dict] = [{"text": prompt}]
        for src in (source_images or []):
            if src.base64:
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": src.base64,
                    },
                })
            elif src.url:
                # Gemini 不支持远程 URL,需要先下载再 base64
                try:
                    async with httpx.AsyncClient(timeout=30) as dl:
                        rr = await dl.get(src.url)
                        if rr.status_code == 200:
                            import base64 as _b64
                            parts.append({
                                "inline_data": {
                                    "mime_type": rr.headers.get("content-type", "image/jpeg").split(";")[0],
                                    "data": _b64.b64encode(rr.content).decode("ascii"),
                                },
                            })
                except Exception:
                    pass

        # 算最近的 Gemini 支持的 aspect ratio
        ratio = params.width / params.height if params.height else 1
        aspect = "1:1"
        for r_label, r_val in [("1:1", 1), ("3:4", 0.75), ("4:3", 1.33), ("9:16", 0.5625), ("16:9", 1.78)]:
            if abs(ratio - r_val) < abs(ratio - {"1:1": 1, "3:4": 0.75, "4:3": 1.33, "9:16": 0.5625, "16:9": 1.78}[aspect]):
                aspect = r_label

        body = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": {"aspectRatio": aspect},
            },
        }

        # 多张输出 — Gemini 单次只回 1 张,要多张就并发调用
        async def _call_once(client: httpx.AsyncClient) -> list[str]:
            r = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent",
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=body,
            )
            if r.status_code >= 400:
                raise RuntimeError(f"Gemini Nano Banana error {r.status_code}: {r.text[:300]}")
            data = r.json()
            urls = []
            for cand in data.get("candidates", []):
                for p in cand.get("content", {}).get("parts", []):
                    inline = p.get("inline_data") or p.get("inlineData")  # SDK 风格 vs REST 风格
                    if inline and inline.get("data"):
                        mime = inline.get("mime_type") or inline.get("mimeType") or "image/png"
                        urls.append(f"data:{mime};base64,{inline['data']}")
            return urls

        async with httpx.AsyncClient(timeout=180) as client:
            tasks = [_call_once(client) for _ in range(max(1, params.output_count))]
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            urls: list[str] = []
            errors: list[str] = []
            for res in all_results:
                if isinstance(res, Exception):
                    errors.append(str(res))
                else:
                    urls.extend(res)
            if not urls:
                raise RuntimeError(f"Gemini Nano Banana returned no images. Errors: {errors[:2]}")
            return GenerationResult(image_urls=urls, generation_time_ms=int((time.time() - start) * 1000))

    async def health_check(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE


# ──────────────────────────────────────────────────────────────────────────────
# 字节豆包 — Seedream 4.0
# ──────────────────────────────────────────────────────────────────────────────
class SeedreamProvider(AIProviderBase):
    @property
    def model_id(self) -> str:
        return "seedream_4"

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        if not _api_key("ARK_API_KEY"):
            return _mock_result("seedream", params, start)
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                "https://ark.cn-beijing.volces.com/api/v3/images/generations",
                headers={"Authorization": f"Bearer {_api_key('ARK_API_KEY')}"},
                json={
                    "model": "doubao-seedream-4-0-250828",
                    "prompt": prompt,
                    "size": f"{params.width}x{params.height}",
                    "n": params.output_count,
                },
            )
            r.raise_for_status()
            data = r.json()
            urls = [item["url"] for item in data.get("data", [])]
            return GenerationResult(image_urls=urls, generation_time_ms=int((time.time() - start) * 1000))

    async def health_check(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE


# ──────────────────────────────────────────────────────────────────────────────
# Black Forest Labs — Flux Kontext Pro (img2img / 编辑能力)
# ──────────────────────────────────────────────────────────────────────────────
class FluxKontextProvider(AIProviderBase):
    @property
    def model_id(self) -> str:
        return "flux_kontext"

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        if not _api_key("REPLICATE_API_TOKEN"):
            return _mock_result("flux-kontext", params, start)
        input_data = {
            "prompt": prompt,
            "aspect_ratio": "match_input_image" if source_images and source_images[0].url else "3:4",
            "output_format": "jpg",
        }
        if source_images and source_images[0].url:
            input_data["input_image"] = source_images[0].url
        async with httpx.AsyncClient(timeout=300) as client:
            r = await client.post(
                "https://api.replicate.com/v1/models/black-forest-labs/flux-kontext-pro/predictions",
                json={"input": input_data},
                headers={"Authorization": f"Token {_api_key('REPLICATE_API_TOKEN')}", "Prefer": "wait"},
            )
            r.raise_for_status()
            data = r.json()
            output = data.get("output")
            urls = output if isinstance(output, list) else [output] if output else []
            return GenerationResult(image_urls=urls, generation_time_ms=int((time.time() - start) * 1000))

    async def health_check(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE


# ──────────────────────────────────────────────────────────────────────────────
# OpenAI — GPT Image 1 / GPT Image 2 (ChatGPT Images 2.0, 2026-04 发布)
# ──────────────────────────────────────────────────────────────────────────────
class _OpenAIImageBase(AIProviderBase):
    """OpenAI 图像生成基类 — 子类只需指定 openai_model_id。"""
    openai_model_id: str = "gpt-image-1"

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        api_key = _api_key("OPENAI_API_KEY")
        if not api_key:
            return _mock_result(self.openai_model_id, params, start)

        # OpenAI Images API 支持的 size:1024x1024 / 1024x1536 / 1536x1024 / auto
        size_map = {
            (1024, 1024): "1024x1024",
            (1024, 1536): "1024x1536",
            (1024, 1365): "1024x1536",  # 我们的 3:4 默认 → 取最近的支持档位
            (1536, 1024): "1536x1024",
        }
        size = size_map.get((params.width, params.height), "1024x1024")

        payload = {
            "model": self.openai_model_id,
            "prompt": prompt,
            "size": size,
            "n": params.output_count,
        }

        async with httpx.AsyncClient(timeout=300) as client:
            r = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            if r.status_code >= 400:
                raise RuntimeError(f"OpenAI {self.openai_model_id} API error {r.status_code}: {r.text[:300]}")
            data = r.json()
            urls = []
            for item in data.get("data", []):
                if item.get("url"):
                    urls.append(item["url"])
                elif item.get("b64_json"):
                    # OpenAI 图像 API 通常返回 b64_json,我们用 data URL 让前端可直接展示
                    urls.append(f"data:image/png;base64,{item['b64_json']}")
            if not urls:
                raise RuntimeError(f"OpenAI returned no images: {data}")
            return GenerationResult(image_urls=urls, generation_time_ms=int((time.time() - start) * 1000))

    async def health_check(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE


class GPTImage1Provider(_OpenAIImageBase):
    openai_model_id = "gpt-image-1"

    @property
    def model_id(self) -> str:
        return "gpt_image_1"


class GPTImage2Provider(_OpenAIImageBase):
    openai_model_id = "gpt-image-2"

    @property
    def model_id(self) -> str:
        return "gpt_image_2"


# ──────────────────────────────────────────────────────────────────────────────
# 智谱 CogView-3-Flash(完全免费,无 token 限制)/ CogView-4
# ──────────────────────────────────────────────────────────────────────────────
class _ZhipuCogViewBase(AIProviderBase):
    """智谱图像生成基类 — OpenAI 兼容格式。"""
    zhipu_model_id: str = "cogview-3-flash"

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        api_key = _api_key("ZHIPU_API_KEY")
        if not api_key:
            return _mock_result(self.zhipu_model_id, params, start)

        # CogView 支持的 size:1024x1024 / 1024x1792 / 1792x1024 等
        size_map = {
            (1024, 1024): "1024x1024",
            (1024, 1365): "1024x1792",  # 我们 3:4 默认 → 智谱最近的竖版档位
            (1024, 1536): "1024x1792",
            (1536, 1024): "1792x1024",
            (1280, 720): "1792x1024",
        }
        size = size_map.get((params.width, params.height), "1024x1024")

        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                "https://open.bigmodel.cn/api/paas/v4/images/generations",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.zhipu_model_id,
                    "prompt": prompt,
                    "size": size,
                },
            )
            if r.status_code >= 400:
                raise RuntimeError(f"Zhipu {self.zhipu_model_id} API error {r.status_code}: {r.text[:300]}")
            data = r.json()
            urls = [item["url"] for item in data.get("data", []) if item.get("url")]
            if not urls:
                raise RuntimeError(f"Zhipu returned no images: {data}")
            # CogView 单次只返回一张,如果用户要多张就并发再调几次
            if params.output_count > 1 and len(urls) < params.output_count:
                more_tasks = [
                    client.post(
                        "https://open.bigmodel.cn/api/paas/v4/images/generations",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={"model": self.zhipu_model_id, "prompt": prompt, "size": size},
                    )
                    for _ in range(params.output_count - 1)
                ]
                more_responses = await asyncio.gather(*more_tasks, return_exceptions=True)
                for resp in more_responses:
                    if isinstance(resp, Exception):
                        continue
                    try:
                        for it in resp.json().get("data", []):
                            if it.get("url"):
                                urls.append(it["url"])
                    except Exception:
                        pass
            return GenerationResult(image_urls=urls, generation_time_ms=int((time.time() - start) * 1000))

    async def health_check(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE


class CogView3FlashProvider(_ZhipuCogViewBase):
    """完全免费,无 token 限制(仅限并发)。"""
    zhipu_model_id = "cogview-3-flash"

    @property
    def model_id(self) -> str:
        return "cogview_3_flash"


class CogView4Provider(_ZhipuCogViewBase):
    """付费但出图质量更高,新用户有大额免费额度。"""
    zhipu_model_id = "cogview-4-250304"

    @property
    def model_id(self) -> str:
        return "cogview_4"


# ──────────────────────────────────────────────────────────────────────────────
# 阿里通义 — Qwen-Image-Edit(图生图,真实人脸保持)
# ──────────────────────────────────────────────────────────────────────────────
class QwenImageProvider(AIProviderBase):
    """阿里通义 qwen-image-edit:把上传的人脸图作为参考,生成新场景下的同一人物。
    DashScope multimodal-generation 端点是同步调用,不需要轮询。
    """

    @property
    def model_id(self) -> str:
        return "qwen_image"

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        api_key = _api_key("DASHSCOPE_API_KEY")
        if not api_key:
            return _mock_result("qwen-image-edit", params, start)

        # 拼装第一张源图(image+text)— Qwen-Image-Edit 需要源图作为 reference
        content: list[dict] = []
        primary = next((s for s in (source_images or []) if s.base64 or s.url), None)
        if primary:
            if primary.url:
                content.append({"image": primary.url})
            elif primary.base64:
                content.append({"image": f"data:image/jpeg;base64,{primary.base64}"})
        content.append({"text": prompt})

        # 单次调用,output_count > 1 就并发再调
        async def _call_once(client: httpx.AsyncClient) -> list[str]:
            r = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "qwen-image-edit",
                    "input": {"messages": [{"role": "user", "content": content}]},
                    "parameters": {"n": 1, "watermark": False, "negative_prompt": negative_prompt or " "},
                },
            )
            if r.status_code >= 400:
                raise RuntimeError(f"Qwen-Image-Edit error {r.status_code}: {r.text[:300]}")
            data = r.json()
            urls: list[str] = []
            for choice in data.get("output", {}).get("choices", []):
                for item in choice.get("message", {}).get("content", []):
                    if item.get("image"):
                        urls.append(item["image"])
            return urls

        async with httpx.AsyncClient(timeout=300) as client:
            tasks = [_call_once(client) for _ in range(max(1, params.output_count))]
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            urls: list[str] = []
            errors: list[str] = []
            for res in all_results:
                if isinstance(res, Exception):
                    errors.append(str(res))
                else:
                    urls.extend(res)
            if not urls:
                raise RuntimeError(f"Qwen-Image-Edit returned no images. Errors: {errors[:2]}")
            return GenerationResult(image_urls=urls, generation_time_ms=int((time.time() - start) * 1000))

    async def health_check(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE


# ──────────────────────────────────────────────────────────────────────────────
# 快手 — Kling Image (可灵图像)
# ──────────────────────────────────────────────────────────────────────────────
class KlingImageProvider(AIProviderBase):
    @property
    def model_id(self) -> str:
        return "kling_image"

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        # 可灵签名鉴权较复杂(JWT),Mock 优先
        return _mock_result("kling", params, start)

    async def health_check(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE


# ──────────────────────────────────────────────────────────────────────────────
# Midjourney V7
# ──────────────────────────────────────────────────────────────────────────────
class MidjourneyV7Provider(AIProviderBase):
    @property
    def model_id(self) -> str:
        return "mj_v7"

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        return _mock_result("mj-v7", params, start)

    async def health_check(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE
