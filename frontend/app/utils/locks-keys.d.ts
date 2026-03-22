const pxLockUnlockModes = ['permanent', 'temporary', 'reversible', 'collapsible'] as const
type PxLockUnlockModeType = (typeof pxLockUnlockModes)[number] // TODO: improve name

const pxKeyTypes = ['item', 'ability', 'none'] as const
type PxKeyTypesType = (typeof pxKeyTypes)[number] // TODO: improve name

interface PxLockDefinition {
  id: string
  name: string
  unlocked_by: string[] // ids of key definitions
  unlock_mode: PxLockUnlockModeType
  created_at: string
  updated_at: string
  owner: number | null
}

interface PxKeyDefinition {
  id: string
  name: string
  type: PxKeyTypesType
  consumable: boolean
  fixed: boolean
  unique: boolean // can also be verified. alternatively: show summary with count of each key
  created_at: string
  updated_at: string
  owner: number | null
}

interface PxLock {
  id: string
  px_chart: string
  definition: string
  edge: string
  count: number
  created_at: string
  updated_at: string
  owner: number | null
}

interface PxKey {
  id: string
  definition: string
  node: string
  count: number
  created_at: string
  updated_at: string
  owner: number | null
}
