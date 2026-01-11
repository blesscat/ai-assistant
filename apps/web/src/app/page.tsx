'use client'

import { useSession } from 'next-auth/react'
import { redirect } from 'next/navigation'
import { ChatContainer } from '@/components/chat/chat-container'
import { Sidebar } from '@/components/chat/sidebar'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { LogOut, User, Menu } from 'lucide-react'
import { signOut } from 'next-auth/react'
import { useAtom } from 'jotai'
import { sidebarOpenAtom } from '@/atoms/ui-atoms'

export default function Home() {
  const { data: session, status } = useSession()
  const [sidebarOpen, setSidebarOpen] = useAtom(sidebarOpenAtom)

  if (status === 'loading') {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="border-primary h-8 w-8 animate-spin rounded-full border-b-2"></div>
      </div>
    )
  }

  if (!session) {
    redirect('/login')
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="bg-background flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setSidebarOpen(true)}>
            <Menu className="h-4 w-4" />
          </Button>
          <h1 className="text-xl font-semibold">AI 助理</h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Avatar className="h-8 w-8">
              <AvatarImage src={session.user?.image || undefined} />
              <AvatarFallback>
                <User className="h-4 w-4" />
              </AvatarFallback>
            </Avatar>
            <span className="hidden text-sm font-medium sm:inline">{session.user?.name}</span>
          </div>
          <Button variant="ghost" size="icon" onClick={() => signOut({ callbackUrl: '/login' })}>
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex flex-1 overflow-hidden">
        <Sidebar />
        <div className="flex-1 overflow-hidden">
          <ChatContainer />
        </div>
      </main>
    </div>
  )
}
