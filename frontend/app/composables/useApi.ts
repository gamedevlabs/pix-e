export const useApi = () => {
  const config = useRuntimeConfig()
  const csrfToken = useCookie('csrftoken')
  const headers = useRequestHeaders(['cookie'])
  const baseURL = import.meta.server
    ? config.apiUrl || 'http://backend-dev:8000'
    : config.public.apiBase

  const apiFetch = $fetch.create({
    baseURL: baseURL as string,
    onResponseError({ response }) {
      console.error('API Error:', response.status, response._data)
    },
    headers: headers as HeadersInit,

    onRequest({ options }) {
      options.headers = new Headers(options.headers || {})

      if (csrfToken.value) {
        options.headers.set('X-CSRFToken', csrfToken.value)
      }
    },
  })

  return {
    apiFetch,
    baseURL,
  }
}
