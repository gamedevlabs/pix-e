import { useApi } from './useApi'

export function useAuthentication() {
  const { apiFetch } = useApi()
  const user = useState<User | null>('auth-user', () => null)
  const isLoggedIn = computed(() => user.value !== null)
  const checkedLogin = useState<boolean>('checkedLogin', () => false)
  const router = useRouter()
  const { addLog } = useSessionLog()

  async function register(username: string, password: string): Promise<boolean> {
    // log registration start
    addLog('info', 'registration_started')
    try {
      await apiFetch('/api/accounts/register/', {
        method: 'POST',
        body: { username: username, password: password },
        credentials: 'include',
      })
      return await login(username, password)
    } catch {
      // log registration fail
      addLog('error', 'registration_failed')
      return false
    }
  }

  async function login(username: string, password: string): Promise<boolean> {
    // log login start
    addLog('info', 'login_started')
    try {
      await apiFetch('/api/accounts/login/', {
        method: 'POST',
        body: { username: username, password: password },
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      const success = await checkAuthentication()
      if (!success) {
        // log login fail
        addLog('info', 'login_failed', {
          message: 'Authentication failed.',
        })
        return false
      }
      const route = useRoute()
      const redirectTo = (route.query.redirect as string) || '/'
      await router.push(redirectTo)
      // log login success
      addLog('info', 'login_succeeded')
      return true
    } catch {
      // log login fail
      addLog('error', 'login_failed', {
        message: 'An error occurred.',
      })
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
    // log logout start
    addLog('info', 'logout_started')
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
      // log logout start
      addLog('info', 'logout_succeeded')
      return true
    } catch {
      // log logout start
      addLog('error', 'logout_failed', {
        message: 'An error occurred.',
      })
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
