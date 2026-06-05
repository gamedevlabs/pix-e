import { useApi } from './useApi'

export function useAuthentication() {
  const { apiFetch } = useApi()
  const user = useState<User | null>('auth-user', () => null)
  const isLoggedIn = computed(() => user.value !== null)
  const checkedLogin = useState<boolean>('checkedLogin', () => false)
  const router = useRouter()

  async function register(username: string, password: string): Promise<boolean> {
    try {
      await apiFetch('/api/accounts/register/', {
        method: 'POST',
        body: { username: username, password: password },
        credentials: 'include',
      })
      return await login(username, password)
    } catch {
      return false
    }
  }

  async function login(username: string, password: string): Promise<boolean> {
    try {
      await apiFetch('/api/accounts/login/', {
        method: 'POST',
        body: { username: username, password: password },
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      const success = await checkAuthentication()
      if (!success) {
        return false
      }
      const route = useRoute()
      const redirectTo = (route.query.redirect as string) || '/'
      await router.push(redirectTo)
      return true
    } catch {
      return false
    }
  }

  //let authPromise: Promise<boolean> | null = null

  async function checkAuthentication(): Promise<boolean> {
    try {
      checkedLogin.value = true
      user.value = await apiFetch<User>('/api/accounts/me/', {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      return true
    } catch {
      user.value = null
      // Handling the exception more precise requires dancing around the ESLinter and Vues internal ruleset
      // which would not even remove the console error on the 401 Unauthorized
      // Rules: ESLint: no-explicit-any, vue: catch-only-any-or-unknown
      return false
    }
  }

  async function logout(): Promise<boolean> {
    try {
      await apiFetch('/api/accounts/logout/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      user.value = null
      await router.push('/')
      return true
    } catch {
      return false
    }
  }

  return {
    user,
    isLoggedIn,
    checkedLogin,
    register,
    login,
    checkAuthentication,
    logout,
  }
}
