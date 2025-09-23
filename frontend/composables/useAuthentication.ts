export function useAuthentication() {
  const user = useState<User | null>('auth-user', () => null)
  const isLoggedIn = computed(() => user.value !== null)
  const checkedLogin = useState<boolean>('checkedLogin', () => false)
  const router = useRouter()
  const config = useRuntimeConfig()

  async function register(username: string, password: string): Promise<boolean> {
    try {
      await $fetch(`${config.public.apiBase}/accounts/register/`, {
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
      await $fetch(`${config.public.apiBase}/accounts/login/`, {
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

  async function checkAuthentication(): Promise<boolean> {
    try {
      checkedLogin.value = true

      const userData = await $fetch<User>(`${config.public.apiBase}/accounts/me/`, {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })

      user.value = userData
      return true
    } catch {
      user.value = null // Handling the exception more precise requires dancing around the ESLinter and Vues internal ruleset
      // which would not even remove the console error on the 401 Unauthorized
      // Rules: ESLint: no-explicit-any, vue: catch-only-any-or-unknown
      return false
    }
  }

  async function logout(): Promise<boolean> {
    try {
      await $fetch(`${config.public.apiBase}/accounts/logout/`, {
        method: 'POST',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
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
