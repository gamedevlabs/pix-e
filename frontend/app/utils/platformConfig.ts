import type { ProjectTargetPlatform } from './project.d'

export interface PlatformConfig {
  value: ProjectTargetPlatform
  label: string
  icon: string
}

export const platformConfigs: PlatformConfig[] = [
  { value: 'web', label: 'Web', icon: 'i-heroicons-globe-alt' },
  { value: 'mobile', label: 'Mobile', icon: 'i-heroicons-device-phone-mobile' },
  { value: 'desktop', label: 'Desktop', icon: 'i-heroicons-computer-desktop' },
  { value: 'console', label: 'Console', icon: 'i-heroicons-puzzle-piece' },
]

// Genre suggestions for project creation
export const genreSuggestions = [
  'Action',
  'Adventure',
  'RPG',
  'Strategy',
  'Simulation',
  'Puzzle',
  'Narrative',
  'Horror',
  'Platformer',
  'Sports',
] as const

export type GenreSuggestion = (typeof genreSuggestions)[number]

// Helper function to get platform config by value
export function getPlatformConfig(value: ProjectTargetPlatform): PlatformConfig | undefined {
  return platformConfigs.find((config) => config.value === value)
}

// Helper function to get platform icon by value
export function getPlatformIcon(value: ProjectTargetPlatform): string {
  return getPlatformConfig(value)?.icon || 'i-heroicons-square-3-stack-3d'
}
