import type { Asset, MovieProject } from '../utils/movie-script-evaluator.d.ts'

export function useMovieScriptEvaluator() {
  return useCrudWithAuthentication<MovieProject>('movie-script-evaluator/')
}

export function useMovieScriptEvaluatorAssets(project_id: string) {
  return useCrudWithAuthentication<Asset>("movie-script-evaluator/"+project_id +"/assets/")
}