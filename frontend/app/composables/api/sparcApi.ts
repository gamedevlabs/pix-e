export function useSparcApi() {
  const config = useRuntimeConfig()
  const llm = useLLM()

  async function runQuickScanAPICall(gameText: string, context: string = '') {
    return await $fetch<SPARCQuickScanResponse>(`${config.public.apiBase}/sparc/quick-scan/`, {
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
    return await $fetch<SPARCMonolithicResponse>(`${config.public.apiBase}/sparc/monolithic/`, {
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
    return await $fetch<GameConcept>(`${config.public.apiBase}/game-concept/current/`, {
      method: 'GET',
      credentials: 'include',
      headers: useRequestHeaders(['cookie']),
    })
  }

  async function updateGameConceptAPICall(content: string) {
    return await $fetch<GameConcept>(`${config.public.apiBase}/game-concept/update_current/`, {
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
    return await $fetch<SPARCEvaluation[]>(`${config.public.apiBase}/sparc/evaluations/`, {
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
