'use client'

import type { UIMessage } from '@ai-sdk/react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { useSession } from 'next-auth/react'
import { Bot, User } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MessageItemProps {
  message: UIMessage
}

export function MessageItem({ message }: MessageItemProps) {
  const { data: session } = useSession()
  const isUser = message.role === 'user'

  // 從 parts 取得文字內容
  const getTextContent = () => {
    if (!message.parts) return ''
    return message.parts
      .filter((part) => part.type === 'text')
      .map((part) => (part as { type: 'text'; text: string }).text)
      .join('')
  }

  return (
    <div className={cn('flex gap-3 rounded-lg p-4', isUser ? 'bg-muted/50' : 'bg-background')}>
      <Avatar className="h-8 w-8">
        {isUser ? (
          <>
            <AvatarImage src={session?.user?.image || undefined} />
            <AvatarFallback>
              <User className="h-4 w-4" />
            </AvatarFallback>
          </>
        ) : (
          <AvatarFallback className="bg-primary text-primary-foreground">
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        )}
      </Avatar>
      <div className="flex-1 space-y-2">
        <div className="text-sm font-medium">{isUser ? session?.user?.name || '你' : 'AI 助理'}</div>
        <div className="text-sm whitespace-pre-wrap">{getTextContent()}</div>
      </div>
    </div>
  )
}
