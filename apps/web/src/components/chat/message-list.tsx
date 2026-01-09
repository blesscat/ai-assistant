'use client'

import type { UIMessage } from '@ai-sdk/react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { MessageItem } from './message-item'
import { useEffect, useRef } from 'react'
import { Loader2 } from 'lucide-react'

interface MessageListProps {
  messages: UIMessage[]
  isLoading: boolean
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="mx-auto max-w-3xl space-y-4">
        {messages.length === 0 ? (
          <div className="text-muted-foreground flex h-full flex-col items-center justify-center py-20 text-center">
            <h2 className="mb-2 text-2xl font-semibold">AI 助理</h2>
            <p>有什麼我可以幫助你的嗎？</p>
          </div>
        ) : (
          messages.map((message) => <MessageItem key={message.id} message={message} />)
        )}
        {isLoading && (
          <div className="text-muted-foreground flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>AI 正在思考中...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}
