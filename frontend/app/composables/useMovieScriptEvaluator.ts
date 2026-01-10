import type {
  Asset,
  AssetListAnalysis,
  MovieProject,
  MovieScript,
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

  async function useAnalyzeMovieScript(projectId: string): Promise<AssetListAnalysis> {
    return await movieScriptAPI.analyzeMovieScript(projectId)
  }

  return {
    ...movieScriptProjects,
    uploadMovieScript,
    useAssets,
    useAnalyzeMovieScript,
    useMovieScript,
  }
}
