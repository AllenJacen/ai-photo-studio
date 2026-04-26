from __future__ import annotations
from app.services.ai_gateway.base import AIProviderBase, ProviderStatus
from app.services.ai_gateway.providers import (
    NanoBananaProvider,
    SeedreamProvider,
    FluxKontextProvider,
    GPTImage1Provider,
    GPTImage2Provider,
    QwenImageProvider,
    KlingImageProvider,
    MidjourneyV7Provider,
    CogView3FlashProvider,
    CogView4Provider,
)

_PROVIDERS: dict[str, AIProviderBase] = {
    "cogview_3_flash": CogView3FlashProvider(),
    "cogview_4": CogView4Provider(),
    "nano_banana": NanoBananaProvider(),
    "seedream_4": SeedreamProvider(),
    "flux_kontext": FluxKontextProvider(),
    "gpt_image_1": GPTImage1Provider(),
    "gpt_image_2": GPTImage2Provider(),
    "qwen_image": QwenImageProvider(),
    "kling_image": KlingImageProvider(),
    "mj_v7": MidjourneyV7Provider(),
}

FALLBACK_ORDER = ["cogview_3_flash", "nano_banana", "seedream_4", "flux_kontext", "gpt_image_2", "gpt_image_1"]


def get_provider(model_id: str) -> AIProviderBase:
    provider = _PROVIDERS.get(model_id)
    if not provider:
        raise ValueError(f"Unknown model: {model_id}")
    return provider


async def route_model(
    preferred_model: str,
    scene_recommended: str | None = None,
    scene_supported: list[str] | None = None,
) -> AIProviderBase:
    """路由到可用模型,按 preferred → 场景推荐 → 全局兜底顺序尝试。

    注意:用户明确选择的 preferred_model 拥有最高优先级,即使该模型不在场景的
    supported_models 列表里也会优先使用 — 用户的显式选择不应被场景预设静默覆盖。
    """
    candidates = [preferred_model]
    if scene_recommended and scene_recommended not in candidates:
        candidates.append(scene_recommended)
    for fallback in FALLBACK_ORDER:
        if fallback not in candidates:
            candidates.append(fallback)

    for idx, model_id in enumerate(candidates):
        if model_id not in _PROVIDERS:
            continue
        # 仅对 fallback 候选(idx > 0)应用 scene_supported 过滤
        # idx == 0 是用户明确指定的模型,无条件尊重
        if idx > 0 and scene_supported and model_id not in scene_supported:
            continue
        provider = _PROVIDERS[model_id]
        try:
            status = await provider.health_check()
            if status != ProviderStatus.MAINTENANCE:
                return provider
        except Exception:
            continue

    raise RuntimeError("所有 AI 模型当前不可用，请稍后重试")
