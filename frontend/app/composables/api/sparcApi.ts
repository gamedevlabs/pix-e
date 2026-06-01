import { useApi } from '~/composables/useApi'

export function useSparcApi() {
  const { apiFetch } = useApi()
  const llm = useLLM()

  async function runQuickScanAPICall(gameText: string, context: string = '') {
    return await apiFetch<SPARCQuickScanResponse>(`/api/sparc/quick-scan/`, {
      method: 'POST',
      body: {
        game_text: gameText,
        context: context,
        model: llm.active_llm,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  async function runMonolithicAPICall(gameText: string, context: string = '') {
    return await apiFetch<SPARCMonolithicResponse>(`/api/sparc/monolithic/`, {
      method: 'POST',
      body: {
        game_text: gameText,
        context: context,
        model: llm.active_llm,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  async function getCurrentGameConceptAPICall() {
    return await apiFetch<GameConcept>(`/api/game-concept/current/`, {
      method: 'GET',
      credentials: 'include',
      headers: useRequestHeaders(['cookie']),
    })
  }

  async function updateGameConceptAPICall(content: string) {
    return await apiFetch<GameConcept>(`/api/game-concept/update_current/`, {
      method: 'POST',
      body: {
        content: content,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  async function getEvaluationsAPICall() {
    return await apiFetch<SPARCEvaluation[]>(`/api/sparc/evaluations/`, {
      method: 'GET',
      credentials: 'include',
      headers: useRequestHeaders(['cookie']),
    })
  }

  return {
    runQuickScanAPICall,
    runMonolithicAPICall,
    getCurrentGameConceptAPICall,
    updateGameConceptAPICall,
    getEvaluationsAPICall,
  }
}
