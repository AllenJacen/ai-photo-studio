import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Navbar } from '@/components/layout/Navbar'
import { HomePage } from '@/pages/Home'
import { GeneratePage } from '@/pages/Generate'
import { ProgressPage } from '@/pages/Progress'
import { ResultPage } from '@/pages/Result'
import { HistoryPage } from '@/pages/History'
import { ProfilePage } from '@/pages/Profile'
import { AuthPage } from '@/pages/Auth'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 1000 * 60, retry: 1 },
  },
})

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/auth/:mode" element={<AuthPage />} />
          <Route path="/auth" element={<Navigate to="/auth/login" replace />} />
          <Route
            path="/*"
            element={
              <Layout>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/generate" element={<GeneratePage />} />
                  <Route path="/progress/:taskId" element={<ProgressPage />} />
                  <Route path="/result/:taskId" element={<ResultPage />} />
                  <Route path="/history" element={<HistoryPage />} />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Layout>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
