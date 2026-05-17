import { useSessionLog } from '~/composables/useSessionLog'

/*
  Used for logging browser session events.
 */

export default defineNuxtPlugin((nuxtApp) => {
  const { addLog } = useSessionLog()

  // logs page swap
  nuxtApp.hook('page:finish', () => {
    addLog('info', 'page_changed', {
      path: window.location.pathname,
      query: window.location.search,
    })
  })

  // log unhandled javascript errors
  window.addEventListener('error', (event) => {
    addLog('error', 'frontend_error', {
      message: event.message,
      source: event.filename,
      line: event.lineno,
      column: event.colno,
    })
  })

  // log unhandled async/promise errors
  window.addEventListener('unhandledrejection', (event) => {
    addLog('error', 'unhandled_rejection', {
      reason: String(event.reason),
    })
  })
})
