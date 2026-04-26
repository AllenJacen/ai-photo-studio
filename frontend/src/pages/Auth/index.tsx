import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Sparkles, Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { authApi } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'

type Mode = 'login' | 'register'

export function AuthPage() {
  const { mode = 'login' } = useParams<{ mode?: Mode }>()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isLogin = mode === 'login'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) { setError('请填写邮箱和密码'); return }
    setLoading(true)
    setError(null)
    try {
      const fn = isLogin ? authApi.login : authApi.register
      const result = await fn({ email, password })
      setAuth(result.user, result.accessToken)
      navigate('/generate')
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e?.message ?? (isLogin ? '登录失败，请检查邮箱和密码' : '注册失败，请重试'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-white to-purple-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-primary mb-3">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold">AI 艺术照</h1>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{isLogin ? '欢迎回来' : '免费注册'}</CardTitle>
            <CardDescription>
              {isLogin ? '登录您的账户继续创作' : '注册即送 5 次免费生成额度'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">邮箱</label>
                <Input
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">密码</label>
                <div className="relative">
                  <Input
                    type={showPwd ? 'text' : 'password'}
                    placeholder={isLogin ? '输入密码' : '设置密码（至少8位）'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={isLogin ? 1 : 8}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                    onClick={() => setShowPwd(!showPwd)}
                  >
                    {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}

              <Button type="submit" className="w-full" size="lg" loading={loading}>
                {isLogin ? '登录' : '注册并开始创作'}
              </Button>
            </form>

            <div className="mt-4 text-center text-sm text-muted-foreground">
              {isLogin ? (
                <>还没有账户？ <button className="text-primary hover:underline font-medium" onClick={() => navigate('/auth/register')}>免费注册</button></>
              ) : (
                <>已有账户？ <button className="text-primary hover:underline font-medium" onClick={() => navigate('/auth/login')}>立即登录</button></>
              )}
            </div>

            {!isLogin && (
              <p className="mt-4 text-center text-xs text-muted-foreground">
                注册即表示同意<button className="text-primary hover:underline">服务条款</button>和<button className="text-primary hover:underline">隐私政策</button>
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
