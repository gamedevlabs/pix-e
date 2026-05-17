/*
  Used for handling session logging. Session logs can then be attached to bug reports by users
 */

// Definition of log entries
// consist of timestamp, severity level, event name, and optional metadata
type SessionLogEntry = {
  time: string
  level: 'info' | 'warn' | 'error'
  event: string
  data?: Record<string, unknown>
}

// used for sessionStorage -> cleared when tab/window is closed
const STORAGE_KEY = 'pixe-session-logs'
// limits amount of logs in storage at once
const MAX_LOGS = 150

export function useSessionLog() {
  // reads the current log list from sessionStorage.
  function readLogs(): SessionLogEntry[] {
    if (import.meta.server) return []

    try {
      return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]')
    } catch {
      return []
    }
  }

  // adds a new log entry
  // Example usages:
  // addLog('info', 'helpdesk_form_opened')
  // addLog('error', 'api_error', { status: 500 })
  function addLog(level: SessionLogEntry['level'], event: string, data = {}) {
    if (import.meta.server) return

    const logs = readLogs()

    logs.push({
      time: new Date().toISOString(),
      level,
      event,
      data,
    })

    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(logs.slice(-MAX_LOGS)))
  }

  // returns complete session log payload (can be attached to bug report)
  function getLogs() {
    if (import.meta.server) return null

    return {
      url: window.location.href, // current page where bug report was submitted
      userAgent: navigator.userAgent, // browser/system info
      logs: readLogs(), // recorded browser logs
    }
  }

  // clears current session logs
  function clearLogs() {
    if (import.meta.server) return
    sessionStorage.removeItem(STORAGE_KEY)
  }

  return { addLog, getLogs, clearLogs }
}