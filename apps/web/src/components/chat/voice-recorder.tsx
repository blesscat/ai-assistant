'use client'

import { useState, useRef, useEffect } from 'react'
import { Mic, Square, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface VoiceRecorderProps {
  onRecord: (audioData: string) => void
  onClose: () => void
}

export function VoiceRecorder({ onRecord, onClose }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [duration, setDuration] = useState(0)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop()
      }
    }
  }, [isRecording])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' })
        const reader = new FileReader()
        reader.onload = () => {
          const base64 = (reader.result as string).split(',')[1]
          onRecord(base64)
        }
        reader.readAsDataURL(blob)

        // 停止所有音軌
        stream.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      setDuration(0)

      timerRef.current = setInterval(() => {
        setDuration((prev) => prev + 1)
      }, 1000)
    } catch (error) {
      console.error('無法存取麥克風:', error)
      alert('無法存取麥克風，請確認已授予權限')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="relative mb-4">
      <Button variant="ghost" size="icon" className="absolute top-2 right-2 z-10" onClick={onClose}>
        <X className="h-4 w-4" />
      </Button>

      <div className="bg-muted/50 rounded-lg border p-6 text-center">
        <div className="flex flex-col items-center gap-4">
          {isRecording ? (
            <>
              <div className="relative">
                <div className="absolute inset-0 animate-ping rounded-full bg-red-400 opacity-75" />
                <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-red-500">
                  <Mic className="h-8 w-8 text-white" />
                </div>
              </div>
              <p className="text-lg font-medium">{formatDuration(duration)}</p>
              <Button variant="destructive" onClick={stopRecording}>
                <Square className="mr-2 h-4 w-4" />
                停止錄音
              </Button>
            </>
          ) : (
            <>
              <div className="bg-primary flex h-16 w-16 items-center justify-center rounded-full">
                <Mic className="text-primary-foreground h-8 w-8" />
              </div>
              <p className="text-muted-foreground text-sm">點擊開始錄音</p>
              <Button onClick={startRecording}>
                <Mic className="mr-2 h-4 w-4" />
                開始錄音
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
