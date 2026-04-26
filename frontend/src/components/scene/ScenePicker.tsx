import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, X, Crown, Flame, Sparkles } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { sceneApi } from '@/services/api'
import type { Scene } from '@/types'
import { cn } from '@/lib/utils'

const CATEGORIES = [
  { id: '', name: '全部' },
  { id: 'wedding', name: '婚纱系列' },
  { id: 'portrait', name: '时尚写真' },
  { id: 'chinese_style', name: '中国风' },
  { id: 'artistic', name: '艺术风格' },
  { id: 'fantasy', name: '奇幻主题' },
  { id: 'professional', name: '商务证件' },
]

interface Props {
  open: boolean
  onClose: () => void
  onSelect: (scene: Scene) => void
  selectedId?: string
}

export function ScenePicker({ open, onClose, onSelect, selectedId }: Props) {
  const [category, setCategory] = useState('')
  const [keyword, setKeyword] = useState('')

  const { data } = useQuery({
    queryKey: ['scenes', category, keyword],
    queryFn: () => sceneApi.list({ category: category || undefined, keyword: keyword || undefined, pageSize: 50 }),
    enabled: open,
  })

  const scenes = data?.items ?? []

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-4xl max-h-[85vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <DialogTitle className="text-xl">选择场景</DialogTitle>
          <div className="flex gap-3 mt-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索场景..."
                className="pl-9"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
              />
            </div>
          </div>
          <div className="flex gap-2 mt-3 overflow-x-auto pb-1 scrollbar-hide">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setCategory(cat.id)}
                className={cn(
                  'whitespace-nowrap rounded-full px-3 py-1 text-sm font-medium transition-colors',
                  category === cat.id
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground',
                )}
              >
                {cat.name}
              </button>
            ))}
          </div>
        </DialogHeader>

        <div className="overflow-y-auto flex-1 p-6">
          {scenes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <Sparkles className="h-12 w-12 mb-3 opacity-30" />
              <p>暂无场景</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {scenes.map((scene) => (
                <SceneCard
                  key={scene.id}
                  scene={scene}
                  selected={scene.id === selectedId}
                  onSelect={() => { onSelect(scene); onClose() }}
                />
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

function SceneCard({ scene, selected, onSelect }: { scene: Scene; selected: boolean; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      className={cn(
        'group relative overflow-hidden rounded-xl border-2 text-left transition-all hover:shadow-md',
        selected ? 'border-primary ring-2 ring-primary/20' : 'border-transparent hover:border-primary/40',
      )}
    >
      <div className="aspect-[3/4] overflow-hidden bg-muted">
        {scene.thumbnailUrl ? (
          <img
            src={scene.thumbnailUrl}
            alt={scene.name}
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
          />
        ) : (
          <div className="h-full w-full flex items-center justify-center">
            <Sparkles className="h-8 w-8 text-muted-foreground/30" />
          </div>
        )}
      </div>
      <div className="p-2.5">
        <p className="text-sm font-medium line-clamp-1">{scene.name}</p>
        <div className="mt-1.5 flex flex-wrap gap-1">
          {scene.tags.includes('热门') && (
            <Badge variant="hot" className="text-[10px] px-1.5 py-0">
              <Flame className="h-2.5 w-2.5 mr-0.5" /> 热门
            </Badge>
          )}
          {scene.isPremium && (
            <Badge variant="premium" className="text-[10px] px-1.5 py-0">
              <Crown className="h-2.5 w-2.5 mr-0.5" /> 会员
            </Badge>
          )}
          {scene.tags.includes('新上线') && (
            <Badge variant="new" className="text-[10px] px-1.5 py-0">新</Badge>
          )}
        </div>
      </div>
      {selected && (
        <div className="absolute top-2 right-2 h-6 w-6 rounded-full bg-primary flex items-center justify-center">
          <X className="h-3 w-3 text-white rotate-45" />
        </div>
      )}
    </button>
  )
}
