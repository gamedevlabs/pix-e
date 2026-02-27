import type {
  MovieScript,
  MovieScriptAnalysisResponse,
  ScriptSceneAnalysis,
} from '~/utils/movie-script-evaluator'
import { useProjectDataProvider } from '~/studyMock'

export function useMovieScriptEvaluatorApi() {
  // Upload: store script metadata + file content locally in mock store
  async function uploadFile(projectId: string, movieScriptFile: MovieScript) {
    try {
      const provider = useProjectDataProvider()
      // Read file content as text so we can store and later analyze it
      const content = await movieScriptFile.file.text()
      return await provider.createEntity(`movie-script-evaluator:projects:${projectId}:script`, {
        title: movieScriptFile.title,
        project: projectId,
        content,
      })
    } catch (error) {
      console.error('Error uploading script: ', error)
      throw error
    }
  }

  // Analyze: read script content from mock store and call Nuxt LLM server route
  async function analyzeMovieScript(
    projectId: string,
    script_id: number,
  ): Promise<MovieScriptAnalysisResponse> {
    try {
      const provider = useProjectDataProvider()
      const scripts = await provider.getEntities(
        `movie-script-evaluator:projects:${projectId}:script`,
      )
      const script = scripts.find(
        (s) => String((s as Record<string, unknown>).id) === String(script_id),
      ) as Record<string, unknown> | undefined

      if (!script) throw new Error('Script not found in local store')

      const scriptContent = (script.content as string) ?? ''

      return await $fetch<MovieScriptAnalysisResponse>('/api/llm/movie-script/analyze', {
        method: 'POST',
        body: { scriptContent },
      })
    } catch (error) {
      throw new Error((error as Error)?.message || 'Failed to analyze movie script')
    }
  }

  // Store scene analysis results locally
  async function createScriptSceneAnalysisBulk(
    projectId: string,
    items: ScriptSceneAnalysis[],
  ): Promise<ScriptSceneAnalysis[]> {
    try {
      const provider = useProjectDataProvider()
      const collection = `movie-script-evaluator:projects:${projectId}:script-scene-analysis`
      const results: ScriptSceneAnalysis[] = []
      for (const item of items) {
        const created = await provider.createEntity(
          collection,
          item as unknown as Record<string, unknown>,
        )
        results.push(created as unknown as ScriptSceneAnalysis)
      }
      return results
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
