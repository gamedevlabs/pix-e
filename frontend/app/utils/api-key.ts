import type { ProviderType } from '~/types/api-key'

/** Human-readable display labels for each LLM provider type. */
export const PROVIDER_LABELS: Record<ProviderType, string> = {
  openai: 'OpenAI',
  gemini: 'Gemini',
  morpheus: 'Morpheus (TUM CIT)',
  custom: 'Custom API',
}

/** Icon name mappings for each provider type (plus ollama for local fallback). */
export const PROVIDER_ICONS: Record<ProviderType | 'ollama', string> = {
  openai: 'i-simple-icons-openai',
  gemini: 'i-simple-icons-googlegemini',
  morpheus: 'i-lucide-graduation-cap',
  custom: 'i-lucide-globe',
  ollama: 'i-lucide-circle-help',
}

/** UI option definitions for the provider selection dropdown. */
export const PROVIDER_OPTIONS = [
  {
    value: 'morpheus' as ProviderType,
    label: 'Morpheus',
    icon: 'i-lucide-graduation-cap',
    description: 'TUM CIT LLM cluster — free for students/staff',
  },
  {
    value: 'openai' as ProviderType,
    label: 'OpenAI',
    icon: 'i-simple-icons-openai',
    description: 'GPT-4, GPT-4o, GPT-4o-mini and more',
  },
  {
    value: 'gemini' as ProviderType,
    label: 'Google Gemini',
    icon: 'i-simple-icons-googlegemini',
    description: 'Gemini 2.0 Flash, Gemini Pro and more',
  },
  {
    value: 'custom' as ProviderType,
    label: 'Custom API',
    icon: 'i-lucide-globe',
    description: 'Any OpenAI-compatible API (Azure, Groq, etc.)',
  },
]
