import type { Asset } from "../utils/movie-script-evaluator.d.ts";

export function useMovieScriptEvaluator() {
    return useCrudWithAuthentication<Asset>('movie-script-evaluator')
}