import { useNavigate } from 'react-router-dom'
import { Coins, Crown, Calendar, Sparkles, History as HistoryIcon, LogOut } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useAuthStore } from '@/stores/authStore'

const MEMBERSHIP_LABELS: Record<string, { label: string; color: string }> = {
  free: { label: '免费版', color: 'bg-gray-100 text-gray-700' },
  standard: { label: '标准版', color: 'bg-blue-100 text-blue-700' },
  pro: { label: 'Pro 专业版', color: 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white' },
}

export function ProfilePage() {
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuthStore()

  if (!isAuthenticated || !user) {
    return (
      <div className="container mx-auto px-4 py-12">
        <Card className="max-w-md mx-auto">
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground mb-4">请先登录</p>
            <Button onClick={() => navigate('/auth/login')}>去登录</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const ms = MEMBERSHIP_LABELS[user.membershipType] ?? MEMBERSHIP_LABELS.free
  const expiresAt = user.membershipExpiresAt ? new Date(user.membershipExpiresAt).toLocaleDateString('zh-CN') : null

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-2xl font-bold mb-6">个人中心</h1>

      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-white text-2xl font-bold">
              {(user.nickname || user.email || 'U').slice(0, 1).toUpperCase()}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-semibold">{user.nickname || '未命名用户'}</h2>
                <Badge className={ms.color}>{ms.label}</Badge>
              </div>
              <p className="text-sm text-muted-foreground">{user.email || user.phone}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="p-5 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-yellow-100 flex items-center justify-center">
              <Coins className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <div className="text-xs text-muted-foreground">剩余积分</div>
              <div className="text-2xl font-bold">{user.credits}</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <div className="text-xs text-muted-foreground">已生成</div>
              <div className="text-2xl font-bold">{user.totalGenerated}</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Calendar className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <div className="text-xs text-muted-foreground">会员到期</div>
              <div className="text-sm font-bold">{expiresAt ?? '永久'}</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">常用操作</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Button variant="outline" className="w-full justify-start" onClick={() => navigate('/generate')}>
            <Sparkles className="mr-2 h-4 w-4" /> 开始新的创作
          </Button>
          <Button variant="outline" className="w-full justify-start" onClick={() => navigate('/history')}>
            <HistoryIcon className="mr-2 h-4 w-4" /> 查看生成历史
          </Button>
          {user.membershipType === 'free' && (
            <Button variant="default" className="w-full justify-start">
              <Crown className="mr-2 h-4 w-4" /> 升级到 Pro 解锁全部场景
            </Button>
          )}
          <Button
            variant="outline"
            className="w-full justify-start text-destructive hover:text-destructive"
            onClick={() => { logout(); navigate('/') }}
          >
            <LogOut className="mr-2 h-4 w-4" /> 退出登录
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
