import { create } from 'zustand'
import type { Scene, AIModel, InputImage, GenerationParams } from '@/types'

interface GenerateState {
  selectedScene: Scene | null
  selectedModel: AIModel | null
  inputImages: InputImage[]
  params: GenerationParams
  setScene: (scene: Scene) => void
  setModel: (model: AIModel) => void
  addImage: (image: InputImage) => void
  removeImage: (storageKey: string) => void
  updateParams: (params: Partial<GenerationParams>) => void
  reset: () => void
}

const defaultParams: GenerationParams = {
  aspectRatio: '3:4',
  quality: 'hd',
  outputCount: 2,
  styleStrength: 7,
}

export const useGenerateStore = create<GenerateState>((set) => ({
  selectedScene: null,
  selectedModel: null,
  inputImages: [],
  params: defaultParams,
  setScene: (scene) => set({ selectedScene: scene }),
  setModel: (model) => set({ selectedModel: model }),
  addImage: (image) =>
    set((state) => ({
      inputImages: [...state.inputImages.filter((i) => i.role !== image.role), image],
    })),
  removeImage: (storageKey) =>
    set((state) => ({
      inputImages: state.inputImages.filter((i) => i.storageKey !== storageKey),
    })),
  updateParams: (params) =>
    set((state) => ({ params: { ...state.params, ...params } })),
  reset: () =>
    set({ selectedScene: null, selectedModel: null, inputImages: [], params: defaultParams }),
}))
