export interface ProgressEvent {
  stage: string
  message: string
  current?: number
  total?: number
}

export function useSparcV2Api() {
  const config = useRuntimeConfig()
  const llm = useLLM()

  async function runV2EvaluateAPICall(
    gameText: string,
    context: string = '',
    pillarMode: PillarMode = 'filtered',
  ) {
    return await $fetch<SPARCV2Response>(`${config.public.apiBase}/sparc/v2/evaluate/`, {
      method: 'POST',
      body: {
        game_text: gameText,
        context: context,
        model: llm.active_llm,
        pillar_mode: pillarMode,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  async function runV2EvaluateStreamAPICall(
    gameText: string,
    context: string = '',
    pillarMode: PillarMode = 'filtered',
    onProgress: (event: ProgressEvent) => void,
    onComplete: (result: SPARCV2Response) => void,
    onError: (error: string) => void,
  ) {
    const url = `${config.public.apiBase}/sparc/v2/evaluate-stream/`

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': useCookie('csrftoken').value || '',
        },
        credentials: 'include',
        body: JSON.stringify({
          game_text: gameText,
          context: context,
          model: llm.active_llm,
          pillar_mode: pillarMode,
        }),
      })

      if (!response.body) {
        onError('No response body')
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue

          const [eventLine, dataLine] = line.split('\n')
          if (!eventLine || !dataLine) continue

          const eventType = eventLine.replace('event: ', '').trim()
          const data = dataLine.replace('data: ', '').trim()

          if (!data) continue

          try {
            const parsedData = JSON.parse(data)

            if (eventType === 'progress') {
              onProgress(parsedData as ProgressEvent)
            } else if (eventType === 'complete') {
              onComplete(parsedData as SPARCV2Response)
            } else if (eventType === 'error') {
              onError(parsedData.message || 'Evaluation failed')
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e)
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Connection error')
    }
  }

  async function runV2AspectAPICall(
    gameText: string,
    aspect: SPARCV2AspectName,
    context: string = '',
  ) {
    return await $fetch<SPARCV2Response>(`${config.public.apiBase}/sparc/v2/evaluate/aspect/`, {
      method: 'POST',
      body: {
        game_text: gameText,
        aspect: aspect,
        context: context,
        model: llm.active_llm,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  async function runV2AspectsAPICall(
    gameText: string,
    aspects: SPARCV2AspectName[],
    context: string = '',
  ) {
    return await $fetch<SPARCV2Response>(`${config.public.apiBase}/sparc/v2/evaluate/aspects/`, {
      method: 'POST',
      body: {
        game_text: gameText,
        aspects: aspects,
        context: context,
        model: llm.active_llm,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  return {
    runV2EvaluateAPICall,
    runV2EvaluateStreamAPICall,
    runV2AspectAPICall,
    runV2AspectsAPICall,
  }
}
