import type { Asset, MovieProject } from '../utils/movie-script-evaluator.d.ts'
import { useMovieScriptEvaluatorApi } from './api/movieScriptEvaluatorApi.js'

export function useMovieScriptEvaluator() {
  const movieScriptAPI = useMovieScriptEvaluatorApi()

  function useProjects() {
    return useCrudWithAuthentication<MovieProject>('movie-script-evaluator/')
  }

  function useAssets(projectId: string) {
    return useCrudWithAuthentication<Asset>('movie-script-evaluator/' + projectId + '/assets/')
  }

  async function useUploadFile(projectId: string, file: File) {
    return await movieScriptAPI.uploadFile(projectId, file)
  }

  return {
    useProjects,
    useAssets,
    useUploadFile,
  }
}
