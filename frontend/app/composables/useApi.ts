import { useSessionLog } from '~/composables/useSessionLog'

export const useApi = () => {
  const config = useRuntimeConfig()
  const csrfToken = useCookie('csrftoken')
  const headers = useRequestHeaders(['cookie'])
  const baseURL = import.meta.server
    ? config.apiUrl || 'http://backend-dev:8000'
    : config.public.apiBase

  const { addLog, getSessionId } = useSessionLog()

  const apiFetch = $fetch.create({
    baseURL: baseURL as string,
    onResponseError({ request, response }) {
      console.error('API Error (call: ' + baseURL + '):', response.status, response._data)

      addLog('error', 'api_error', {
        request: String(request),
        status: response.status,
        hasResponseData: Boolean(response._data),
      })
    },
    headers: headers as HeadersInit,

    onRequest({ options }) {
      options.headers = new Headers(options.headers || {})
      const sessionId = getSessionId()
      if (sessionId) {
        options.headers.set('X-Pixe-Session-Id', sessionId)
      }

      if (csrfToken.value) {
        options.headers.set('X-CSRFToken', csrfToken.value)
      }
    },
  })

  const apiFetchStream = async (
    path: string,
    options: RequestInit = {},
  ): Promise<ReadableStream<Uint8Array>> => {
    const mergedHeaders = new Headers(headers as HeadersInit)
    if (options.headers) {
      new Headers(options.headers).forEach((value, key) => {
        mergedHeaders.set(key, value)
      })
    }
    const sessionId = getSessionId()
    if (sessionId) {
      mergedHeaders.set('X-Pixe-Session-Id', sessionId)
    }
    if (csrfToken.value) {
      mergedHeaders.set('X-CSRFToken', csrfToken.value)
    }

    const response = await fetch(`${baseURL}${path}`, {
      ...options,
      headers: mergedHeaders,
    })

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown Error')
      console.error('API Stream Error (call: ' + baseURL + path + '):', response.status, errorText)
      throw new Error(`Stream failed with status ${response.status}`)
    }

    if (!response.body) {
      throw new Error('Response body is not readable')
    }

    return response.body
  }

  return {
    apiFetch,
    apiFetchStream,
    baseURL,
  }
}
