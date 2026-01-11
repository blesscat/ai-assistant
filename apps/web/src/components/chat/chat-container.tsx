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
  const { currentConversationId, addConversation, updateConversation } = useChatStore()
  const [input, setInput] = useState('')
  const [key, setKey] = useState(0) // 用於強制重新創建 useChat hook

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
    key: key.toString(), // 使用 key 來強制重置
  })

  const isLoading = status === 'streaming' || status === 'submitted'

  // 當對話切換時，重置 messages
  useEffect(() => {
    setKey((prev) => prev + 1) // 改變 key 會強制 useChat 重新初始化
  }, [currentConversationId])

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
    // 注意：input 已經在 ChatInput 中被清除了，這裡不需要再清除

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

    // 如果是新對話的第一條訊息，自動生成標題
    if (messages.length === 0 && currentConversationId && content.trim()) {
      const title = content.trim().slice(0, 30) + (content.trim().length > 30 ? '...' : '')
      updateConversation(currentConversationId, { title })
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
