'use client'

import { useState, useRef, FormEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Send, Mic, X, Image as ImageIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { FileUpload } from './file-upload'
import { VoiceRecorder } from './voice-recorder'

interface ChatInputProps {
  input: string
  onInputChange: (value: string) => void
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
  onSendMessage: (content: string, attachments?: { type: 'image' | 'audio'; data: string }[]) => void
  isLoading: boolean
}

export function ChatInput({ input, onInputChange, onSubmit, onSendMessage, isLoading }: ChatInputProps) {
  const [attachments, setAttachments] = useState<{ type: 'image' | 'audio'; data: string; preview?: string }[]>([])
  const [showFileUpload, setShowFileUpload] = useState(false)
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (isLoading) return

    onSendMessage(
      input,
      attachments.map((a) => ({ type: a.type, data: a.data }))
    )
    setAttachments([])
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      const form = e.currentTarget.form
      if (form) {
        form.requestSubmit()
      }
    }
  }

  const handleFileSelect = (file: File) => {
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = (reader.result as string).split(',')[1]
      setAttachments((prev) => [
        ...prev,
        {
          type: 'image',
          data: base64,
          preview: reader.result as string,
        },
      ])
    }
    reader.readAsDataURL(file)
    setShowFileUpload(false)
  }

  const handleVoiceRecord = (audioData: string) => {
    setAttachments((prev) => [
      ...prev,
      {
        type: 'audio',
        data: audioData,
      },
    ])
    setShowVoiceRecorder(false)
  }

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="bg-background border-t p-4">
      <div className="mx-auto max-w-3xl">
        {/* 附件預覽 */}
        {attachments.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {attachments.map((attachment, index) => (
              <div key={index} className="group bg-muted relative rounded-lg p-2">
                {attachment.type === 'image' && attachment.preview && (
                  <img src={attachment.preview} alt="預覽" className="h-16 w-16 rounded object-cover" />
                )}
                {attachment.type === 'audio' && (
                  <div className="flex items-center gap-2 px-3 py-2">
                    <Mic className="h-4 w-4" />
                    <span className="text-sm">語音訊息</span>
                  </div>
                )}
                <button
                  onClick={() => removeAttachment(index)}
                  className="bg-destructive text-destructive-foreground absolute -top-2 -right-2 rounded-full p-1 opacity-0 transition-opacity group-hover:opacity-100"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* 檔案上傳 */}
        {showFileUpload && <FileUpload onFileSelect={handleFileSelect} onClose={() => setShowFileUpload(false)} />}

        {/* 語音錄製 */}
        {showVoiceRecorder && (
          <VoiceRecorder onRecord={handleVoiceRecord} onClose={() => setShowVoiceRecorder(false)} />
        )}

        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <div className="flex gap-1">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => setShowFileUpload(!showFileUpload)}
              className={cn(showFileUpload && 'bg-muted')}
            >
              <ImageIcon className="h-5 w-5" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => setShowVoiceRecorder(!showVoiceRecorder)}
              className={cn(showVoiceRecorder && 'bg-muted')}
            >
              <Mic className="h-5 w-5" />
            </Button>
          </div>

          <div className="relative flex-1">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="輸入訊息..."
              rows={1}
              className="bg-background focus:ring-ring max-h-[200px] min-h-[48px] w-full resize-none rounded-lg border px-4 py-3 text-sm focus:ring-2 focus:outline-none"
              style={{
                height: 'auto',
                minHeight: '48px',
              }}
            />
          </div>

          <Button type="submit" size="icon" disabled={isLoading || (!input.trim() && attachments.length === 0)}>
            <Send className="h-5 w-5" />
          </Button>
        </form>
      </div>
    </div>
  )
}
