export const projectTargetPlatforms = ['web', 'mobile', 'desktop', 'console'] as const
export type ProjectTargetPlatform = (typeof projectTargetPlatforms)[number]

export interface Project {
  id: string
  name: string
  shortDescription: string
  genre: string
  targetPlatform: ProjectTargetPlatform[] | ProjectTargetPlatform | string | string[]
  created_at: string
  updated_at: string
  // Optional icon data URL (base64) or remote URL
  icon?: string | null
}
