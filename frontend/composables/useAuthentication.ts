export function useAuthentication() {
  const userId = useState<number | null>('auth-user-id', () => null)
  const username = useState<string | null>('auth-username', () => null)
  const error = ref('')

  async function register(username: string, password: string) {
    error.value = ''
    try {
      await $fetch('http://localhost:8000/accounts/register/', {
        method: 'POST',
        body: { username: username, password: password },
        credentials: 'include',
      })
      await login(username, password)
    } catch {
      error.value = 'Registration failed.'
    }
  }

  async function login(username: string, password: string) {
    error.value = ''
    try {
      await $fetch('http://localhost:8000/accounts/login/', {
        method: 'POST',
        body: { username: username, password: password },
        credentials: 'include',
      })
      await checkAuth()
    } catch {
      error.value = 'Login failed.'
    }
  }

  async function checkAuth() {
    try {
      const res = await $fetch<{ id: number; username: string }>(
        'http://localhost:8000/accounts/me/',
        {
          credentials: 'include',
        },
      )
      userId.value = res.id
      username.value = res.username
    } catch {
      error.value = 'Not logged in'
      userId.value = null
    }
  }

  async function logout() {
    error.value = ''
    try {
      await $fetch('http://localhost:8000/accounts/logout/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      userId.value = null
    } catch {
      error.value = 'Logout failed.'
    }
  }

  return {
    userId,
    error,
    username,
    register,
    login,
    checkAuth,
    logout,
  }
}
