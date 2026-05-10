export const projectTargetPlatforms = ['web', 'mobile', 'desktop', 'console'] as const
export type ProjectTargetPlatform = (typeof projectTargetPlatforms)[number]

export interface Project {
  id: string
  name: string
  description: string
  genre: string
  targetPlatform: ProjectTargetPlatform[] | ProjectTargetPlatform | string | string[]
  is_current?: boolean
  created_at: string
  updated_at: string
  icon?: string | null
}
