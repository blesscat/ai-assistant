'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useSession } from 'next-auth/react'
import { MessageList } from './message-list'
import { ChatInput } from './chat-input'
import { useChatStore } from '@/stores/chat-store'
import { useEffect, useState, useMemo } from 'react'

export function ChatContainer() {
  const { data: session } = useSession()
  const { currentConversationId, addConversation } = useChatStore()
  const [input, setInput] = useState('')

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: '/api/chat',
        body: {
          userId: session?.user?.id,
          conversationId: currentConversationId,
        },
      }),
    [session?.user?.id, currentConversationId]
  )

  const { messages, sendMessage, status } = useChat({
    transport,
  })

  const isLoading = status === 'streaming' || status === 'submitted'

  // 如果沒有當前對話，建立一個新的
  useEffect(() => {
    if (!currentConversationId && messages.length === 0) {
      const newConversation = {
        id: crypto.randomUUID(),
        title: '新對話',
        createdAt: new Date(),
        updatedAt: new Date(),
      }
      addConversation(newConversation)
    }
  }, [currentConversationId, messages.length, addConversation])

  const handleSendMessage = (content: string, attachments?: { type: 'image' | 'audio'; data: string }[]) => {
    // 先清除 input（重要：無論送出成功與否都清除，避免重複送出）
    setInput('')

    // 檢查是否有內容
    if (!content.trim() && !attachments?.length) return

    // 建構多模態訊息
    const parts: Array<{ type: 'text'; text: string } | { type: 'file'; mediaType: string; data: string }> = []

    if (content.trim()) {
      parts.push({ type: 'text', text: content })
    }

    if (attachments) {
      for (const attachment of attachments) {
        parts.push({
          type: 'file',
          mediaType: attachment.type === 'image' ? 'image/png' : 'audio/wav',
          data: attachment.data,
        })
      }
    }

    // 送出訊息
    sendMessage({ text: content })
  }

  return (
    <div className="flex h-full flex-col">
      <MessageList messages={messages} isLoading={isLoading} />
      <ChatInput input={input} onInputChange={setInput} onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  )
}
