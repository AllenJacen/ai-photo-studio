import axios from 'axios'
import type {
  User, Scene, SceneCategory, AIModel,
  GenerationTask, GeneratedImage, PaginatedResponse,
  PresignResult, UploadConfirmResult, CreateTaskRequest, CreateTaskResponse,
} from '@/types'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (res) => res.data.data,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/auth/login'
    }
    return Promise.reject(err.response?.data || err)
  },
)

export const authApi = {
  login: (data: { email?: string; phone?: string; password?: string; smsCode?: string }) =>
    http.post<never, { user: User; accessToken: string; refreshToken: string }>('/auth/login', data),
  register: (data: { email?: string; phone?: string; password?: string; smsCode?: string }) =>
    http.post<never, { user: User; accessToken: string; refreshToken: string }>('/auth/register', data),
  sendSms: (phone: string) => http.post('/auth/sms/send', { phone }),
  refresh: (refreshToken: string) =>
    http.post<never, { accessToken: string; refreshToken: string }>('/auth/refresh', { refreshToken }),
}

export const userApi = {
  me: () => http.get<never, User>('/users/me'),
}

export const uploadApi = {
  presign: (data: { fileName: string; fileSize: number; fileType: string }) =>
    http.post<never, PresignResult>('/uploads/presign', { ...data, purpose: 'source' }),
  confirm: (storageKey: string) =>
    http.post<never, UploadConfirmResult>('/uploads/confirm', { storageKey }),
  uploadToOss: async (uploadUrl: string, file: File, onProgress?: (pct: number) => void) => {
    await axios.put(uploadUrl, file, {
      headers: { 'Content-Type': file.type },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
      },
    })
  },
}

export const sceneApi = {
  list: (params?: { category?: string; keyword?: string; page?: number; pageSize?: number }) =>
    http.get<never, PaginatedResponse<Scene>>('/scenes', { params }),
  get: (id: string) => http.get<never, Scene>(`/scenes/${id}`),
  categories: () => http.get<never, SceneCategory[]>('/scenes/categories'),
  recommended: () => http.get<never, Scene[]>('/scenes/recommended'),
}

export const modelApi = {
  list: () => http.get<never, AIModel[]>('/ai-models'),
  status: (id: string) => http.get<never, { status: string; queueLength: number; estimatedWaitS: number }>(`/ai-models/${id}/status`),
}

export const taskApi = {
  create: (data: CreateTaskRequest) =>
    http.post<never, CreateTaskResponse>('/tasks', data),
  get: (id: string) => http.get<never, GenerationTask>(`/tasks/${id}`),
  cancel: (id: string) => http.post<never, { success: boolean; creditsRefunded: number }>(`/tasks/${id}/cancel`),
  retry: (id: string) => http.post<never, CreateTaskResponse>(`/tasks/${id}/retry`),
  results: (id: string) => http.get<never, GeneratedImage[]>(`/tasks/${id}/results`),
}

export const historyApi = {
  list: (params?: { status?: string; page?: number; pageSize?: number }) =>
    http.get<never, PaginatedResponse<GenerationTask>>('/history', { params }),
  delete: (id: string) => http.delete(`/history/${id}`),
  batchDelete: (ids: string[]) => http.delete('/history', { data: { taskIds: ids } }),
}

export const imageApi = {
  downloadUrl: (id: string, format?: string) =>
    http.get<never, { downloadUrl: string; expiresIn: number }>(`/images/${id}/download-url`, { params: { format } }),
  batchDownload: (imageIds: string[]) =>
    http.post<never, { zipUrl: string; expiresIn: number }>('/images/batch-download', { imageIds }),
  favorite: (id: string) =>
    http.post<never, { isFavorited: boolean }>(`/images/${id}/favorite`),
  rate: (id: string, rating: number) =>
    http.post(`/images/${id}/rate`, { rating }),
  share: (id: string, data: { expiresHours: number; password?: string }) =>
    http.post<never, { shareUrl: string; expiresAt: string }>(`/images/${id}/share`, data),
}
