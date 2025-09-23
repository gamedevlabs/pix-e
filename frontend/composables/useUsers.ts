interface User {
  id: number
  username: string
}

export function useUsers() {
  const config = useRuntimeConfig()
  
  async function fetchUsers(): Promise<User[]> {
    try {
      const response = await $fetch(`${config.public.apiBase}/accounts/users/`, {
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      
      return (response as { users: User[] }).users || []
    } catch (error) {
      console.error('❌ Error fetching users:', error)
      throw error
    }
  }
  
  return {
    fetchUsers
  }
}
