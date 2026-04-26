import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Sparkles, History, User, LogOut, Coins } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore()
  const navigate = useNavigate()
  const { pathname } = useLocation()

  const isActive = (path: string) =>
    path === '/' ? pathname === '/' : pathname.startsWith(path)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <nav className="sticky top-0 z-40 w-full border-b bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <span className="bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
            AI 艺术照
          </span>
        </Link>

        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <>
              <div className="hidden sm:flex items-center gap-1.5 rounded-full border bg-muted px-3 py-1.5 text-sm">
                <Coins className="h-3.5 w-3.5 text-yellow-500" />
                <span className="font-medium">{user?.credits ?? 0}</span>
                <span className="text-muted-foreground">积分</span>
              </div>
              <Button
                variant={isActive('/generate') ? 'default' : 'ghost'}
                size="sm"
                onClick={() => navigate('/generate')}
                disabled={isActive('/generate')}
                className={cn(isActive('/generate') && 'pointer-events-none')}
              >
                <Sparkles className="mr-2 h-4 w-4" />
                开始创作
              </Button>
              <Button
                variant={isActive('/history') ? 'secondary' : 'ghost'}
                size="icon"
                onClick={() => navigate('/history')}
                title="历史记录"
              >
                <History className="h-4 w-4" />
              </Button>
              <Button
                variant={isActive('/profile') ? 'secondary' : 'ghost'}
                size="icon"
                onClick={() => navigate('/profile')}
                title="个人中心"
              >
                <User className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate('/auth/login')}>
                登录
              </Button>
              <Button size="sm" onClick={() => navigate('/auth/register')}>
                免费注册
              </Button>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
