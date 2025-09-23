// Enhanced TypeScript interfaces for production-ready moodboards

export interface MoodboardMetadata {
  id: string
  title: string
  description?: string
  is_public: boolean
  is_draft: boolean
  public_permission: 'view' | 'edit'
  color_palette: string[]
  tags: string[]
  created_at: string
  updated_at: string
  owner_id: string
  view_count: number
  like_count: number
}

export interface MoodboardImage {
  id: string
  url: string
  thumbnail_url: string
  prompt: string
  is_selected: boolean
  order_index: number
  created_at: string
  metadata: ImageMetadata
  // Canvas positioning fields
  x_position: number
  y_position: number
  canvas_width: number
  canvas_height: number
  rotation: number
  z_index: number
  opacity: number
}

export interface MoodboardTextElement {
  id: string
  content: string
  x_position: number
  y_position: number
  width: number
  height: number
  rotation: number
  z_index: number
  opacity: number
  font_family: string
  font_size: number
  font_weight: number
  text_align: 'left' | 'center' | 'right' | 'justify'
  line_height: number
  letter_spacing: number
  text_color: string
  background_color?: string
  border_color?: string
  border_width: number
  is_selected: boolean
  order_index: number
  created_at: string
  updated_at: string
}

export interface ImageMetadata {
  width: number
  height: number
  file_size: number
  generation_params: {
    model: string
    seed?: number
    steps?: number
    cfg_scale?: number
  }
  color_analysis: {
    dominant_colors: string[]
    brightness: number
    contrast: number
  }
}

export interface UserPermissions {
  is_owner: boolean
  permission: 'view' | 'edit' | 'admin'
  can_edit: boolean
  can_delete: boolean
  can_share: boolean
  can_manage_permissions: boolean
}

export interface MoodboardState {
  // Core data
  metadata: MoodboardMetadata | null
  images: MoodboardImage[]
  permissions: UserPermissions

  // UI state
  ui: {
    loading: boolean
    saving: boolean
    error: MoodboardError | null
    selectedImageIds: string[]
    viewMode: 'grid' | 'list' | 'masonry'
    filterTags: string[]
    sortBy: 'created_at' | 'title' | 'updated_at'
    sortOrder: 'asc' | 'desc'
  }

  // Optimistic updates
  pendingUpdates: PendingUpdate[]
}

export interface PendingUpdate {
  id: string
  type: 'metadata' | 'image_selection' | 'image_order'
  data: Record<string, unknown>
  timestamp: number
  retryCount: number
}

export interface MoodboardError {
  code: string
  message: string
  recoverable: boolean
  context?: Record<string, unknown>
  timestamp: number
}

export interface MoodboardFilters {
  search?: string
  tags?: string[]
  is_public?: boolean
  is_draft?: boolean
  owner?: string
  date_range?: {
    start: string
    end: string
  }
}

export interface MoodboardAnalytics {
  views: number
  unique_viewers: number
  likes: number
  shares: number
  time_spent: number
  bounce_rate: number
  popular_images: string[]
}

export interface CollaborationEvent {
  type: 'image_added' | 'image_removed' | 'metadata_updated' | 'user_joined' | 'user_left'
  user_id: string
  user_name: string
  data: Record<string, unknown>
  timestamp: number
}

export interface MoodboardTemplate {
  id: string
  name: string
  description: string
  thumbnail_url: string
  tags: string[]
  color_palette: string[]
  default_prompts: string[]
  usage_count: number
}

// API Response types
export interface APIResponse<T> {
  data: T
  meta?: {
    page: number
    per_page: number
    total: number
    total_pages: number
  }
  errors?: APIError[]
}

export interface APIError {
  code: string
  message: string
  field?: string
  details?: Record<string, unknown>
}

// Configuration interfaces
export interface MoodboardConfig {
  max_images_per_moodboard: number
  max_moodboards_per_user: number
  supported_image_formats: string[]
  max_image_size: number
  default_grid_size: number
  auto_save_interval: number
  cache_duration: number
  websocket_enabled: boolean
}

export interface GenerationSettings {
  model: string
  quality: 'draft' | 'standard' | 'high'
  batch_size: number
  style_presets: string[]
  negative_prompts: string[]
  aspect_ratios: Array<{ label: string; value: string }>
}
