import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Sparkles, ArrowRight, Upload, Palette, Download, Star, Zap, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { sceneApi } from '@/services/api'

export function HomePage() {
  const navigate = useNavigate()
  const { data } = useQuery({
    queryKey: ['scenes-home'],
    queryFn: () => sceneApi.list({ pageSize: 8 }),
  })

  const hotScenes = data?.items ?? []

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-pink-50 via-white to-purple-50 py-20 md:py-32">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmOWE4ZDQiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzRjMC0yLjIgMS44LTQgNC00czQgMS44IDQgNC0xLjggNC00IDQtNC0xLjgtNC00em0wLTMwYzAtMi4yIDEuOC00IDQtNHM0IDEuOCA0IDQtMS44IDQtNCA0LTQtMS44LTQtNHptLTMwIDBjMC0yLjIgMS44LTQgNC00czQgMS44IDQgNC0xLjggNC00IDQtNC0xLjgtNC00eiIvPjwvZz48L2c+PC9zdmc+')] opacity-50" />
        <div className="container mx-auto px-4 text-center relative z-10">
          <Badge variant="secondary" className="mb-6 text-sm px-4 py-1.5">
            <Zap className="h-3.5 w-3.5 mr-1.5 text-yellow-500" />
            AI 驱动 · 5分钟出图 · 专业级画质
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
            AI 一键生成
            <span className="block bg-gradient-to-r from-primary via-pink-500 to-purple-600 bg-clip-text text-transparent mt-2">
              专属婚纱艺术照
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            上传个人照片，选择梦想场景，AI 为你生成摄影级婚纱照与艺术写真。
            <br className="hidden md:block" />
            无需专业摄影，媲美万元婚纱照效果。
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="xl" onClick={() => navigate('/generate')}>
              <Sparkles className="mr-2 h-5 w-5" />
              立即免费体验
            </Button>
            <Button size="xl" variant="outline" onClick={() => document.getElementById('scenes')?.scrollIntoView({ behavior: 'smooth' })}>
              浏览场景库
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">注册即送 5 次免费生成额度，无需信用卡</p>
        </div>
      </section>

      {/* Steps */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">三步完成专属艺术照</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {[
              { icon: Upload, step: '01', title: '上传照片', desc: '上传您的个人或双人照片，支持单人/情侣模式，AI 自动检测人脸质量' },
              { icon: Palette, step: '02', title: '选择场景', desc: '从 50+ 精美场景中选择，婚纱、古风、油画、写真任意切换，支持多种 AI 模型' },
              { icon: Download, step: '03', title: '下载结果', desc: '5 分钟内生成高清艺术照，支持 1080P / 4K 输出，一键下载分享至社交媒体' },
            ].map(({ icon: Icon, step, title, desc }) => (
              <div key={step} className="text-center">
                <div className="relative mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                  <Icon className="h-7 w-7 text-primary" />
                  <div className="absolute -top-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-[11px] font-bold text-white">
                    {step}
                  </div>
                </div>
                <h3 className="text-lg font-semibold mb-2">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Hot Scenes */}
      <section id="scenes" className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold">热门场景</h2>
            <Button variant="ghost" onClick={() => navigate('/generate')}>
              查看全部 <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {hotScenes.length > 0
              ? hotScenes.map((scene) => (
                  <button
                    key={scene.id}
                    onClick={() => navigate('/generate')}
                    className="group overflow-hidden rounded-xl border bg-white shadow-sm hover:shadow-md transition-all text-left"
                  >
                    <div className="aspect-[3/4] overflow-hidden bg-muted">
                      {scene.thumbnailUrl ? (
                        <img src={scene.thumbnailUrl} alt={scene.name} className="h-full w-full object-cover transition-transform group-hover:scale-105" />
                      ) : (
                        <div className="h-full w-full flex items-center justify-center bg-gradient-to-br from-pink-100 to-purple-100">
                          <Sparkles className="h-8 w-8 text-primary/50" />
                        </div>
                      )}
                    </div>
                    <div className="p-3">
                      <p className="font-medium text-sm">{scene.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{scene.description}</p>
                    </div>
                  </button>
                ))
              : Array.from({ length: 8 }, (_, i) => (
                  <div key={i} className="overflow-hidden rounded-xl border bg-white shadow-sm">
                    <div className="aspect-[3/4] shimmer" />
                    <div className="p-3 space-y-2">
                      <div className="h-4 w-3/4 shimmer rounded" />
                      <div className="h-3 w-1/2 shimmer rounded" />
                    </div>
                  </div>
                ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-4">简单透明的定价</h2>
          <p className="text-center text-muted-foreground mb-12">注册即送 5 次免费额度，随时升级</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {[
              {
                name: '免费版', price: '¥0', period: '永久免费',
                features: ['每月 5 次生成', '720P 输出', '基础场景库', '30天历史保留'],
                cta: '立即注册', popular: false,
              },
              {
                name: '标准版', price: '¥29', period: '/月',
                features: ['每月 50 次生成', '1080P 输出', '全部场景库', '优先生成队列', '永久历史保留', '无水印下载'],
                cta: '升级标准版', popular: true,
              },
              {
                name: '专业版', price: '¥99', period: '/月',
                features: ['无限次生成', '4K 超清输出', '全部场景 + 新场景优先', '专属 GPU 优先', '批量生成', 'API 接入'],
                cta: '升级专业版', popular: false,
              },
            ].map((plan) => (
              <Card key={plan.name} className={plan.popular ? 'border-primary ring-2 ring-primary/20 relative' : ''}>
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="px-4 py-1">最受欢迎</Badge>
                  </div>
                )}
                <CardContent className="p-6">
                  <h3 className="font-bold text-lg">{plan.name}</h3>
                  <div className="mt-2 mb-4">
                    <span className="text-3xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground">{plan.period}</span>
                  </div>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-center gap-2 text-sm">
                        <Star className="h-4 w-4 text-primary shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Button
                    className="w-full"
                    variant={plan.popular ? 'default' : 'outline'}
                    onClick={() => navigate('/auth/register')}
                  >
                    {plan.cta}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Trust */}
      <section className="py-12 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto text-center">
            {[
              { icon: Shield, title: '隐私保护', desc: '原始照片 30 天后自动删除，绝不用于模型训练' },
              { icon: Zap, title: '极速出图', desc: '平均 3 分钟内完成，高峰期不超过 10 分钟' },
              { icon: Star, title: '专业质量', desc: '基于 Flux/SDXL 顶级模型，媲美专业摄影棚效果' },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="flex flex-col items-center gap-3">
                <div className="rounded-full bg-primary/10 p-3">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold">{title}</h3>
                <p className="text-sm text-muted-foreground">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 text-center text-sm text-muted-foreground">
        <p>© 2026 AI 艺术照 · 让每个人都能拥有专属艺术照</p>
      </footer>
    </div>
  )
}
