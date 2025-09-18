// Generated with ChatGPT
export const useDownloadJson = () => {
  /**
   * Triggers a download of the given JSON data.
   * @param data The object/array to export as JSON.
   * @param filename Optional filename (default: backup-ISO-date.json)
   */
  const downloadJson = (data: unknown, filename?: string): void => {
    if (!data) {
      console.warn('No data provided for download')
      return
    }

    try {
      const jsonString = JSON.stringify(data, null, 2)
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url
      link.download = filename ?? `backup-${new Date().toISOString()}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download JSON:', err)
    }
  }

  return { downloadJson }
}
