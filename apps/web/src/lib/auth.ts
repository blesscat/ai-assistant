import NextAuth from 'next-auth'
import Google from 'next-auth/providers/google'

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          prompt: 'consent',
          access_type: 'offline',
          response_type: 'code',
        },
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      // 當用戶首次登入或每次登入時，同步用戶資訊到後端資料庫
      if (account?.provider === 'google' && profile) {
        try {
          const ADK_API_URL = process.env.ADK_API_URL || 'http://localhost:8000'
          const response = await fetch(`${ADK_API_URL}/api/users/sync`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              google_id: profile.sub,
              email: profile.email,
              name: profile.name,
              image: profile.picture,
            }),
          })

          if (!response.ok) {
            console.error('Failed to sync user to database:', response.status)
            // 不阻擋登入，即使同步失敗
          } else {
            console.log('User synced to database successfully')
          }
        } catch (error) {
          console.error('Error syncing user to database:', error)
          // 不阻擋登入
        }
      }
      return true
    },
    async jwt({ token, account, profile }) {
      if (account && profile) {
        token.accessToken = account.access_token
        token.refreshToken = account.refresh_token
        token.expiresAt = account.expires_at
        token.googleId = profile.sub
      }
      return token
    },
    async session({ session, token }) {
      session.user.id = token.googleId as string
      session.accessToken = token.accessToken as string
      return session
    },
  },
  pages: {
    signIn: '/login',
  },
})

declare module 'next-auth' {
  interface Session {
    accessToken?: string
    user: {
      id: string
      name?: string | null
      email?: string | null
      image?: string | null
    }
  }
}
