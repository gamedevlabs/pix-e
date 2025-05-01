export function useAnonCookie() {
  const cookieName = 'anon_id'

  if (import.meta.client) {
    const cookie = useCookie(cookieName)
    if (!cookie.value) {
      console.log('creating new cookie')
      const id = crypto.randomUUID()
      useCookie(cookieName, {
        default: () => id,
        maxAge: 60 * 60 * 24 * 365, // 1 year
        sameSite: 'lax',
      })
    }
  }
}
