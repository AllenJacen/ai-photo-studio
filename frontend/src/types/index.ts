export type MembershipType = 'free' | 'standard' | 'pro'
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
export type TaskStage = 'preprocessing' | 'generating' | 'postprocessing'
export type ModelStatus = 'available' | 'busy' | 'maintenance'

export interface User {
  id: string
  email?: string
  phone?: string
  nickname: string
  avatarUrl?: string
  membershipType: MembershipType
  membershipExpiresAt?: string
  credits: number
  totalGenerated: number
}

export interface Scene {
  id: string
  name: string
  category: string
  description: string
  thumbnailUrl: string
  previewUrls: string[]
  recommendedModel: string
  supportedModels: string[]
  creditCost: number
  isPremium: boolean
  tags: string[]
  defaultParams: GenerationParams
}

export interface SceneCategory {
  id: string
  name: string
  icon: string
  count: number
}

export interface AIModel {
  id: string
  displayName: string
  description: string
  capabilities: string[]
  creditMultiplier: number
  avgGenerationTimeS: number
  maxResolution: string
  status: ModelStatus
  queueLength?: number
  estimatedWaitS?: number
}

export interface GenerationParams {
  width?: number
  height?: number
  aspectRatio: '1:1' | '4:3' | '3:4' | '16:9'
  quality: 'standard' | 'hd' | 'uhd'
  outputCount: 1 | 2 | 4
  styleStrength: number
  customPrompt?: string
  customNegativePrompt?: string
}

export interface InputImage {
  storageKey: string
  role: 'person1' | 'person2' | 'single'
  previewUrl?: string
  faceDetection?: FaceDetectionResult
}

export interface FaceDetectionResult {
  facesFound: number
  qualityScore: number
  warnings: string[]
}

export interface GenerationTask {
  id: string
  userId: string
  sceneId: string
  scene?: Scene
  aiModel: string
  status: TaskStatus
  progress: number
  currentStage?: TaskStage
  queuePosition?: number
  estimatedRemainingS?: number
  resultImages?: GeneratedImage[]
  errorMessage?: string
  creditsConsumed: number
  generationTimeMs?: number
  createdAt: string
  completedAt?: string
}

export interface GeneratedImage {
  id: string
  taskId: string
  originalUrl: string
  thumbnailUrl: string
  width: number
  height: number
  fileSize: number
  format: string
  isFavorited: boolean
  userRating?: number
  downloadCount: number
  watermarkRemoved: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  timestamp: number
}

export interface PresignResult {
  uploadUrl: string
  storageKey: string
  expiresIn: number
}

export interface UploadConfirmResult {
  imageId: string
  faceDetectionResult: FaceDetectionResult
}

export interface CreateTaskRequest {
  sceneId: string
  aiModel: string
  inputImages: { storageKey: string; role: string }[]
  params: GenerationParams
}

export interface CreateTaskResponse {
  taskId: string
  status: TaskStatus
  queuePosition: number
  estimatedWaitS: number
  creditsToConsume: number
}
