import type {
  ScriptSceneAnalysis,
  Asset,
  MovieProject,
  MovieScript,
  MovieScriptAnalysisResponse,
} from '../utils/movie-script-evaluator.d.ts'
import { useMovieScriptEvaluatorApi } from './api/movieScriptEvaluatorApi.js'

export function useMovieScriptEvaluator() {
  const movieScriptAPI = useMovieScriptEvaluatorApi()
  const movieScriptProjects = useCrudWithAuthentication<MovieProject>(
    'movie-script-evaluator/projects/',
  )

  function useAssets(projectId: string) {
    return useCrudWithAuthentication<Asset>(
      'movie-script-evaluator/projects/' + projectId + '/assets/',
    )
  }

  function uploadMovieScript(projectId: string, movieScriptFile: MovieScript) {
    return movieScriptAPI.uploadFile(projectId, movieScriptFile)
  }

  function useMovieScript(projectId: string) {
    return useCrudWithAuthentication<MovieScript>(
      'movie-script-evaluator/projects/' + projectId + '/script/',
    )
  }

  async function useAnalyzeMovieScript(projectId: string, script_id: number): Promise<MovieScriptAnalysisResponse> {
    return await movieScriptAPI.analyzeMovieScript(projectId, script_id)
  }

  function useScriptSceneAssetAnalysis(projectId: string) {
    return useCrudWithAuthentication<ScriptSceneAnalysis>(
      'movie-script-evaluator/projects/' + projectId + '/script-scene-analysis/',
    )
  }

  return {
    ...movieScriptProjects,
    uploadMovieScript,
    useAssets,
    useAnalyzeMovieScript,
    useMovieScript,
    useScriptSceneAssetAnalysis
  }
}
