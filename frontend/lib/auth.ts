import Cookies from 'js-cookie'
import api from './api'

export interface User { nome: string; perfil: string }

export async function login(email: string, senha: string): Promise<User> {
  const { data } = await api.post('/auth/login', { email, senha })
  Cookies.set('access_token', data.access_token, { expires: 1/3, secure: false, sameSite: 'strict' })
  Cookies.set('refresh_token', data.refresh_token, { expires: 7, secure: false, sameSite: 'strict' })
  return { nome: data.nome, perfil: data.perfil }
}

export function logout() {
  Cookies.remove('access_token')
  Cookies.remove('refresh_token')
  window.location.href = '/login'
}

export function getUser(): User | null {
  const token = Cookies.get('access_token')
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return { nome: '', perfil: payload.perfil }
  } catch { return null }
}
