import type {
  MovieScript,
  MovieScriptAnalysisResponse,
  ScriptSceneAnalysis,
} from '~/utils/movie-script-evaluator'
import { useApi } from '~/composables/useApi'

export function useMovieScriptEvaluatorApi() {
  const { apiFetch } = useApi()
  const llm = useLLM()

  async function uploadFile(projectId: string, movieScriptFile: MovieScript) {
    try {
      const formData = new FormData()
      formData.append('title', movieScriptFile.title)
      formData.append('project', projectId)
      formData.append('file', movieScriptFile.file)

      return await apiFetch(`/api/movie-script-evaluator/projects/${projectId}/script/`, {
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
      const params = new URLSearchParams({
        script_id: String(script_id),
      })
      if (llm.activeKeyId) {
        params.set('api_key_id', llm.activeKeyId)
      }

      return await apiFetch(
        `/api/movie-script-evaluator/projects/${projectId}/analyze?${params.toString()}`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            'X-CSRFToken': useCookie('csrftoken').value,
          } as HeadersInit,
        },
      )
    } catch (error) {
      throw new Error((error as Error)?.message || 'Failed to analyze movie script', {
        cause: error,
      })
    }
  }

  async function createScriptSceneAnalysisBulk(
    projectId: string,
    items: ScriptSceneAnalysis[],
  ): Promise<ScriptSceneAnalysis[]> {
    try {
      return await apiFetch(
        `/api/movie-script-evaluator/projects/${projectId}/script-scene-analysis/`,
        {
          method: 'POST',
          body: items,
          credentials: 'include',
          headers: {
            'X-CSRFToken': useCookie('csrftoken').value,
          } as HeadersInit,
        },
      )
    } catch (error) {
      throw new Error((error as Error)?.message || 'Failed to create script scene analysis items', {
        cause: error,
      })
    }
  }

  return {
    createScriptSceneAnalysisBulk,
    uploadFile,
    analyzeMovieScript,
  }
}
