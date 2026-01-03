import type { Asset, AssetListAnalysis, MovieProject } from '../utils/movie-script-evaluator.d.ts'
import { useMovieScriptEvaluatorApi } from './api/movieScriptEvaluatorApi.js'

export function useMovieScriptEvaluator() {
  const movieScriptAPI = useMovieScriptEvaluatorApi()
  const movieScriptProjects = useCrudWithAuthentication<MovieProject>('movie-script-evaluator/')

  function useAssets(projectId: string) {
    return useCrudWithAuthentication<Asset>('movie-script-evaluator/' + projectId + '/assets/')
  }

  async function useUploadFile(projectId: string, file: File) {
    return await movieScriptAPI.uploadFile(projectId, file)
  }

  async function useAnalyzeMovieScript(projectId: string): Promise<AssetListAnalysis> {
    return await movieScriptAPI.analyzeMovieScript(projectId)
  }

  return {
    ...movieScriptProjects,
    useAssets,
    useAnalyzeMovieScript,
    useUploadFile,
  }
}
