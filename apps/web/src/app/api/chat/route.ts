import { auth } from '@/lib/auth'

const ADK_API_URL = process.env.ADK_API_URL || 'http://localhost:8000'

interface AISdkMessage {
  id: string
  role: 'user' | 'assistant'
  parts?: Array<{ type: string; text?: string }>
  content?: string
}

interface BackendMessage {
  role: string
  content: string
}

export async function POST(req: Request) {
  const session = await auth()

  if (!session?.user?.id) {
    return new Response('Unauthorized', { status: 401 })
  }

  const body = await req.json()
  const { messages, conversationId } = body

  // 轉換 AI SDK v6 訊息格式到後端格式
  const transformedMessages: BackendMessage[] = (messages || []).map((msg: AISdkMessage) => {
    // AI SDK v6 使用 parts 陣列
    let content = msg.content || ''
    if (msg.parts && msg.parts.length > 0) {
      content = msg.parts
        .filter((part) => part.type === 'text' && part.text)
        .map((part) => part.text)
        .join('')
    }
    return {
      role: msg.role,
      content,
    }
  })

  console.log('Transformed messages:', JSON.stringify(transformedMessages, null, 2))

  try {
    // DEBUG: 先測試 debug endpoint
    const requestBody = {
      messages: transformedMessages,
      user_id: session.user.id,
      conversation_id: conversationId || null,
    }
    console.log('Sending to backend:', JSON.stringify(requestBody, null, 2))

    // 轉發請求到 Python 後端
    const response = await fetch(`${ADK_API_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Backend error:', response.status, errorText)
      throw new Error(`Backend error: ${response.status}`)
    }

    console.log('Backend response OK, streaming...')

    // 直接轉發 SSE stream (AI SDK data stream protocol)
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
        'X-Accel-Buffering': 'no',
        'x-vercel-ai-data-stream': 'v1',
      },
    })
  } catch (error) {
    console.error('Chat API error:', error)
    return new Response('Internal Server Error', { status: 500 })
  }
}
