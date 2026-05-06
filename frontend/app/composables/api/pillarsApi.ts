/**
 * Composable providing LLM-powered design pillar API calls.
 * Automatically injects the selected model and optional api_key_id into each request.
 */
export function usePillarsApi() {
  const config = useRuntimeConfig()
  const llm = useLLM()

  /**
   * Build the shared request body with the active model and (optionally)
   * the selected personal API key ID. Merges any additional fields.
   * @param extra - Additional fields to merge into the body.
   * @returns Object with model, optional api_key_id, and extra fields.
   */
  function buildBody(extra: Record<string, unknown> = {}) {
    return {
      model: llm.activeModelName,
      ...(llm.activeKeyId ? { api_key_id: llm.activeKeyId } : {}),
      ...extra,
    }
  }

  /**
   * Update the current design idea via the LLM.
   * @param designIdea - The design idea text to send.
   */
  async function updateDesignIdeaAPICall(designIdea: string) {
    if (designIdea.trim() === '') return
    try {
      await sessionFetch(config.public.apiBase + '/api/llm/design/', {
        method: 'PUT',
        body: { description: designIdea.trim() },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
    } catch (error) {
      console.error('Error fetching:', error)
    }
  }

  /**
   * Get overall pillars-in-context feedback from the LLM.
   * @returns Feedback assessing how well pillars fit the design context.
   */
  async function getPillarsInContextAPICall() {
    return await sessionFetch<PillarsInContextFeedback>(
      config.public.apiBase + '/api/llm/feedback/overall/',
      {
        method: 'POST',
        body: buildBody(),
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  /**
   * Get contradiction analysis between pillars from the LLM.
   * @returns Feedback highlighting conflicting pillar definitions.
   */
  async function getPillarsContradictionsAPICall() {
    return await sessionFetch<PillarContradictionsFeedback>(
      config.public.apiBase + '/api/llm/feedback/contradictions/',
      {
        method: 'POST',
        body: buildBody(),
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  /**
   * Get completeness analysis of the pillar set from the LLM.
   * @returns Feedback identifying gaps in pillar coverage.
   */
  async function getPillarsCompletenessAPICall() {
    return await sessionFetch<PillarCompletenessFeedback>(
      config.public.apiBase + '/api/llm/feedback/completeness/',
      {
        method: 'POST',
        body: buildBody(),
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  /**
   * Get suggested pillar additions from the LLM.
   * @returns Feedback recommending new pillars to add.
   */
  async function getPillarsAdditionsAPICall() {
    return await sessionFetch<PillarAdditionsFeedback>(
      config.public.apiBase + '/api/llm/feedback/additions/',
      {
        method: 'POST',
        body: buildBody(),
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  /**
   * Validate a single pillar against the design idea via the LLM.
   * Sets `llm_feedback` on the pillar object in-place.
   * @param pillar - The pillar to validate (mutated with feedback).
   */
  async function validatePillarAPICall(pillar: Pillar) {
    pillar.llm_feedback = await sessionFetch<PillarFeedback>(
      config.public.apiBase + `/api/llm/pillars/${pillar.id}/validate/`,
      {
        method: 'POST',
        body: buildBody(),
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  /**
   * Request an AI-generated fix/revision for a pillar.
   * @param pillar - The pillar to fix.
   * @returns Updated PillarDTO with AI-suggested changes.
   */
  async function fixPillarWithAIAPICall(pillar: Pillar) {
    return await sessionFetch<PillarDTO>(
      config.public.apiBase + `/api/llm/pillars/${pillar.id}/fix/`,
      {
        method: 'POST',
        body: buildBody(),
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  /**
   * Evaluate how well a given context string fits within the existing pillars.
   * @param context - The external context text to assess.
   * @returns Feedback on context-pillar alignment.
   */
  async function getContextInPillarsAPICall(context: string) {
    return await sessionFetch<ContextInPillarsFeedback>(
      config.public.apiBase + '/api/llm/feedback/context/',
      {
        method: 'POST',
        body: buildBody({ context }),
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  return {
    updateDesignIdeaAPICall,
    validatePillarAPICall,
    getPillarsInContextAPICall,
    getPillarsContradictionsAPICall,
    getPillarsCompletenessAPICall,
    getPillarsAdditionsAPICall,
    fixPillarWithAIAPICall,
    getContextInPillarsAPICall,
  }
}
