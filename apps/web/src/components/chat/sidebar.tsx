'use client'

import { useChatStore } from '@/stores/chat-store'
import { Button } from '@/components/ui/button'
import { MessageSquarePlus, Trash2, Menu, Pencil, Check, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAtom } from 'jotai'
import { sidebarOpenAtom } from '@/atoms/ui-atoms'
import { useState } from 'react'

export function Sidebar() {
  const [isOpen, setIsOpen] = useAtom(sidebarOpenAtom)
  const { conversations, currentConversationId, setCurrentConversation, addConversation, deleteConversation, updateConversation } =
    useChatStore()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  const handleNewConversation = () => {
    const newConversation = {
      id: crypto.randomUUID(),
      title: '新對話',
      createdAt: new Date(),
      updatedAt: new Date(),
    }
    addConversation(newConversation)
  }

  const handleDeleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('確定要刪除這個對話嗎？')) {
      deleteConversation(id)
    }
  }

  const handleStartEdit = (id: string, title: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(id)
    setEditTitle(title)
  }

  const handleSaveEdit = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (editTitle.trim()) {
      updateConversation(id, { title: editTitle.trim() })
    }
    setEditingId(null)
    setEditTitle('')
  }

  const handleCancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(null)
    setEditTitle('')
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => setIsOpen(false)} />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r bg-background transition-transform lg:relative lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="font-semibold">對話</h2>
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setIsOpen(false)}>
            <Menu className="h-4 w-4" />
          </Button>
        </div>

        {/* New conversation button */}
        <div className="p-3">
          <Button variant="outline" className="w-full justify-start gap-2" onClick={handleNewConversation}>
            <MessageSquarePlus className="h-4 w-4" />
            新對話
          </Button>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">尚無對話</div>
          ) : (
            <div className="space-y-1 p-2">
              {conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={cn(
                    'group flex items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-accent cursor-pointer',
                    currentConversationId === conversation.id && 'bg-accent'
                  )}
                  onClick={() => setCurrentConversation(conversation.id)}
                >
                  {editingId === conversation.id ? (
                    <>
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(conversation.id, e as any)
                          if (e.key === 'Escape') handleCancelEdit(e as any)
                        }}
                        className="flex-1 bg-transparent border-b border-primary focus:outline-none"
                        autoFocus
                      />
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={(e) => handleSaveEdit(conversation.id, e)}
                        >
                          <Check className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={handleCancelEdit}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    </>
                  ) : (
                    <>
                      <span className="flex-1 truncate">{conversation.title}</span>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={(e) => handleStartEdit(conversation.id, conversation.title, e)}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={(e) => handleDeleteConversation(conversation.id, e)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>
    </>
  )
}
