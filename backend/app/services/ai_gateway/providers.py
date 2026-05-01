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
# 字节豆包 — Seedream 4.0 / 4.5(文生图为主,可传 image 参数做图生图)
# 火山方舟 ARK API,OpenAI 兼容格式
# ──────────────────────────────────────────────────────────────────────────────
class _ArkImageBase(AIProviderBase):
    """字节豆包图像模型基类(火山方舟 ARK)。子类只需定义 ark_model_id。"""
    ark_model_id: str = "doubao-seedream-4-0-250828"

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        api_key = _api_key("ARK_API_KEY")
        if not api_key:
            return _mock_result(self.ark_model_id, params, start)

        # 拼装 reference image:支持 URL 或 base64 → data URL
        primary = next((s for s in (source_images or []) if s.base64 or s.url), None)
        ref_image = None
        if primary:
            ref_image = primary.url or f"data:image/jpeg;base64,{primary.base64}" if primary.base64 else None

        # ARK 支持的 size:1024x1024 / 2K(2048) / 4K 等档位
        size = f"{params.width}x{params.height}"
        if params.width == params.height == 1024:
            size = "1024x1024"
        elif max(params.width, params.height) >= 2048:
            size = "2K"

        body: dict = {
            "model": self.ark_model_id,
            "prompt": prompt,
            "size": size,
            "response_format": "url",
            "watermark": False,
        }
        # 图生图:ARK 用 image(单图)字段
        if ref_image:
            body["image"] = ref_image

        async def _call_once(client: httpx.AsyncClient) -> list[str]:
            r = await client.post(
                "https://ark.cn-beijing.volces.com/api/v3/images/generations",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=body,
            )
            if r.status_code >= 400:
                raise RuntimeError(f"ARK {self.ark_model_id} API {r.status_code}: {r.text[:300]}")
            data = r.json()
            return [item["url"] for item in data.get("data", []) if item.get("url")]

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
                raise RuntimeError(f"ARK {self.ark_model_id} returned no images. Errors: {errors[:2]}")
            return GenerationResult(image_urls=urls, generation_time_ms=int((time.time() - start) * 1000))

    async def health_check(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE


class SeedreamProvider(_ArkImageBase):
    """Seedream 4.0 — 字节文生图旗舰,中文场景理解强"""
    ark_model_id = "doubao-seedream-4-0-250828"

    @property
    def model_id(self) -> str:
        return "seedream_4"


class SeedEditProvider(_ArkImageBase):
    """SeedEdit 3.0 — 字节图像编辑专用,主体保留 + 局部编辑"""
    ark_model_id = "doubao-seededit-3-0-i2i-250628"

    @property
    def model_id(self) -> str:
        return "seededit_3"


# ──────────────────────────────────────────────────────────────────────────────
# Black Forest Labs — Flux Kontext Pro (img2img / 人脸保持编辑)
# Replicate 端点:同步等待用 Prefer:wait;异步则需轮询 prediction_id
# ──────────────────────────────────────────────────────────────────────────────
class FluxKontextProvider(AIProviderBase):
    @property
    def model_id(self) -> str:
        return "flux_kontext"

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        api_key = _api_key("REPLICATE_API_TOKEN")
        if not api_key:
            return _mock_result("flux-kontext", params, start)

        # 支持 URL 与 base64 两种源图(worker 现在统一传 base64)
        primary = next((s for s in (source_images or []) if s.base64 or s.url), None)
        input_image_field = None
        if primary:
            if primary.url:
                input_image_field = primary.url
            elif primary.base64:
                # Replicate 接受 data URL
                input_image_field = f"data:image/jpeg;base64,{primary.base64}"

        # 算 Flux 支持的 aspect ratio(img2img 时可以 match_input_image)
        if input_image_field:
            aspect = "match_input_image"
        else:
            ratio = params.width / params.height if params.height else 1
            aspect = "1:1"
            for label, val in [("1:1", 1), ("3:4", 0.75), ("4:3", 1.33), ("9:16", 0.5625), ("16:9", 1.78), ("2:3", 0.667), ("3:2", 1.5)]:
                if abs(ratio - val) < abs(ratio - {"1:1": 1, "3:4": 0.75, "4:3": 1.33, "9:16": 0.5625, "16:9": 1.78, "2:3": 0.667, "3:2": 1.5}[aspect]):
                    aspect = label

        input_data: dict = {
            "prompt": prompt,
            "aspect_ratio": aspect,
            "output_format": "jpg",
            "safety_tolerance": 2,
        }
        if input_image_field:
            input_data["input_image"] = input_image_field

        # 多张输出 — Flux Kontext 单次只回 1 张,要多张就并发调用
        async def _call_once(client: httpx.AsyncClient) -> list[str]:
            r = await client.post(
                "https://api.replicate.com/v1/models/black-forest-labs/flux-kontext-pro/predictions",
                json={"input": input_data},
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Prefer": "wait=60",  # 同步最多等 60s,超时后转异步轮询
                },
            )
            if r.status_code not in (200, 201):
                raise RuntimeError(f"Flux Kontext API {r.status_code}: {r.text[:300]}")
            data = r.json()

            # 已直接返回 succeeded
            if data.get("status") == "succeeded":
                output = data.get("output")
                return output if isinstance(output, list) else ([output] if output else [])

            # 否则轮询 prediction_id 直到 completed
            prediction_id = data.get("id")
            if not prediction_id:
                raise RuntimeError(f"Flux Kontext: no prediction id in {data}")
            for _ in range(60):  # 最多再等 5 分钟
                await asyncio.sleep(5)
                poll = await client.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                pdata = poll.json()
                if pdata.get("status") == "succeeded":
                    output = pdata.get("output")
                    return output if isinstance(output, list) else ([output] if output else [])
                if pdata.get("status") in ("failed", "canceled"):
                    raise RuntimeError(f"Flux Kontext failed: {pdata.get('error')}")
            raise RuntimeError("Flux Kontext polling timed out")

        async with httpx.AsyncClient(timeout=600) as client:
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
                raise RuntimeError(f"Flux Kontext returned no images. Errors: {errors[:2]}")
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
# 快手 — Kling Image v1.5(可灵图像)— JWT 鉴权 + 异步任务
# ──────────────────────────────────────────────────────────────────────────────
class KlingImageProvider(AIProviderBase):
    @property
    def model_id(self) -> str:
        return "kling_image"

    @staticmethod
    def _make_jwt(access_key: str, secret_key: str) -> str:
        """可灵 API 用 JWT 鉴权:HS256 签名,exp 30 分钟,nbf -5 秒。"""
        import jwt as _jwt  # PyJWT
        import time as _t
        payload = {
            "iss": access_key,
            "exp": int(_t.time()) + 1800,
            "nbf": int(_t.time()) - 5,
        }
        return _jwt.encode(payload, secret_key, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"})

    async def generate(self, source_images, prompt, negative_prompt, params):
        start = time.time()
        ak = _api_key("KLING_ACCESS_KEY")
        sk = _api_key("KLING_SECRET_KEY")
        if not ak or not sk:
            return _mock_result("kling", params, start)

        try:
            token = self._make_jwt(ak, sk)
        except Exception as e:
            raise RuntimeError(f"Kling JWT 生成失败(检查 PyJWT 是否安装): {e}")

        primary = next((s for s in (source_images or []) if s.base64 or s.url), None)

        body: dict = {
            "model_name": "kling-v1-5",
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "aspect_ratio": "3:4",
            "n": 1,  # 单次 1 张,多张并发
        }
        # 计算 aspect_ratio
        ratio = params.width / params.height if params.height else 1
        for label, val in [("1:1", 1), ("16:9", 1.78), ("9:16", 0.5625), ("4:3", 1.33), ("3:4", 0.75), ("3:2", 1.5), ("2:3", 0.667)]:
            if abs(ratio - val) < abs(ratio - {"1:1": 1, "16:9": 1.78, "9:16": 0.5625, "4:3": 1.33, "3:4": 0.75, "3:2": 1.5, "2:3": 0.667}[body["aspect_ratio"]]):
                body["aspect_ratio"] = label

        if primary:
            if primary.url:
                body["image"] = primary.url
            elif primary.base64:
                body["image"] = primary.base64  # 可灵接受裸 base64
            # 关键:可灵 v1.5 要求带 image 时必须指定 reference 用途
            # "face" = 人脸保留(我们的婚纱艺术照场景),"subject" = 主体保留
            body["image_reference"] = "face"
            body["image_fidelity"] = 0.5  # 0~1,越大越像原图(人脸保留度)

        async def _call_once(client: httpx.AsyncClient) -> list[str]:
            # 1. 提交任务
            r = await client.post(
                "https://api-beijing.klingai.com/v1/images/generations",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=body,
            )
            if r.status_code >= 400:
                raise RuntimeError(f"Kling submit error {r.status_code}: {r.text[:300]}")
            data = r.json()
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                raise RuntimeError(f"Kling: no task_id in {data}")

            # 2. 轮询任务结果
            for _ in range(60):  # 最多 5 分钟
                await asyncio.sleep(5)
                poll = await client.get(
                    f"https://api-beijing.klingai.com/v1/images/generations/{task_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                pdata = poll.json().get("data", {})
                status = pdata.get("task_status", "")
                if status == "succeed":
                    images = pdata.get("task_result", {}).get("images", [])
                    return [img["url"] for img in images if img.get("url")]
                if status == "failed":
                    raise RuntimeError(f"Kling task failed: {pdata.get('task_status_msg')}")
            raise RuntimeError("Kling polling timed out")

        async with httpx.AsyncClient(timeout=600) as client:
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
                raise RuntimeError(f"Kling returned no images. Errors: {errors[:2]}")
            return GenerationResult(image_urls=urls, generation_time_ms=int((time.time() - start) * 1000))

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
