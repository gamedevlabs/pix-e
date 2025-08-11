import { ref, computed } from 'vue'
import { useRuntimeConfig } from '#imports'

interface AISuggestion {
  text: string
  applied: boolean
}

interface AIService {
  id: string
  name: string
  status: 'available' | 'unavailable' | 'loading'
}

interface SuggestionResponse {
  status: string
  suggestions?: string[]
  error?: string
  prompt?: string
  service_used?: string
}

interface Service {
  id: string
  name?: string
  status: string
  description?: string
  available?: boolean
}

interface ServicesResponse {
  status: string
  services?: Record<string, Service>
  active_service?: string
}

interface UserToken {
  id: string
  service_type: string
  created_at: string
  updated_at: string
}

interface APIError {
  message?: string
  data?: {
    error?: string
    detail?: string
  }
  statusCode?: number
  response?: {
    data?: {
      error?: string
      detail?: string
    }
  }
}

export const useAISuggestions = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase || 'http://localhost:8000'

  // Helper function to extract error message
  const getErrorMessage = (error: unknown, fallback: string): string => {
    const apiError = error as APIError
    return apiError.data?.error || apiError.message || fallback
  }

  // State
  const suggestions = ref<AISuggestion[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const services = ref<AIService[]>([])
  const activeService = ref<string | null>(null)

  // Token management state
  const userTokens = ref<UserToken[]>([])
  const isTokensLoading = ref(false)
  const tokenError = ref<string | null>(null)

  // UI State
  const isVisible = ref(false)
  const mode = ref<'default' | 'gaming'>('default')
  const suggestionType = ref<'short' | 'long'>('short')
  const lastPrompt = ref('')

  // Computed
  const hasUntriedSuggestions = computed(() => 
    suggestions.value.some(s => !s.applied)
  )

  const appliedSuggestionsCount = computed(() =>
    suggestions.value.filter(s => s.applied).length
  )

  const totalSuggestions = computed(() =>
    suggestions.value.length
  )

  // Clear error state
  const clearError = () => {
    error.value = null
  }

  // Clear state
  const clearSuggestions = () => {
    suggestions.value = []
    error.value = null
    lastPrompt.value = ''
  }

  // Validate prompt without showing error
  const isValidPrompt = (prompt: string): boolean => {
    return !!(prompt?.trim() && prompt.trim().length >= 3)
  }

  // Generate AI suggestions
  const generateSuggestions = async (prompt: string, options: {
    numSuggestions?: number
    serviceId?: string
    mode?: 'default' | 'gaming'
    suggestionType?: 'short' | 'long'
    skipValidation?: boolean
  } = {}) => {
    
    if (!options.skipValidation) {
      if (!prompt?.trim()) {
        error.value = 'Please enter a prompt to generate suggestions'
        return
      }
      
      if (prompt.trim().length < 3) {
        error.value = 'Prompt must be at least 3 characters long'
        return
      }
    }

    loading.value = true
    error.value = null
    lastPrompt.value = prompt

    try {
      const csrfToken = useCookie('csrftoken').value
      const requestBody = {
        prompt: prompt.trim(),
        service: options.serviceId || activeService.value,
        num_suggestions: options.numSuggestions || 3,
        mode: options.mode || mode.value,
        suggestion_type: options.suggestionType || suggestionType.value
      }
      
      const response = await $fetch<SuggestionResponse>(`${apiBase}/api/llm/text-suggestions/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken && { 'X-CSRFToken': csrfToken }),
          ...useRequestHeaders(['cookie'])
        },
        body: requestBody
      })

      if (response.status === 'success' && response.suggestions) {
        suggestions.value = response.suggestions.map((text: string) => ({
          text: text.trim(),
          applied: false
        }))
      } else {
        throw new Error(response.error || 'Failed to generate suggestions')
      }

    } catch (err: unknown) {
      const apiError = err as APIError
      
      // Log error for debugging in development only
      if (process.env.NODE_ENV === 'development') {
        console.error('Error generating suggestions:', err)
      }
      
      // Set appropriate error message based on the error type
      if ((apiError as APIError).statusCode === 401 || (apiError as APIError).statusCode === 403) {
        error.value = 'Authentication required. Please log in to use AI suggestions.'
      } else if ((apiError as APIError).statusCode === 400 && (apiError as APIError).data?.error?.includes('token')) {
        error.value = 'API token required. Please configure your API tokens in the AI suggestions panel.'
      } else if ((apiError as APIError).data?.error?.includes('service not available')) {
        error.value = 'AI service is currently unavailable. Please check your API token configuration or try again later.'
      } else {
        error.value = (apiError as APIError).data?.error || (apiError as APIError).message || 'AI service failed. Please check your API token configuration.'
      }
      
      // Clear suggestions instead of showing fallback
      suggestions.value = []
    } finally {
      loading.value = false
    }
  }

  // Apply a suggestion to the prompt
  const applySuggestion = (index: number, currentPrompt: string): string => {
    if (index < 0 || index >= suggestions.value.length) return currentPrompt

    const suggestion = suggestions.value[index]
    if (!suggestion || suggestion.applied) return currentPrompt

    suggestion.applied = true

    // Smart suggestion application
    const cleanPrompt = currentPrompt.trim()
    const cleanSuggestion = suggestion.text.trim()

    // If suggestion starts with the original prompt, replace entirely
    if (cleanSuggestion.toLowerCase().startsWith(cleanPrompt.toLowerCase())) {
      return cleanSuggestion
    }

    // If prompt ends with punctuation, replace it
    if (cleanPrompt.endsWith('.') || cleanPrompt.endsWith(',') || cleanPrompt.endsWith(';')) {
      return `${cleanPrompt.slice(0, -1)}, ${cleanSuggestion}`
    }

    // Otherwise, append with comma
    return cleanPrompt ? `${cleanPrompt}, ${cleanSuggestion}` : cleanSuggestion
  }

  // Remove/unapply a suggestion
  const unapplySuggestion = (index: number) => {
    if (index >= 0 && index < suggestions.value.length && suggestions.value[index]) {
      suggestions.value[index].applied = false
    }
  }

  // Get available AI services
  const fetchServices = async () => {
    try {
      const response = await $fetch<ServicesResponse>(`${apiBase}/api/llm/llm-services/`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          ...useRequestHeaders(['cookie'])
        }
      })

      if (response.status === 'success') {
        services.value = Object.entries(response.services || {}).map(([id, service]: [string, Service]) => ({
          id,
          name: service.name || id,
          status: service.available ? 'available' : 'unavailable'
        }))
        activeService.value = response.active_service || services.value[0]?.id || null
      }
    } catch (err) {
      console.error('Error fetching AI services:', err)
    }
  }

  // Toggle panel visibility
  const togglePanel = () => {
    isVisible.value = !isVisible.value
  }

  const showPanel = () => {
    isVisible.value = true
  }

  const hidePanel = () => {
    isVisible.value = false
  }

  // Set mode
  const setMode = (newMode: 'default' | 'gaming') => {
    mode.value = newMode
  }

  // Set suggestion type
  const setSuggestionType = (type: 'short' | 'long') => {
    suggestionType.value = type
  }

  // Set active service
  const setActiveService = (serviceId: string | null) => {
    activeService.value = serviceId
  }

  // Token management methods
  const fetchUserTokens = async () => {
    isTokensLoading.value = true
    tokenError.value = null
    
    try {
      const response = await $fetch<UserToken[]>(`${apiBase}/api/accounts/ai-tokens/`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          ...useRequestHeaders(['cookie'])
        }
      })
      
      userTokens.value = Array.isArray(response) ? response : []
    } catch (err: unknown) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching user tokens:', err)
      }
      tokenError.value = getErrorMessage(err, 'Failed to fetch tokens')
    } finally {
      isTokensLoading.value = false
    }
  }

  const saveUserToken = async (serviceType: string, token: string, isActive: boolean = true) => {
    try {
      // First check if a token already exists for this service
      const existingToken = userTokens.value.find(t => t.service_type === serviceType)
      
      if (existingToken) {
        console.log('Token already exists for this service, updating instead...')
        return await updateUserToken(serviceType, token, isActive)
      }
      
      const csrfToken = useCookie('csrftoken').value
      
      const response = await $fetch<{ success: boolean; token?: UserToken }>(`${apiBase}/api/accounts/ai-tokens/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken && { 'X-CSRFToken': csrfToken }),
          ...useRequestHeaders(['cookie'])
        },
        body: {
          service_type: serviceType,
          token: token,
          is_active: isActive
        }
      })
      
      // Refresh tokens list
      await fetchUserTokens()
      return response
    } catch (err: unknown) {
      const apiError = err as APIError
      
      // Fallback: If token already exists and we missed it above, try updating
      if (apiError.statusCode === 400 && apiError.data?.error?.includes('already exists')) {
        console.log('Token already exists (fallback), updating instead...')
        return await updateUserToken(serviceType, token, isActive)
      }
      
      if (process.env.NODE_ENV === 'development') {
        console.error('Error saving token:', err)
      }
      tokenError.value = getErrorMessage(err, 'Failed to save token')
      throw err
    }
  }

  const updateUserToken = async (serviceType: string, token: string, isActive?: boolean) => {
    try {
      const csrfToken = useCookie('csrftoken').value
      const body: Record<string, unknown> = { token }
      if (isActive !== undefined) {
        body.is_active = isActive
      }
      
      const response = await $fetch<{ success: boolean; token?: UserToken }>(`${apiBase}/api/accounts/ai-tokens/${serviceType}/`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken && { 'X-CSRFToken': csrfToken }),
          ...useRequestHeaders(['cookie'])
        },
        body
      })
      
      // Refresh tokens list
      await fetchUserTokens()
      return response
    } catch (err: unknown) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error updating token:', err)
      }
      tokenError.value = getErrorMessage(err, 'Failed to update token')
      throw err
    }
  }

  const deleteUserToken = async (serviceType: string) => {
    try {
      const csrfToken = useCookie('csrftoken').value
      
      await $fetch(`${apiBase}/api/accounts/ai-tokens/${serviceType}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          ...(csrfToken && { 'X-CSRFToken': csrfToken }),
          ...useRequestHeaders(['cookie'])
        }
      })
      
      // Refresh tokens list
      await fetchUserTokens()
    } catch (err: unknown) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error deleting token:', err)
      }
      tokenError.value = getErrorMessage(err, 'Failed to delete token')
      throw err
    }
  }

  // Regenerate suggestions with same prompt
  const regenerateSuggestions = async (options?: {
    numSuggestions?: number
    serviceId?: string
  }) => {
    if (lastPrompt.value) {
      await generateSuggestions(lastPrompt.value, {
        ...options,
        mode: mode.value,
        suggestionType: suggestionType.value
      })
    }
  }

  return {
    // State
    suggestions,
    loading,
    error,
    services,
    activeService,
    
    // Token management state
    userTokens,
    isTokensLoading,
    tokenError,
    
    // UI State
    isVisible,
    mode,
    suggestionType,
    lastPrompt,
    
    // Computed
    hasUntriedSuggestions,
    appliedSuggestionsCount,
    totalSuggestions,
    
    // Methods
    generateSuggestions,
    applySuggestion,
    unapplySuggestion,
    clearSuggestions,
    clearError,
    fetchServices,
    regenerateSuggestions,
    isValidPrompt,
    
    // Token management methods
    fetchUserTokens,
    saveUserToken,
    updateUserToken,
    deleteUserToken,
    
    // Panel control
    togglePanel,
    showPanel,
    hidePanel,
    
    // Settings
    setMode,
    setSuggestionType,
    setActiveService
  }
}
