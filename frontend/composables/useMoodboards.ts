/**
 * Composable for Moodboard CRUD operations
 * Handles all interactions with the comprehensive moodboard API
 */

import { ref } from 'vue'
import type { Ref } from 'vue'
import { useRuntimeConfig, useToast, useRequestHeaders } from '#imports'

interface APIError {
  data?: {
    detail?: string
    error?: string
  }
  statusMessage?: string
  message?: string
  statusCode?: number
}

interface FetchMoodboardsParams {
  page?: number
  page_size?: number
  category?: string
  status?: string
  search?: string
  tags?: string
  is_public?: boolean
  owner?: string
  _t?: number
}

interface AISessionResponse {
  moodboard: Moodboard
  session_id?: string
}

interface BulkActionData {
  new_category?: string
  tag_names?: string[]
  [key: string]: unknown
}

interface SearchFilters {
  category?: string
  status?: string
  tags?: string
  is_public?: boolean
  owner?: string
  page?: number
  page_size?: number
}

interface PaginatedResponse<T> {
  results?: T[]
  count?: number
  next?: string
  previous?: string
}

export interface Moodboard {
  id: string
  title: string
  description: string
  category: string
  status: string
  tags: string
  color_palette: string[]
  is_public: boolean
  owner: string
  images: MoodboardImage[]
  text_elements: MoodboardTextElement[]
  // Canvas settings
  canvas_width: number
  canvas_height: number
  canvas_background_color: string
  canvas_background_image?: string
  canvas_drawing_layer?: string
  grid_enabled: boolean
  grid_size: number
  snap_to_grid: boolean
  created_at: string
  updated_at: string
}

export interface MoodboardImage {
  id: string
  moodboard: string
  image_url: string
  title: string
  prompt?: string
  source: string
  is_selected: boolean
  order_index: number
  // Canvas positioning
  x_position: number
  y_position: number
  canvas_width: number
  canvas_height: number
  rotation: number
  z_index: number
  opacity: number
  // Technical metadata
  width?: number
  height?: number
  ai_model?: string
  generation_params?: object
  created_at: string
}

export interface MoodboardTextElement {
  id: string
  moodboard: string
  content: string
  // Canvas positioning
  x_position: number
  y_position: number
  width: number
  height: number
  rotation: number
  z_index: number
  opacity: number
  // Typography
  font_family: string
  font_size: number
  font_weight: number
  text_align: 'left' | 'center' | 'right' | 'justify'
  line_height: number
  letter_spacing: number
  // Colors
  text_color: string
  background_color?: string
  border_color?: string
  border_width: number
  // State
  is_selected: boolean
  order_index: number
  created_at: string
  updated_at: string
}

export interface MoodboardShare {
  id: string
  moodboard: string
  shared_with_email: string
  permission: 'view' | 'comment' | 'edit'
  created_at: string
}

export interface MoodboardComment {
  id: string
  moodboard: string
  image?: string
  author: string
  content: string
  parent?: string
  created_at: string
}

export interface MoodboardTemplate {
  id: string
  name: string
  description: string
  category: string
  color_palette: string[]
  default_tags: string
  created_by: string
  is_public: boolean
}

