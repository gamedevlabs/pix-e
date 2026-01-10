import type { AssetListAnalysis, MovieScript } from '~/utils/movie-script-evaluator'

export function useMovieScriptEvaluatorApi() {
  const config = useRuntimeConfig()
  const apiBase = `${config.public.apiBase}/movie-script-evaluator`

  async function uploadFile(projectId: string, movieScriptFile: MovieScript) {
    try {
      const formData = new FormData()
      formData.append('title', movieScriptFile.title)
      formData.append('project', projectId)
      formData.append('file', movieScriptFile.file)

      return await $fetch(`${apiBase}/projects/${projectId}/script/`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
    } catch (error) {
      console.error('Error fetching: ', error)
      throw error
    }
  }

  async function analyzeMovieScript(projectId: string): Promise<AssetListAnalysis> {
    return await $fetch(`${apiBase}/projects/${projectId}/analyze`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  return {
    uploadFile,
    analyzeMovieScript,
  }
}
