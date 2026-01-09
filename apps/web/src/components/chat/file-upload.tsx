'use client'

import { useCallback, useState } from 'react'
import { Upload, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  onClose: () => void
}

export function FileUpload({ onFileSelect, onClose }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)

      const files = e.dataTransfer.files
      if (files.length > 0) {
        const file = files[0]
        if (file.type.startsWith('image/')) {
          onFileSelect(file)
        }
      }
    },
    [onFileSelect]
  )

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      onFileSelect(files[0])
    }
  }

  return (
    <div className="relative mb-4">
      <Button variant="ghost" size="icon" className="absolute top-2 right-2 z-10" onClick={onClose}>
        <X className="h-4 w-4" />
      </Button>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          'rounded-lg border-2 border-dashed p-8 text-center transition-colors',
          isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
        )}
      >
        <Upload className="text-muted-foreground mx-auto mb-4 h-10 w-10" />
        <p className="text-muted-foreground mb-2 text-sm">拖放圖片到這裡，或點擊選擇檔案</p>
        <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" id="file-upload" />
        <label htmlFor="file-upload">
          <Button variant="outline" asChild>
            <span>選擇圖片</span>
          </Button>
        </label>
      </div>
    </div>
  )
}