export const useMoodboards = () => {
  const config = useRuntimeConfig()
  const toast = useToast()
  const apiBase = config.public.apiBase

  // State
  const moodboards: Ref<Moodboard[]> = ref([])
  const currentMoodboard: Ref<Moodboard | null> = ref(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Helper function to create headers with CSRF token
  const createHeaders = (additionalHeaders: Record<string, string> = {}) => {
    const csrfToken = useCookie('csrftoken').value
    return {
      ...useRequestHeaders(['cookie']),
      'Content-Type': 'application/json',
      ...(csrfToken && { 'X-CSRFToken': csrfToken }),
      ...additionalHeaders,
    }
  }

  // Helper function for API calls
  const handleApiCall = async <T>(apiCall: () => Promise<T>): Promise<T | null> => {
    try {
      error.value = null
      return await apiCall()
    } catch (err: unknown) {
      const apiError = err as APIError
      error.value =
        apiError.data?.detail || apiError.statusMessage || apiError.message || 'An error occurred'
      toast.add({
        title: 'Error',
        description: error.value || undefined,
        color: 'error',
      })
      return null
    }
  }

  // Moodboard CRUD Operations
  const fetchMoodboards = async (params?: FetchMoodboardsParams) => {
    loading.value = true
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/`, {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
        query: params,
      })
      return response
    })

    if (result) {
      moodboards.value = (result as PaginatedResponse<Moodboard>).results || (result as Moodboard[])
    }
    loading.value = false
    return result
  }

  const fetchMoodboard = async (id: string) => {
    loading.value = true

    try {
      error.value = null
      const response = await $fetch(`${apiBase}/moodboards/${id}/`, {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
        query: {
          _t: Date.now(),
        },
      })

      currentMoodboard.value = response as Moodboard
      loading.value = false
      return response
    } catch (err: unknown) {
      const apiError = err as APIError
      if (apiError.statusCode === 404) {
        error.value = apiError.data?.detail || 'Moodboard not found'
        loading.value = false
        return null
      } else if (apiError.statusCode === 500) {
        error.value = 'Server error occurred while loading moodboard'
        loading.value = false
        return null
      } else if (apiError.statusCode === 403) {
        error.value = apiError.data?.detail || 'Permission denied'
        loading.value = false
        return null
      }

      error.value =
        apiError.data?.detail || apiError.statusMessage || apiError.message || 'An error occurred'
      toast.add({
        title: 'Error',
        description: error.value || undefined,
        color: 'error',
      })
      loading.value = false
      return null
    }
  }

  const createMoodboard = async (data: Partial<Moodboard>) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: data,
      })
      return response
    })

    if (result) {
      await fetchMoodboards()
    }
    return result
  }

  const updateMoodboard = async (id: string, data: Partial<Moodboard>) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${id}/`, {
        method: 'PATCH',
        credentials: 'include',
        headers: createHeaders(),
        body: data,
      })
      return response
    })

    if (result) {
      currentMoodboard.value = result as Moodboard
      await fetchMoodboards()
    }
    return result
  }

  const deleteMoodboard = async (id: string) => {
    const result = await handleApiCall(async () => {
      await $fetch(`${apiBase}/moodboards/${id}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: createHeaders(),
      })
      return true
    })

    if (result) {
      await fetchMoodboards()
    }
    return result
  }

  const duplicateMoodboard = async (id: string) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${id}/duplicate/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
      })
      return response
    })

    if (result) {
      await fetchMoodboards()
    }
    return result
  }

  // Image Operations
  const addImageToMoodboard = async (moodboardId: string, imageData: Partial<MoodboardImage>) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${moodboardId}/images/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: imageData,
      })
      return response
    })

    if (result) {
      toast.add({
        title: 'Success',
        description: 'Image added to moodboard',
        color: 'success',
      })
      if (currentMoodboard.value?.id === moodboardId) {
        await fetchMoodboard(moodboardId)
      }
    }
    return result
  }

  const updateMoodboardImage = async (
    moodboardId: string,
    imageId: string,
    imageData: Partial<MoodboardImage>,
  ) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${moodboardId}/images/${imageId}/`, {
        method: 'PATCH',
        credentials: 'include',
        headers: createHeaders(),
        body: imageData,
      })
      return response
    })

    if (result && currentMoodboard.value?.id === moodboardId) {
      await fetchMoodboard(moodboardId)
    }
    return result
  }

  const removeImageFromMoodboard = async (moodboardId: string, imageId: string) => {
    const result = await handleApiCall(async () => {
      await $fetch(`${apiBase}/moodboards/${moodboardId}/images/${imageId}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: createHeaders(),
      })
      return true
    })

    if (result) {
      toast.add({
        title: 'Success',
        description: 'Image removed from moodboard',
        color: 'success',
      })
      if (currentMoodboard.value?.id === moodboardId) {
        await fetchMoodboard(moodboardId)
      }
    }
    return result
  }

  const bulkImageAction = async (
    moodboardId: string,
    action: string,
    imageIds: string[],
    data?: BulkActionData,
  ) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${moodboardId}/images/bulk_action/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: {
          action,
          image_ids: imageIds,
          data,
        },
      })
      return response
    })

    if (result) {
      toast.add({
        title: 'Success',
        description: `${action.charAt(0).toUpperCase() + action.slice(1)} applied to images`,
        color: 'success',
      })
      if (currentMoodboard.value?.id === moodboardId) {
        await fetchMoodboard(moodboardId)
      }
    }
    return result
  }

  // Sharing Operations
  const shareMoodboard = async (moodboardId: string, userId: string, permission: string) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${moodboardId}/share/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: {
          user_id: userId,
          permission,
        },
      })
      return response
    })

    if (result) {
      toast.add({
        title: 'Success',
        description: `Moodboard shared successfully`,
        color: 'success',
      })
    }
    return result
  }

  const shareMoodboardWithMultipleUsers = async (
    moodboardId: string,
    userIds: string[],
    permission: string,
  ) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${moodboardId}/bulk_share/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: {
          user_ids: userIds,
          permission,
        },
      })
      return response
    })

    if (result) {
      toast.add({
        title: 'Success',
        description: `Moodboard shared with ${userIds.length} user(s)`,
        color: 'success',
      })
    }
    return result
  }

  const getSharedMoodboards = async (params?: FetchMoodboardsParams) => {
    loading.value = true
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/shared_with_me/`, {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
        query: params,
      })
      return response
    })
    loading.value = false
    return result
  }

  const getPublicMoodboards = async (params?: FetchMoodboardsParams) => {
    loading.value = true
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/public/`, {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
        query: params,
      })
      return response
    })
    loading.value = false
    return result
  }

  const refreshPublicMoodboards = async () => {
    const params = { _t: Date.now() }
    return await getPublicMoodboards(params)
  }

  // Analytics
  const getMoodboardAnalytics = async () => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/analytics/`, {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      return response
    })
    return result
  }

  // Comments
  const addComment = async (
    moodboardId: string,
    content: string,
    imageId?: string,
    parentId?: string,
  ) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${moodboardId}/comments/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: {
          content,
          ...(imageId && { image: imageId }),
          ...(parentId && { parent: parentId }),
        },
      })
      return response
    })

    if (result) {
      toast.add({
        title: 'Success',
        description: 'Comment added successfully',
        color: 'success',
      })
    }
    return result
  }

  const getComments = async (moodboardId: string) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${moodboardId}/comments/`, {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      return response
    })
    return result
  }

  // Templates
  const getTemplates = async () => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/templates/`, {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      return response
    })
    return result
  }

  const createTemplate = async (data: Partial<MoodboardTemplate>) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/templates/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: data,
      })
      return response
    })

    if (result) {
      toast.add({
        title: 'Success',
        description: 'Template created successfully',
        color: 'success',
      })
    }
    return result
  }

  const useTemplate = async (templateId: string) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/templates/${templateId}/use_template/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
      })
      return response
    })

    if (result) {
      toast.add({
        title: 'Success',
        description: 'Template applied successfully',
        color: 'success',
      })
    }
    return result
  }

  // Search
  const searchMoodboards = async (query: string, filters?: SearchFilters) => {
    loading.value = true
    const result = await handleApiCall(async () => {
      const params = { search: query, ...filters }
      const response = await $fetch(`${apiBase}/moodboards/`, {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
        query: params,
      })
      return response
    })

    if (result) {
      moodboards.value = (result as PaginatedResponse<Moodboard>).results || (result as Moodboard[])
    }
    loading.value = false
    return result
  }

  // AI Moodboard Playground Functionality
  const startAISession = async (sessionData?: Partial<Moodboard>) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/start-session/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: sessionData || {},
      })
      return response
    })

    if (result) {
      currentMoodboard.value = (result as AISessionResponse).moodboard
    }
    return result
  }

  const generateAIImages = async (
    sessionId: string,
    prompt: string,
    selectedImageIds: string[] = [],
    mode: string = 'gaming',
  ) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/generate-images/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: {
          session_id: sessionId,
          prompt,
          selected_image_ids: selectedImageIds,
          mode,
        },
      })
      return response
    })

    if (result) {
      // Image generation completed successfully
    }
    return result
  }

  const getAISession = async (sessionId: string) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/session/${sessionId}/`, {
        method: 'GET',
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      return response
    })
    return result
  }

  const endAISession = async (
    sessionId: string,
    selectedImageIds: string[] = [],
    title?: string,
    isPublic?: boolean,
  ) => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/end-session/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: {
          session_id: sessionId,
          selected_image_ids: selectedImageIds,
          ...(title && { title }),
          ...(isPublic !== undefined && { public: isPublic }),
        },
      })
      return response
    })

    if (result) {
      // Session completed successfully
    }
    return result
  }

  const preloadAI = async () => {
    const result = await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/preload/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: {},
      })
      return response
    })
    return result
  }

  // Backward compatibility methods using the REST API endpoints
  const legacyStartSession = async () => {
    return await startAISession()
  }

  const legacyGenerateImages = async (
    sessionId: string,
    prompt: string,
    selectedImageIds: string[] = [],
    mode: string = 'gaming',
  ) => {
    return await generateAIImages(sessionId, prompt, selectedImageIds, mode)
  }

  const legacyGetSession = async (sessionId: string) => {
    return await getAISession(sessionId)
  }

  const legacyEndSession = async (
    sessionId: string,
    selectedImageIds: string[] = [],
    title?: string,
    isPublic?: boolean,
  ) => {
    return await endAISession(sessionId, selectedImageIds, title, isPublic)
  }

  const legacyPreload = async () => {
    return await preloadAI()
  }

  // Canvas Operations
  const updateImagePosition = async (
    moodboardId: string,
    imageId: string,
    positionData: Partial<MoodboardImage>,
  ) => {
    return await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${moodboardId}/images/${imageId}/`, {
        method: 'PATCH',
        credentials: 'include',
        headers: createHeaders(),
        body: positionData,
      })
      return response
    })
  }

  const createTextElement = async (
    moodboardId: string,
    textData: Partial<MoodboardTextElement>,
  ) => {
    return await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${moodboardId}/text-elements/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: textData,
      })

      return response
    })
  }

  const updateTextElement = async (
    moodboardId: string,
    textElementId: string,
    textData: Partial<MoodboardTextElement>,
  ) => {
    return await handleApiCall(async () => {
      const response = await $fetch(
        `${apiBase}/moodboards/${moodboardId}/text-elements/${textElementId}/`,
        {
          method: 'PATCH',
          credentials: 'include',
          headers: createHeaders(),
          body: textData,
        },
      )
      return response
    })
  }

  const deleteTextElement = async (moodboardId: string, textElementId: string) => {
    return await handleApiCall(async () => {
      const response = await $fetch(
        `${apiBase}/moodboards/${moodboardId}/text-elements/${textElementId}/`,
        {
          method: 'DELETE',
          credentials: 'include',
          headers: createHeaders(),
        },
      )
      return response
    })
  }

  const getTextElements = async (moodboardId: string) => {
    return await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/${moodboardId}/text-elements/`, {
        method: 'GET',
        credentials: 'include',
        headers: createHeaders(),
      })
      return response
    })
  }

  const exportCanvas = async (
    moodboardId: string,
    format: 'png' | 'jpg' | 'pdf' | 'svg',
    options: Record<string, unknown> = {},
  ) => {
    return await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/canvas/${moodboardId}/export/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: { format, ...options },
      })
      return response
    })
  }

  const autoLayoutCanvas = async (
    moodboardId: string,
    layoutType: 'grid' | 'masonry' | 'scattered' | 'centered',
  ) => {
    return await handleApiCall(async () => {
      const response = await $fetch(`${apiBase}/moodboards/canvas/${moodboardId}/auto-layout/`, {
        method: 'POST',
        credentials: 'include',
        headers: createHeaders(),
        body: { layout_type: layoutType },
      })
      return response
    })
  }

  const importImagesToCanvas = async (moodboardId: string, files: File[]) => {
    return await handleApiCall(async () => {
      const formData = new FormData()
      files.forEach((file, index) => {
        formData.append(`images[${index}]`, file)
      })

      const response = await $fetch(`${apiBase}/moodboards/canvas/${moodboardId}/import-image/`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })
      return response
    })
  }

  return {
    // State
    moodboards,
    currentMoodboard,
    loading,
    error,

    // Moodboard Operations
    fetchMoodboards,
    fetchMoodboard,
    createMoodboard,
    updateMoodboard,
    deleteMoodboard,
    duplicateMoodboard,

    // Image Operations
    addImageToMoodboard,
    updateMoodboardImage,
    removeImageFromMoodboard,
    bulkImageAction,

    // Sharing
    shareMoodboard,
    shareMoodboardWithMultipleUsers,
    getSharedMoodboards,
    getPublicMoodboards,
    refreshPublicMoodboards,

    // Analytics
    getMoodboardAnalytics,

    // Comments
    addComment,
    getComments,

    // Templates
    getTemplates,
    createTemplate,
    useTemplate,

    // Search
    searchMoodboards,

    // AI Moodboard Playground (New Integrated Methods)
    startAISession,
    generateAIImages,
    getAISession,
    endAISession,
    preloadAI,

    // Backward Compatibility (Legacy API Endpoints)
    legacyStartSession,
    legacyGenerateImages,
    legacyGetSession,
    legacyEndSession,
    legacyPreload,

    // Canvas Operations
    updateImagePosition,
    createTextElement,
    updateTextElement,
    deleteTextElement,
    getTextElements,
    exportCanvas,
    autoLayoutCanvas,
    importImagesToCanvas,
  }
}
