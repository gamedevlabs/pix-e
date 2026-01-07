export const projectTargetPlatforms = ['web', 'mobile', 'desktop', 'console'] as const
export type ProjectTargetPlatform = (typeof projectTargetPlatforms)[number]

export interface Project {
  id: string
  name: string
  shortDescription: string
  genre: string
  targetPlatform: ProjectTargetPlatform | string
  created_at: string
  updated_at: string
}
