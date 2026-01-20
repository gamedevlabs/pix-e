import type {
  MovieScript,
  MovieScriptAnalysisResponse,
  ScriptSceneAnalysis,
} from '~/utils/movie-script-evaluator'

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

  async function analyzeMovieScript(
    projectId: string,
    script_id: number,
  ): Promise<MovieScriptAnalysisResponse> {
    try {
      return await $fetch(`${apiBase}/projects/${projectId}/analyze?script_id=${script_id}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
    } catch (error) {
      throw new Error((error as Error)?.message || 'Failed to analyze movie script')
    }
  }

  async function createScriptSceneAnalysisBulk(
    projectId: string,
    items: ScriptSceneAnalysis[],
  ): Promise<ScriptSceneAnalysis[]> {
    try {
      return await $fetch(`${apiBase}/projects/${projectId}/script-scene-analysis/`, {
        method: 'POST',
        body: items,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
    } catch (error) {
      throw new Error((error as Error)?.message || 'Failed to create script scene analysis items')
    }
  }

  return {
    createScriptSceneAnalysisBulk,
    uploadFile,
    analyzeMovieScript,
  }
}
