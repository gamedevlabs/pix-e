import type { SelectMenuItem } from '@nuxt/ui'

export const pxLockUnlockModes = ['permanent', 'temporary', 'reversible', 'collapsible'] as const
export type PxUnlockModeType = (typeof pxLockUnlockModes)[number]

export const pxUnlockModeDisplayNames = {
  permanent: 'Permanent',
  temporary: 'Temporary',
  reversible: 'Reversible',
  collapsible: 'Collapsible',
}

export const pxUnlockModesForSelection: SelectMenuItem[] = Object.entries(
  pxUnlockModeDisplayNames,
).map((key_type) => ({ value: key_type[0], label: key_type[1] }))

export const pxKeyTypes = ['item', 'ability', 'other'] as const
export type PxKeyTypesType = (typeof pxKeyTypes)[number]

export const pxKeyTypesDisplayNames = {
  item: 'Item',
  ability: 'Ability',
  other: 'Other',
}

export const pxKeyTypesForSelection: SelectMenuItem[] = Object.entries(pxKeyTypesDisplayNames).map(
  (key_type) => ({ value: key_type[0], label: key_type[1] }),
)

export interface PxLockDefinition {
  id: string
  name: string
  soft_gate: boolean
  unlocked_by: string[] // ids of key definitions
  unlock_mode: PxUnlockModeType
  created_at: string
  updated_at: string
  owner: number | null
}

export interface PxKeyDefinition {
  id: string
  name: string
  key_type: PxKeyTypesType
  consumable: boolean
  fixed: boolean
  unique: boolean // can also be verified. alternatively: show summary with count of each key
  created_at: string
  updated_at: string
  owner: number | null
}

export interface PxLock {
  id: string
  px_chart: string
  definition: string
  edge: string
  count: number
  created_at: string
  updated_at: string
  owner: number | null
}

export interface PxKey {
  id: string
  definition: string
  node: string
  count: number
  created_at: string
  updated_at: string
  owner: number | null
}
