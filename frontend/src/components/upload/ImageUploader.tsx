import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { uploadApi } from '@/services/api'
import type { InputImage } from '@/types'

interface Props {
  role: 'single' | 'person1' | 'person2'
  label?: string
  value?: InputImage
  onChange: (image: InputImage) => void
  onRemove: () => void
}

export function ImageUploader({ role, label = '上传照片', value, onChange, onRemove }: Props) {
  const [uploading, setUploading] = useState(false)
  const [uploadPct, setUploadPct] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return

      setUploading(true)
      setError(null)
      setUploadPct(0)

      try {
        const { uploadUrl, storageKey } = await uploadApi.presign({
          fileName: file.name,
          fileSize: file.size,
          fileType: file.type,
        })

        await uploadApi.uploadToOss(uploadUrl, file, setUploadPct)
        const { faceDetectionResult } = await uploadApi.confirm(storageKey)

        onChange({
          storageKey,
          role,
          previewUrl: URL.createObjectURL(file),
          faceDetection: faceDetectionResult,
        })
      } catch {
        setError('上传失败，请重试')
      } finally {
        setUploading(false)
      }
    },
    [role, onChange],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.heic'] },
    maxSize: 20 * 1024 * 1024,
    multiple: false,
    disabled: uploading,
  })

  if (value?.previewUrl) {
    return (
      <div className="relative group overflow-hidden rounded-xl border bg-muted aspect-[3/4]">
        <img src={value.previewUrl} alt="上传的照片" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <button
            onClick={onRemove}
            className="rounded-full bg-white/20 p-2 text-white hover:bg-white/40 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        {value.faceDetection && (
          <div className={cn(
            'absolute bottom-2 left-2 right-2 flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium',
            value.faceDetection.qualityScore >= 0.7
              ? 'bg-green-500/90 text-white'
              : 'bg-yellow-500/90 text-white',
          )}>
            {value.faceDetection.qualityScore >= 0.7
              ? <CheckCircle2 className="h-3.5 w-3.5" />
              : <AlertCircle className="h-3.5 w-3.5" />}
            检测到 {value.faceDetection.facesFound} 张人脸，质量{' '}
            {Math.round(value.faceDetection.qualityScore * 100)}%
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        'relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed aspect-[3/4] transition-colors',
        isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50 hover:bg-muted/50',
        uploading && 'pointer-events-none',
      )}
    >
      <input {...getInputProps()} />
      {uploading ? (
        <div className="flex flex-col items-center gap-3 px-4 text-center">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <div className="w-full">
            <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${uploadPct}%` }}
              />
            </div>
            <p className="mt-1.5 text-xs text-muted-foreground">上传中 {uploadPct}%</p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3 p-4 text-center">
          <div className="rounded-full bg-muted p-4">
            <Upload className="h-6 w-6 text-muted-foreground" />
          </div>
          <div>
            <p className="text-sm font-medium">{label}</p>
            <p className="text-xs text-muted-foreground mt-1">
              拖拽或点击上传
              <br />
              JPG / PNG / WEBP，最大 20MB
            </p>
          </div>
          {error && (
            <p className="text-xs text-destructive flex items-center gap-1">
              <AlertCircle className="h-3.5 w-3.5" /> {error}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
