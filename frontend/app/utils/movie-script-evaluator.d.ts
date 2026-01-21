export interface Asset {
  id: number
  name?: string
  class_name?: string
  project_name?: string
  path?: string

  createdAt?: string
  updatedAt?: string

  title?: string
  type?: string
  size?: number // in bytes
  url?: string
  thumbnailUrl?: string
  previewUrl?: string
}

export interface MovieProject extends NamedEntity {
  id: number

  createdAt?: string
  updatedAt?: string
}

export interface MovieScript {
  id?: number
  title: string
  file: File

  created_at?: Date
  updated_at?: Date
}

export interface AssetListAnalysis {
  scenes: SceneAnalysis[]
}

export interface SceneAnalysis {
  scene_id: number
  can_use_assets: boolean
  assets_used: string[]
}

export interface ScriptSceneAnalysis {
  id?: number
  project?: string

  scene: string
  asset_name: string
  asset_type: string
  fab_search_keyword: string
  notes: string

  created_at?: Date
  updated_at?: Date
}
export interface MovieScriptAnalysisResponse {
  result: ScriptSceneAnalysis[]
}
