import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Download, Heart, Share2, Star, RotateCcw, Archive,
  ChevronLeft, X, ZoomIn, ZoomOut
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { taskApi, imageApi } from '@/services/api'
import type { GenerationTask, GeneratedImage } from '@/types'
import { cn } from '@/lib/utils'

export function ResultPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [task, setTask] = useState<GenerationTask | null>(null)
  const [images, setImages] = useState<GeneratedImage[]>([])
  const [lightboxIdx, setLightboxIdx] = useState<number | null>(null)
  const [downloading, setDownloading] = useState<Set<string>>(new Set())
  const [rating, setRating] = useState<Record<string, number>>({})

  useEffect(() => {
    if (!taskId) return
    taskApi.get(taskId).then((t) => {
      setTask(t)
      setImages(t.resultImages ?? [])
    })
  }, [taskId])

  const handleDownload = async (image: GeneratedImage) => {
    if (downloading.has(image.id)) return
    setDownloading((s) => new Set(s).add(image.id))
    try {
      const { downloadUrl } = await imageApi.downloadUrl(image.id)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `ai-photo-${image.id}.jpg`
      a.click()
    } finally {
      setDownloading((s) => { const ns = new Set(s); ns.delete(image.id); return ns })
    }
  }

  const handleBatchDownload = async () => {
    if (!images.length) return
    const { zipUrl } = await imageApi.batchDownload(images.map((i) => i.id))
    window.open(zipUrl, '_blank')
  }

  const handleFavorite = async (image: GeneratedImage) => {
    const result = await imageApi.favorite(image.id)
    setImages((imgs) => imgs.map((i) => i.id === image.id ? { ...i, isFavorited: result.isFavorited } : i))
  }

  const handleRate = async (image: GeneratedImage, r: number) => {
    await imageApi.rate(image.id, r)
    setRating((prev) => ({ ...prev, [image.id]: r }))
  }

  const lightboxImage = lightboxIdx != null ? images[lightboxIdx] : null

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Button variant="ghost" size="sm" onClick={() => navigate('/history')}>
            <ChevronLeft className="mr-1 h-4 w-4" /> 返回历史
          </Button>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-green-600 bg-green-100">生成成功</Badge>
            {images.length > 0 && (
              <Button variant="outline" size="sm" onClick={handleBatchDownload}>
                <Archive className="mr-1.5 h-4 w-4" /> 打包下载
              </Button>
            )}
          </div>
        </div>

        {task && (
          <div className="mb-4">
            <h1 className="text-2xl font-bold">生成结果</h1>
            <p className="text-muted-foreground text-sm mt-1">
              {task.scene?.name} · {images.length} 张照片 · 使用 {task.aiModel}
            </p>
          </div>
        )}

        {/* Image Grid */}
        {images.length === 0 ? (
          <div className="flex h-64 items-center justify-center rounded-xl border-2 border-dashed">
            <p className="text-muted-foreground">正在加载结果...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {images.map((image, idx) => (
              <ImageCard
                key={image.id}
                image={image}
                userRating={rating[image.id]}
                downloading={downloading.has(image.id)}
                onDownload={() => handleDownload(image)}
                onFavorite={() => handleFavorite(image)}
                onRate={(r) => handleRate(image, r)}
                onExpand={() => setLightboxIdx(idx)}
              />
            ))}
          </div>
        )}

        {/* Actions */}
        <Card>
          <CardContent className="p-4 flex flex-wrap gap-3 justify-center sm:justify-between items-center">
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => navigate('/generate')}>
                <RotateCcw className="mr-1.5 h-4 w-4" /> 重新生成
              </Button>
              <Button variant="outline" onClick={() => navigate('/generate')}>
                调整参数重试
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              对效果满意？给个评分帮助我们改进 AI 模型
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Lightbox */}
      {lightboxImage && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
          onClick={() => setLightboxIdx(null)}
        >
          <button
            className="absolute top-4 right-4 text-white/70 hover:text-white"
            onClick={() => setLightboxIdx(null)}
          >
            <X className="h-8 w-8" />
          </button>
          {lightboxIdx! > 0 && (
            <button
              className="absolute left-4 text-white/70 hover:text-white p-2"
              onClick={(e) => { e.stopPropagation(); setLightboxIdx(lightboxIdx! - 1) }}
            >
              <ChevronLeft className="h-8 w-8" />
            </button>
          )}
          <img
            src={lightboxImage.originalUrl}
            alt="大图预览"
            className="max-h-[90vh] max-w-[90vw] object-contain rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />
          {lightboxIdx! < images.length - 1 && (
            <button
              className="absolute right-4 text-white/70 hover:text-white p-2"
              onClick={(e) => { e.stopPropagation(); setLightboxIdx(lightboxIdx! + 1) }}
            >
              <ZoomIn className="h-8 w-8" />
            </button>
          )}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1">
            {images.map((_, i) => (
              <button
                key={i}
                className={cn('h-1.5 rounded-full transition-all', i === lightboxIdx ? 'w-6 bg-white' : 'w-1.5 bg-white/40')}
                onClick={(e) => { e.stopPropagation(); setLightboxIdx(i) }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface ImageCardProps {
  image: GeneratedImage
  userRating?: number
  downloading: boolean
  onDownload: () => void
  onFavorite: () => void
  onRate: (r: number) => void
  onExpand: () => void
}

function ImageCard({ image, userRating, downloading, onDownload, onFavorite, onRate, onExpand }: ImageCardProps) {
  const [hovering, setHovering] = useState(false)
  const [hoverRating, setHoverRating] = useState(0)

  return (
    <div
      className="relative group overflow-hidden rounded-xl border bg-white shadow-sm"
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
    >
      <div className="aspect-[3/4] overflow-hidden bg-muted cursor-pointer" onClick={onExpand}>
        <img
          src={image.thumbnailUrl || image.originalUrl}
          alt="生成结果"
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
      </div>

      {/* Overlay actions */}
      {hovering && (
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent flex flex-col justify-between p-3">
          <div className="flex justify-end gap-1.5">
            <button
              onClick={onFavorite}
              className={cn(
                'rounded-full p-2 backdrop-blur-sm transition-colors',
                image.isFavorited
                  ? 'bg-red-500 text-white'
                  : 'bg-white/20 text-white hover:bg-white/40',
              )}
            >
              <Heart className={cn('h-4 w-4', image.isFavorited && 'fill-current')} />
            </button>
            <button
              onClick={onExpand}
              className="rounded-full bg-white/20 p-2 text-white hover:bg-white/40 backdrop-blur-sm transition-colors"
            >
              <ZoomOut className="h-4 w-4" />
            </button>
          </div>
          <div className="space-y-2">
            {/* Star Rating */}
            <div className="flex justify-center gap-1">
              {[1, 2, 3, 4, 5].map((s) => (
                <button
                  key={s}
                  onMouseEnter={() => setHoverRating(s)}
                  onMouseLeave={() => setHoverRating(0)}
                  onClick={() => onRate(s)}
                  className="text-yellow-400"
                >
                  <Star
                    className={cn('h-4 w-4', (hoverRating || userRating || 0) >= s ? 'fill-current' : '')}
                  />
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                className="flex-1 h-8 text-xs"
                loading={downloading}
                onClick={onDownload}
              >
                <Download className="mr-1 h-3.5 w-3.5" /> 下载
              </Button>
              <Button size="sm" variant="outline" className="h-8 px-3 bg-white/10 border-white/30 text-white hover:bg-white/20">
                <Share2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
