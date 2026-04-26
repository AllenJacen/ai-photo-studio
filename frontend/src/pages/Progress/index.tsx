import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { CheckCircle2, XCircle, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { taskApi } from '@/services/api'
import { formatDuration } from '@/lib/utils'
import type { GenerationTask } from '@/types'

const STAGE_LABELS: Record<string, string> = {
  preprocessing: '图片预处理中',
  generating: 'AI 正在绘制您的专属艺术照',
  postprocessing: '图片后处理与优化中',
}

const TIPS = [
  '选择光线均匀、五官清晰的照片效果更好',
  '正面或稍侧面的照片比侧脸效果更佳',
  '建议上传高分辨率（>800px）的照片',
  '风格强度越高，生成效果越艺术化',
  '多试几个场景，找到最适合自己的风格',
  '情侣模式下建议两人分别单独上传照片',
]

export function ProgressPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [task, setTask] = useState<GenerationTask | null>(null)
  const [tipIndex, setTipIndex] = useState(0)
  const [cancelling, setCancelling] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!taskId) return

    // cancelled 标志位:页面离开后,所有异步回调(WS onerror、polling tick)
    // 都要先检查它,避免在已 unmount 的状态下做副作用(尤其是 navigate)。
    let cancelled = false

    const token = localStorage.getItem('access_token')
    const wsUrl = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/tasks/${taskId}?token=${token}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (e) => {
      if (cancelled) return
      const msg = JSON.parse(e.data)
      if (msg.event === 'task_update' || msg.event === 'task_completed' || msg.event === 'task_failed') {
        setTask((prev) => prev ? { ...prev, ...msg.data } : msg.data)
      }
      if (msg.event === 'task_completed') {
        navigate(`/result/${taskId}`)
      }
    }

    ws.onerror = () => {
      // 关键修复:如果 effect 已经 cleanup(用户离开页面),不能再启动 polling。
      // 否则会产生孤儿 interval,定时把用户从其他页面拉回 result 页。
      if (cancelled) return
      pollRef.current = setInterval(async () => {
        if (cancelled) {
          if (pollRef.current) clearInterval(pollRef.current)
          return
        }
        try {
          const t = await taskApi.get(taskId)
          if (cancelled) return
          setTask(t)
          if (t.status === 'completed') {
            if (pollRef.current) clearInterval(pollRef.current)
            navigate(`/result/${taskId}`)
          }
          if (t.status === 'failed' || t.status === 'cancelled') {
            if (pollRef.current) clearInterval(pollRef.current)
          }
        } catch {
          // 忽略瞬时网络错误,下个 tick 再试
        }
      }, 3000)
    }

    // Initial fetch
    taskApi.get(taskId).then((t) => { if (!cancelled) setTask(t) }).catch(() => {})

    return () => {
      cancelled = true
      ws.onmessage = null
      ws.onerror = null
      ws.close()
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [taskId, navigate])

  // Rotate tips
  useEffect(() => {
    const t = setInterval(() => setTipIndex((i) => (i + 1) % TIPS.length), 5000)
    return () => clearInterval(t)
  }, [])

  const handleCancel = async () => {
    if (!taskId || !task) return
    setCancelling(true)
    try {
      await taskApi.cancel(taskId)
      navigate('/history')
    } catch {
      setCancelling(false)
    }
  }

  const progress = task?.progress ?? 0
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (progress / 100) * circumference

  const isFailed = task?.status === 'failed'
  const isProcessing = !isFailed && task?.status !== 'cancelled'

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto">
          {isFailed ? (
            <Card>
              <CardContent className="p-8 text-center">
                <XCircle className="h-16 w-16 text-destructive mx-auto mb-4" />
                <h2 className="text-xl font-bold mb-2">生成失败</h2>
                <p className="text-muted-foreground mb-6">{task?.errorMessage ?? '生成过程中出现错误，积分已自动退还'}</p>
                <div className="flex gap-3 justify-center">
                  <Button variant="outline" onClick={() => navigate('/generate')}>重新尝试</Button>
                  <Button onClick={() => navigate('/history')}>查看历史</Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Progress Ring Card */}
              <Card className="mb-6">
                <CardContent className="p-8 text-center">
                  <div className="relative inline-flex items-center justify-center mb-6">
                    <svg className="w-36 h-36 -rotate-90" viewBox="0 0 120 120">
                      <circle
                        cx="60" cy="60" r={radius}
                        fill="none" stroke="hsl(var(--border))" strokeWidth="8"
                      />
                      <circle
                        cx="60" cy="60" r={radius}
                        fill="none" stroke="hsl(var(--primary))" strokeWidth="8"
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={strokeDashoffset}
                        style={{ transition: 'stroke-dashoffset 0.5s ease' }}
                      />
                    </svg>
                    <div className="absolute text-center">
                      <div className="text-3xl font-bold text-primary">{progress}%</div>
                    </div>
                  </div>

                  <h2 className="text-xl font-bold mb-2">
                    {task?.currentStage ? STAGE_LABELS[task.currentStage] : 'AI 正在处理中...'}
                  </h2>

                  {isProcessing && task?.estimatedRemainingS != null && task.estimatedRemainingS > 0 && (
                    <p className="text-muted-foreground mb-2">
                      预计还需 <span className="font-medium text-foreground">{formatDuration(task.estimatedRemainingS)}</span>
                    </p>
                  )}

                  {task?.queuePosition != null && task.queuePosition > 0 && (
                    <p className="text-sm text-muted-foreground mb-2">
                      队列排位：第 <span className="font-medium text-foreground">{task.queuePosition}</span> 位
                    </p>
                  )}

                  <div className="mt-6 flex justify-center">
                    {task?.status === 'pending' && (
                      <Button
                        variant="outline"
                        size="sm"
                        loading={cancelling}
                        onClick={handleCancel}
                      >
                        <X className="mr-1.5 h-4 w-4" /> 取消任务
                      </Button>
                    )}
                    {task?.status === 'processing' && (
                      <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                        生成中不可取消，您可以关闭页面，完成后将通知您
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Tips */}
              <Card className="bg-primary/5 border-primary/20">
                <CardContent className="p-4 text-center">
                  <p className="text-xs text-muted-foreground mb-1">小贴士</p>
                  <p className="text-sm text-foreground transition-all">{TIPS[tipIndex]}</p>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
