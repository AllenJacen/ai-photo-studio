import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Sparkles, ChevronRight, Users, User, Settings2, Coins, Info,
  Zap, Clock, CheckCircle2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Slider } from '@/components/ui/slider'
import { Badge } from '@/components/ui/badge'
import { ImageUploader } from '@/components/upload/ImageUploader'
import { ScenePicker } from '@/components/scene/ScenePicker'
import { useGenerateStore } from '@/stores/generateStore'
import { useAuthStore } from '@/stores/authStore'
import { modelApi, taskApi } from '@/services/api'
import { cn, formatDuration } from '@/lib/utils'
import type { AIModel } from '@/types'

const ASPECT_RATIOS = [
  { value: '1:1' as const, label: '1:1' },
  { value: '4:3' as const, label: '4:3' },
  { value: '3:4' as const, label: '3:4', recommended: true },
  { value: '16:9' as const, label: '16:9' },
]

const OUTPUT_COUNTS = [1, 2, 4] as const
const QUALITY_OPTIONS = [
  { value: 'standard' as const, label: '标准', desc: '720P', free: true },
  { value: 'hd' as const, label: '高清', desc: '1080P', free: false },
  { value: 'uhd' as const, label: '超清', desc: '4K', free: false },
]

export function GeneratePage() {
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuthStore()
  const {
    selectedScene, selectedModel, inputImages, params,
    setScene, setModel, addImage, removeImage, updateParams,
  } = useGenerateStore()

  const [personMode, setPersonMode] = useState<'single' | 'couple'>('single')
  const [showScenePicker, setShowScenePicker] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const { data: models } = useQuery({
    queryKey: ['ai-models'],
    queryFn: modelApi.list,
  })

  const creditsNeeded = (selectedScene?.creditCost ?? 1) *
    (selectedModel?.creditMultiplier ?? 1) * params.outputCount

  const canSubmit =
    isAuthenticated &&
    selectedScene != null &&
    selectedModel != null &&
    inputImages.length >= (personMode === 'couple' ? 2 : 1)

  const handleSubmit = async () => {
    if (!canSubmit || !selectedScene || !selectedModel) return
    setSubmitting(true)
    try {
      const result = await taskApi.create({
        sceneId: selectedScene.id,
        aiModel: selectedModel.id,
        inputImages: inputImages.map((img) => ({
          storageKey: img.storageKey,
          role: img.role,
        })),
        params,
      })
      navigate(`/progress/${result.taskId}`)
    } catch {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">创作艺术照</h1>
          <p className="text-muted-foreground mt-1">上传照片，选择场景，AI 为你生成专属艺术照</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: Config Panel */}
          <div className="lg:col-span-2 space-y-5">
            {/* Step 1: Upload */}
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-white text-xs font-bold">1</div>
                  <h3 className="font-semibold">上传照片</h3>
                </div>
                <Tabs value={personMode} onValueChange={(v) => setPersonMode(v as 'single' | 'couple')}>
                  <TabsList className="w-full mb-4">
                    <TabsTrigger value="single" className="flex-1">
                      <User className="h-3.5 w-3.5 mr-1.5" /> 单人
                    </TabsTrigger>
                    <TabsTrigger value="couple" className="flex-1">
                      <Users className="h-3.5 w-3.5 mr-1.5" /> 情侣/双人
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="single">
                    <ImageUploader
                      role="single"
                      label="上传个人照片"
                      value={inputImages.find((i) => i.role === 'single')}
                      onChange={addImage}
                      onRemove={() => removeImage(inputImages.find((i) => i.role === 'single')?.storageKey ?? '')}
                    />
                  </TabsContent>
                  <TabsContent value="couple">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-muted-foreground mb-2 font-medium">人物 1</p>
                        <ImageUploader
                          role="person1"
                          label="上传照片 1"
                          value={inputImages.find((i) => i.role === 'person1')}
                          onChange={addImage}
                          onRemove={() => removeImage(inputImages.find((i) => i.role === 'person1')?.storageKey ?? '')}
                        />
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-2 font-medium">人物 2</p>
                        <ImageUploader
                          role="person2"
                          label="上传照片 2"
                          value={inputImages.find((i) => i.role === 'person2')}
                          onChange={addImage}
                          onRemove={() => removeImage(inputImages.find((i) => i.role === 'person2')?.storageKey ?? '')}
                        />
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Step 2: Scene */}
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-white text-xs font-bold">2</div>
                  <h3 className="font-semibold">选择场景</h3>
                </div>
                {selectedScene ? (
                  <button
                    onClick={() => setShowScenePicker(true)}
                    className="w-full flex items-center gap-3 rounded-xl border p-3 hover:border-primary/50 transition-colors text-left"
                  >
                    <div className="h-16 w-12 flex-shrink-0 overflow-hidden rounded-lg bg-muted">
                      {selectedScene.thumbnailUrl ? (
                        <img src={selectedScene.thumbnailUrl} alt={selectedScene.name} className="h-full w-full object-cover" />
                      ) : (
                        <div className="h-full w-full flex items-center justify-center">
                          <Sparkles className="h-5 w-5 text-muted-foreground/40" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{selectedScene.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{selectedScene.description}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                  </button>
                ) : (
                  <button
                    onClick={() => setShowScenePicker(true)}
                    className="w-full flex items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border py-6 text-sm text-muted-foreground hover:border-primary/50 hover:text-foreground transition-colors"
                  >
                    <Sparkles className="h-4 w-4" />
                    点击选择场景
                  </button>
                )}
              </CardContent>
            </Card>

            {/* Step 3: Model */}
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-white text-xs font-bold">3</div>
                  <h3 className="font-semibold">选择 AI 引擎</h3>
                </div>
                <div className="space-y-2">
                  {models ? (() => {
                    // 按 live > limited > mock 排序,内部按 creditMultiplier 升序
                    const rank = (id: string) => ({live: 0, limited: 1, mock: 2}[
                      MODEL_LIVE_STATUS[id]?.status ?? 'mock'
                    ])
                    const sorted = [...models].sort((a, b) => {
                      const r = rank(a.id) - rank(b.id)
                      return r !== 0 ? r : a.creditMultiplier - b.creditMultiplier
                    })
                    return sorted.map((model) => (
                      <ModelCard
                        key={model.id}
                        model={model}
                        selected={selectedModel?.id === model.id}
                        onSelect={() => setModel(model)}
                      />
                    ))
                  })() : (
                    <div className="space-y-2">
                      {Array.from({ length: 3 }, (_, i) => (
                        <div key={i} className="h-16 rounded-xl shimmer" />
                      ))}
                    </div>
                  )}
                </div>
                {/* 模型状态图例 */}
                <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-500" /> 已接通真实 API
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-500" /> 受限(Key 限额/未开通)
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-gray-400" /> Mock 占位
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Step 4: Params */}
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-white text-xs font-bold">4</div>
                  <h3 className="font-semibold">生成参数</h3>
                </div>

                {/* Aspect Ratio */}
                <div className="mb-4">
                  <p className="text-sm font-medium mb-2">画面比例</p>
                  <div className="flex gap-2">
                    {ASPECT_RATIOS.map((r) => (
                      <button
                        key={r.value}
                        onClick={() => updateParams({ aspectRatio: r.value })}
                        className={cn(
                          'flex-1 rounded-lg border py-2 text-xs font-medium transition-colors relative',
                          params.aspectRatio === r.value
                            ? 'border-primary bg-primary/5 text-primary'
                            : 'hover:border-primary/40',
                        )}
                      >
                        {r.label}
                        {r.recommended && (
                          <span className="absolute -top-1.5 -right-1 text-[9px] bg-green-500 text-white px-1 rounded-full">推荐</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Output Count */}
                <div className="mb-4">
                  <p className="text-sm font-medium mb-2">生成数量</p>
                  <div className="flex gap-2">
                    {OUTPUT_COUNTS.map((n) => (
                      <button
                        key={n}
                        onClick={() => updateParams({ outputCount: n })}
                        className={cn(
                          'flex-1 rounded-lg border py-2 text-sm font-medium transition-colors',
                          params.outputCount === n
                            ? 'border-primary bg-primary/5 text-primary'
                            : 'hover:border-primary/40',
                        )}
                      >
                        {n} 张
                      </button>
                    ))}
                  </div>
                </div>

                {/* Quality */}
                <div className="mb-4">
                  <p className="text-sm font-medium mb-2">输出画质</p>
                  <div className="flex gap-2">
                    {QUALITY_OPTIONS.map((q) => (
                      <button
                        key={q.value}
                        onClick={() => updateParams({ quality: q.value })}
                        className={cn(
                          'flex-1 rounded-lg border py-2 text-xs font-medium transition-colors',
                          params.quality === q.value
                            ? 'border-primary bg-primary/5 text-primary'
                            : 'hover:border-primary/40',
                          !q.free && user?.membershipType === 'free' && 'opacity-50',
                        )}
                      >
                        <div>{q.label}</div>
                        <div className="text-muted-foreground">{q.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Style Strength */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium">风格强度</p>
                    <span className="text-sm text-muted-foreground">{params.styleStrength}</span>
                  </div>
                  <Slider
                    min={1} max={10} step={1}
                    value={[params.styleStrength]}
                    onValueChange={([v]) => updateParams({ styleStrength: v })}
                  />
                  <div className="flex justify-between mt-1 text-[10px] text-muted-foreground">
                    <span>更像本人</span>
                    <span>风格更强</span>
                  </div>
                </div>

                {/* Advanced */}
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  <Settings2 className="h-3.5 w-3.5" />
                  高级选项
                  <ChevronRight className={cn('h-3.5 w-3.5 transition-transform', showAdvanced && 'rotate-90')} />
                </button>
                {showAdvanced && (
                  <div className="mt-3 space-y-3">
                    <textarea
                      placeholder="自定义正向提示词（可选）"
                      className="w-full rounded-lg border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                      rows={2}
                      value={params.customPrompt ?? ''}
                      onChange={(e) => updateParams({ customPrompt: e.target.value })}
                    />
                    <textarea
                      placeholder="自定义负向提示词（可选）"
                      className="w-full rounded-lg border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                      rows={2}
                      value={params.customNegativePrompt ?? ''}
                      onChange={(e) => updateParams({ customNegativePrompt: e.target.value })}
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Submit */}
            <div className="sticky bottom-4">
              <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-purple-50">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-1.5 text-sm">
                      <Coins className="h-4 w-4 text-yellow-500" />
                      <span>消耗 <span className="font-bold text-foreground">{creditsNeeded}</span> 积分</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                      <Coins className="h-3.5 w-3.5" />
                      <span>余额 {user?.credits ?? 0}</span>
                    </div>
                  </div>
                  {!isAuthenticated ? (
                    <Button className="w-full" size="lg" onClick={() => navigate('/auth/login')}>
                      登录后开始生成
                    </Button>
                  ) : (
                    <Button
                      className="w-full"
                      size="lg"
                      disabled={!canSubmit}
                      loading={submitting}
                      onClick={handleSubmit}
                    >
                      <Sparkles className="mr-2 h-5 w-5" />
                      开始生成
                    </Button>
                  )}
                  {!canSubmit && isAuthenticated && (
                    <p className="text-center text-xs text-muted-foreground mt-2 flex items-center justify-center gap-1">
                      <Info className="h-3 w-3" />
                      请完成：{!inputImages.length ? '上传照片' : !selectedScene ? '选择场景' : '选择 AI 引擎'}
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Right: Preview */}
          <div className="lg:col-span-3">
            {selectedScene ? (
              <div className="space-y-4">
                <Card>
                  <CardContent className="p-5">
                    <h3 className="font-semibold mb-3">场景预览</h3>
                    <div className="grid grid-cols-2 gap-3">
                      {selectedScene.previewUrls.length > 0
                        ? selectedScene.previewUrls.slice(0, 4).map((url, i) => (
                            <div key={i} className="aspect-[3/4] overflow-hidden rounded-xl bg-muted">
                              <img src={url} alt={`预览 ${i + 1}`} className="h-full w-full object-cover" />
                            </div>
                          ))
                        : Array.from({ length: 4 }, (_, i) => (
                            <div key={i} className="aspect-[3/4] overflow-hidden rounded-xl bg-gradient-to-br from-pink-100 to-purple-100 flex items-center justify-center">
                              <Sparkles className="h-10 w-10 text-primary/30" />
                            </div>
                          ))}
                    </div>
                    <div className="mt-4 space-y-1">
                      <h4 className="font-medium">{selectedScene.name}</h4>
                      <p className="text-sm text-muted-foreground">{selectedScene.description}</p>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {selectedScene.tags.map((tag) => (
                          <Badge key={tag} variant="secondary">{tag}</Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-5">
                    <h3 className="font-semibold mb-3">生成预估</h3>
                    <div className="space-y-2">
                      {[
                        { icon: Clock, label: '预计等待', value: selectedModel ? formatDuration(selectedModel.avgGenerationTimeS * params.outputCount) : '选择引擎后显示' },
                        { icon: Coins, label: '消耗积分', value: `${creditsNeeded} 积分` },
                        { icon: Zap, label: '输出规格', value: params.quality === 'standard' ? '720P' : params.quality === 'hd' ? '1080P' : '4K' },
                        { icon: CheckCircle2, label: '生成数量', value: `${params.outputCount} 张` },
                      ].map(({ icon: Icon, label, value }) => (
                        <div key={label} className="flex items-center justify-between text-sm py-1">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Icon className="h-4 w-4" /> {label}
                          </div>
                          <span className="font-medium">{value}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="flex h-full min-h-[400px] flex-col items-center justify-center rounded-2xl border-2 border-dashed text-center p-8">
                <Sparkles className="h-16 w-16 text-muted-foreground/20 mb-4 animate-float" />
                <h3 className="text-lg font-medium mb-2">选择场景开始创作</h3>
                <p className="text-sm text-muted-foreground max-w-xs">
                  从 50+ 精美场景中选择您的风格，AI 将为您生成专属艺术照
                </p>
                <Button className="mt-6" onClick={() => setShowScenePicker(true)}>
                  <Sparkles className="mr-2 h-4 w-4" /> 浏览场景库
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      <ScenePicker
        open={showScenePicker}
        onClose={() => setShowScenePicker(false)}
        onSelect={setScene}
        selectedId={selectedScene?.id}
      />
    </div>
  )
}

const MODEL_ICON_EXT: Record<string, string> = {
  cogview_3_flash: 'png',
  cogview_4: 'png',
  nano_banana: 'png',
  seedream_4: 'png',
  seededit_3: 'png',
  flux_kontext: 'png',
  gpt_image_1: 'png',
  gpt_image_2: 'png',
  qwen_image: 'svg',
  kling_image: 'png',
  mj_v7: 'png',
}

// 模型当前真实接通状态(项目级已知,不需要后端动态算)
type ModelLiveStatus = 'live' | 'limited' | 'mock'
const MODEL_LIVE_STATUS: Record<string, { status: ModelLiveStatus; note?: string }> = {
  // 真实接通且质量好,推荐
  seedream_4:      { status: 'live', note: '中文 + 人脸保留首选' },
  flux_kontext:    { status: 'live', note: '写实质感天花板' },
  qwen_image:      { status: 'live', note: '图生图,人脸保留' },
  kling_image:     { status: 'limited', note: '账号余额不足' },
  // 受限
  seededit_3:      { status: 'limited', note: '账号未开通' },
  nano_banana:     { status: 'limited', note: '配额为 0' },
  gpt_image_1:     { status: 'limited', note: '账单上限' },
  gpt_image_2:     { status: 'limited', note: '账单上限' },
  // Mock
  mj_v7:           { status: 'mock' },
}

function ModelIcon({ modelId }: { modelId: string }) {
  const ext = MODEL_ICON_EXT[modelId] ?? 'png'
  const [errored, setErrored] = useState(false)
  if (errored) {
    return (
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary/10 to-purple-100">
        <Zap className="h-5 w-5 text-primary" />
      </div>
    )
  }
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white border border-border/60 overflow-hidden">
      <img
        src={`/model-icons/${modelId}.${ext}`}
        alt={modelId}
        className="h-7 w-7 object-contain"
        onError={() => setErrored(true)}
      />
    </div>
  )
}

function ModelCard({ model, selected, onSelect }: { model: AIModel; selected: boolean; onSelect: () => void }) {
  const live = MODEL_LIVE_STATUS[model.id] ?? { status: 'mock' as const }
  const isLive = live.status === 'live'
  const isLimited = live.status === 'limited'

  const badgeStyle = {
    live:    'bg-green-100 text-green-700 border-green-200',
    limited: 'bg-amber-100 text-amber-700 border-amber-200',
    mock:    'bg-gray-100 text-gray-500 border-gray-200',
  }[live.status]
  const badgeText = {
    live:    '推荐',
    limited: '受限',
    mock:    'Mock',
  }[live.status]

  return (
    <button
      onClick={onSelect}
      disabled={model.status === 'maintenance'}
      className={cn(
        'w-full flex items-center gap-3 rounded-xl border p-3 text-left transition-all',
        selected ? 'border-primary bg-primary/5' : 'hover:border-primary/40 hover:bg-muted/30',
        model.status === 'maintenance' && 'opacity-50 pointer-events-none',
      )}
      title={live.note ?? ''}
    >
      <ModelIcon modelId={model.id} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-sm font-medium">{model.displayName}</span>
          <span className={cn(
            'inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] rounded-md border',
            badgeStyle,
          )}>
            {isLive && <span className="h-1.5 w-1.5 rounded-full bg-green-500" />}
            {badgeText}
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-0.5 truncate">
          {isLimited && live.note ? <span className="text-amber-600">{live.note} · </span> : null}
          {isLive && live.note ? <span className="text-green-700">{live.note} · </span> : null}
          {model.description}
        </p>
      </div>
      <div className="shrink-0 text-right">
        <div className="text-xs font-medium text-primary">{model.creditMultiplier}x</div>
        <div className="text-[10px] text-muted-foreground">~{model.avgGenerationTimeS}s</div>
      </div>
      {selected && <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />}
    </button>
  )
}
