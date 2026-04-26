import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Clock, CheckCircle2, XCircle, Loader2, Eye, Trash2,
  ImageIcon, Filter, RefreshCw
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { historyApi } from '@/services/api'
import { formatDate, cn } from '@/lib/utils'
import type { GenerationTask, TaskStatus } from '@/types'

const STATUS_FILTERS: { value: TaskStatus | ''; label: string }[] = [
  { value: '', label: '全部' },
  { value: 'completed', label: '已完成' },
  { value: 'processing', label: '生成中' },
  { value: 'pending', label: '排队中' },
  { value: 'failed', label: '失败' },
]

const STATUS_CONFIG: Record<TaskStatus, { icon: typeof Clock; label: string; color: string }> = {
  pending: { icon: Clock, label: '排队中', color: 'text-yellow-600 bg-yellow-50' },
  processing: { icon: Loader2, label: '生成中', color: 'text-blue-600 bg-blue-50' },
  completed: { icon: CheckCircle2, label: '已完成', color: 'text-green-600 bg-green-50' },
  failed: { icon: XCircle, label: '失败', color: 'text-red-600 bg-red-50' },
  cancelled: { icon: XCircle, label: '已取消', color: 'text-gray-500 bg-gray-50' },
}

export function HistoryPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<TaskStatus | ''>('')
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const { data, isLoading } = useQuery({
    queryKey: ['history', statusFilter, page],
    queryFn: () => historyApi.list({ status: statusFilter || undefined, page, pageSize: 12 }),
  })

  const deleteMutation = useMutation({
    mutationFn: (ids: string[]) =>
      ids.length === 1 ? historyApi.delete(ids[0]) : historyApi.batchDelete(ids),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['history'] })
      setSelected(new Set())
    },
  })

  const tasks = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / 12)

  const toggleSelect = (id: string) => {
    setSelected((s) => {
      const ns = new Set(s)
      ns.has(id) ? ns.delete(id) : ns.add(id)
      return ns
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">生成历史</h1>
            <p className="text-muted-foreground text-sm mt-1">共 {total} 条记录</p>
          </div>
          <Button onClick={() => navigate('/generate')}>
            + 新建生成
          </Button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-1">
          <Filter className="h-4 w-4 text-muted-foreground shrink-0" />
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => { setStatusFilter(f.value); setPage(1) }}
              className={cn(
                'whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-medium transition-colors',
                statusFilter === f.value
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-white border text-muted-foreground hover:text-foreground',
              )}
            >
              {f.label}
            </button>
          ))}
          {selected.size > 0 && (
            <Button
              variant="destructive"
              size="sm"
              className="ml-auto"
              onClick={() => deleteMutation.mutate(Array.from(selected))}
            >
              <Trash2 className="mr-1.5 h-4 w-4" />
              删除 {selected.size} 条
            </Button>
          )}
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="grid grid-cols-1 gap-4">
            {Array.from({ length: 4 }, (_, i) => (
              <div key={i} className="h-28 rounded-xl shimmer" />
            ))}
          </div>
        ) : tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <ImageIcon className="h-16 w-16 text-muted-foreground/20 mb-4" />
            <h3 className="text-lg font-medium mb-2">暂无记录</h3>
            <p className="text-muted-foreground text-sm mb-6">开始您的第一次 AI 艺术照生成</p>
            <Button onClick={() => navigate('/generate')}>立即创作</Button>
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => (
              <TaskRow
                key={task.id}
                task={task}
                selected={selected.has(task.id)}
                onToggleSelect={() => toggleSelect(task.id)}
                onView={() => task.status === 'processing' || task.status === 'pending'
                  ? navigate(`/progress/${task.id}`)
                  : navigate(`/result/${task.id}`)
                }
                onDelete={() => deleteMutation.mutate([task.id])}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-8">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              上一页
            </Button>
            <span className="flex items-center text-sm text-muted-foreground px-3">
              {page} / {totalPages}
            </span>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
              下一页
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

interface TaskRowProps {
  task: GenerationTask
  selected: boolean
  onToggleSelect: () => void
  onView: () => void
  onDelete: () => void
}

function TaskRow({ task, selected, onToggleSelect, onView, onDelete }: TaskRowProps) {
  const cfg = STATUS_CONFIG[task.status]
  const Icon = cfg.icon

  const thumbnails = (task.resultImages ?? []).slice(0, 4)

  return (
    <Card className={cn('transition-colors', selected && 'ring-2 ring-primary/40')}>
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          {/* Checkbox */}
          <input
            type="checkbox"
            checked={selected}
            onChange={onToggleSelect}
            className="h-4 w-4 rounded border-gray-300 text-primary"
          />

          {/* Thumbnails */}
          <div className="flex gap-1.5 shrink-0">
            {thumbnails.length > 0
              ? thumbnails.map((img, i) => (
                  <div key={i} className="h-16 w-12 overflow-hidden rounded-lg bg-muted">
                    <img src={img.thumbnailUrl || img.originalUrl} alt="" className="h-full w-full object-cover" />
                  </div>
                ))
              : (
                  <div className="h-16 w-12 rounded-lg bg-muted flex items-center justify-center">
                    <ImageIcon className="h-5 w-5 text-muted-foreground/40" />
                  </div>
                )}
            {(task.resultImages?.length ?? 0) > 4 && (
              <div className="h-16 w-12 rounded-lg bg-muted flex items-center justify-center text-xs text-muted-foreground font-medium">
                +{(task.resultImages?.length ?? 0) - 4}
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-sm truncate">{task.scene?.name ?? '未知场景'}</span>
              <span className={cn('inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium', cfg.color)}>
                <Icon className={cn('h-3 w-3', task.status === 'processing' && 'animate-spin')} />
                {cfg.label}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground flex-wrap">
              <span>{task.aiModel}</span>
              <span>·</span>
              <span>{formatDate(task.createdAt)}</span>
              {task.resultImages && (
                <>
                  <span>·</span>
                  <span>{task.resultImages.length} 张</span>
                </>
              )}
            </div>
            {(task.status === 'processing' || task.status === 'pending') && (
              <div className="mt-2">
                <Progress value={task.progress} className="h-1.5" />
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2 shrink-0">
            {task.status === 'completed' ? (
              <Button size="sm" variant="outline" onClick={onView}>
                <Eye className="mr-1 h-3.5 w-3.5" /> 查看
              </Button>
            ) : (task.status === 'processing' || task.status === 'pending') ? (
              <Button size="sm" variant="outline" onClick={onView}>
                <RefreshCw className="mr-1 h-3.5 w-3.5" /> 进度
              </Button>
            ) : null}
            <Button size="icon" variant="ghost" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={onDelete}>
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
