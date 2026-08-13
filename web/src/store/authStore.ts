import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { AxiosError } from 'axios'
import { authApi } from '../services/api'

interface AuthState {
  token: string | null
  username: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
  login: (password: string) => Promise<boolean>
  logout: () => Promise<void>
  clearError: () => void
}

function extractErrorMessage(error: unknown, defaultMsg: string): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail
    if (detail) return detail
  }
  if (error instanceof Error) return error.message
  return defaultMsg
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      username: null,
      isAuthenticated: false,
      loading: false,
      error: null,

      login: async (password: string) => {
        set({ loading: true, error: null })
        try {
          const response = await authApi.login(password)
          localStorage.setItem('auth_token', response.token)
          set({
            token: response.token,
            username: response.username,
            isAuthenticated: true,
            loading: false,
            error: null,
          })
          return true
        } catch (error: unknown) {
          const errorMessage = extractErrorMessage(error, '登录失败')
          set({ loading: false, error: errorMessage })
          return false
        }
      },

      logout: async () => {
        try {
          await authApi.logout()
        } catch {
          // 忽略登出错误
        }
        localStorage.removeItem('auth_token')
        set({
          token: null,
          username: null,
          isAuthenticated: false,
          loading: false,
          error: null,
        })
      },

      clearError: () => {
        set({ error: null })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        username: state.username,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
