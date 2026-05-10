export const projectTargetPlatforms = ['web', 'mobile', 'desktop', 'console'] as const
export type ProjectTargetPlatform = (typeof projectTargetPlatforms)[number]

export interface Project {
  id: number
  name: string
  description: string
  genres: string[]
  target_platforms: ProjectTargetPlatform[]
  is_current?: boolean
  created_at: string
  updated_at: string
  icon?: string | null
}
