export function useAuthentication() {
  const config = useRuntimeConfig()
  const user = useState<User | null>('auth-user', () => null)
  const isLoggedIn = computed(() => user.value !== null)
  const checkedLogin = useState<boolean>('checkedLogin', () => false)
  const router = useRouter()

  async function register(username: string, password: string): Promise<boolean> {
    try {
      await $fetch(config.public.apiBase + '/api/accounts/register/', {
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
      await $fetch(config.public.apiBase + '/api/accounts/login/', {
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

  let authPromise: Promise<boolean> | null = null

  async function checkAuthentication(): Promise<boolean> {
    if (checkedLogin.value) {
      return !!user.value
    }

    if (authPromise) {
      return authPromise
    }

    authPromise = (async () => {
      try {
        user.value = await $fetch<User>(
          config.public.apiBase + '/api/accounts/me/',
          {
            method: 'GET',
            credentials: 'include',
            headers: import.meta.server
              ? useRequestHeaders(['cookie'])
              : undefined,
          },
        )
        return true
      } catch {
        user.value = null
        return false
      } finally {
        checkedLogin.value = true
        authPromise = null
      }
    })()

    return authPromise
  }

  async function logout(): Promise<boolean> {
    try {
      await $fetch(config.public.apiBase + '/api/accounts/logout/', {
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
