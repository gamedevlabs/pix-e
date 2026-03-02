// Consolidated mock-only study runtime.
// This file intentionally centralizes the mock DB, offline fetch helpers,
// and the localStorage-backed ProjectDataProvider to reduce file count.

import { computed } from 'vue'
import type { WorkflowStep, StepStatus, Substep, ProjectWorkflow } from '~/utils/workflow'

import type { Project } from '~/utils/project'

// ---------------------------------------------------------------------------
// Local helper types + defaults (study mock only)
// ---------------------------------------------------------------------------

type User = {
  username: string
}

// Minimal pillar shape used by this mock. Keep it intentionally flexible so it
// can store whatever the UI sends.
export type Pillar = Record<string, unknown> & {
  id?: string | number
  created_at?: string
  updated_at?: string
}

function idOf(x: unknown): string {
  if (!x || typeof x !== 'object') return ''
  const v = (x as Record<string, unknown>).id
  return typeof v === 'string' || typeof v === 'number' ? String(v) : ''
}

function defaultPillarsState(): OfflinePillarsPayload {
  return {
    schemaVersion: 1,
    pillars: [],
    designIdea: { description: '' },
  }
}

function defaultEntities(): Record<string, Record<string, unknown>[]> {
  return {}
}

// ---------------------------------------------------------------------------
// Constants / types (formerly in data/providers/types.ts)
// ---------------------------------------------------------------------------

export interface ProjectDataProvider {
  // Projects
  getProjects(): Promise<Project[]>
  getProject(id: string): Promise<Project | null>
  createProject(payload: Partial<Project>): Promise<Project>
  updateProject(id: string, patch: Partial<Project>): Promise<Project | null>
  deleteProject(id: string): Promise<boolean>

  // Workflows
  getWorkflowsByProjectId(projectId: string): Promise<WorkflowInstance[]>
  seedProjectWorkflows(
    projectId: string,
    onboardingAlreadyDone?: boolean,
  ): Promise<WorkflowInstance[]>
  saveWorkflow(workflow: WorkflowInstance): Promise<void>
  getUserOnboardingWorkflow(): Promise<WorkflowInstance | null>
  completeOnboardingWorkflow(): Promise<void>
  getActiveWorkflowId(scope: string): string | null
  setActiveWorkflowId(scope: string, id: string | null): void

  // Generic entity CRUD (pxcharts, pxnodes, pxcomponentdefinitions, pxcomponents, containers, edges)
  getEntities(collection: string): Promise<unknown[]>
  createEntity(
    collection: string,
    payload: Record<string, unknown>,
  ): Promise<Record<string, unknown>>
  updateEntity(
    collection: string,
    id: string,
    patch: Record<string, unknown>,
  ): Promise<Record<string, unknown> | null>
  deleteEntity(collection: string, id: string): Promise<boolean>

  // Project scoping for stored entities (mock mode)
  getCurrentProjectId(): string | null
  setCurrentProjectId(id: string | null): void

  // Study/session helpers
  exportState(): Promise<string>
  importState(json: string): Promise<void>
  resetState(): Promise<void>
  getParticipantId(): string
  setParticipantId(id: string): void
  getLastSavedAt(): string | null
}

export const STUDY_STORAGE_NAMESPACE = 'pixe.study.v1'
export const STUDY_SCHEMA_VERSION = 2

// ---------------------------------------------------------------------------
// Offline fetch + offline API (formerly composables/useOfflineFetch.ts + data/offline/offlineApi.ts)
// ---------------------------------------------------------------------------

let cachedMockData: Record<string, unknown> | null = null

async function getMockRoot(): Promise<Record<string, unknown>> {
  if (cachedMockData) return cachedMockData
  cachedMockData = await $fetch<Record<string, unknown>>('/mock/data.json', {
    server: false,
  } as Parameters<typeof $fetch>[1])
  return cachedMockData
}

export async function useOfflineFetch<T>(key: string, path?: string): Promise<T> {
  const effectivePath = path ?? `/mock/${key}.json`

  const root = await getMockRoot()
  if (root && typeof root === 'object' && key in root) {
    return root[key] as T
  }

  // Back-compat mapping for older paths/keys
  const rawPath = String(effectivePath)
  const afterMock = rawPath.includes('/mock/') ? rawPath.split('/mock/').pop() || '' : rawPath
  const normalized = afterMock.replace(/\.json$/i, '').trim()

  const legacyKeyMap: Record<string, string> = {
    'player-expectations': 'playerExpectations',
  }

  const mappedKey = legacyKeyMap[normalized] || normalized
  if (root && typeof root === 'object' && mappedKey in root) {
    return root[mappedKey] as T
  }

  return await $fetch<T>(effectivePath, { server: false } as Parameters<typeof $fetch>[1])
}

export type OfflinePillarsPayload = {
  schemaVersion: number
  pillars: Pillar[]
  designIdea?: { description?: string }
}

export type OfflineSentimentsPayload = {
  schemaVersion: number
  data: unknown[]
}

export type OfflinePlayerExpectationsPayload = {
  schemaVersion: number
  aspectFrequency: Record<string, number>
  aspectSentiment: Array<{
    dominant_aspect: string
    dominant_sentiment: 'positive' | 'neutral' | 'negative'
    count: number
  }>
  trendOverTime: Array<{ month: string; positive?: number; neutral?: number; negative?: number }>
  sentimentPie: Record<string, number>
  heatmap: Record<string, Record<string, number>>
  topConfusions: Array<{ pair: string; count: number }>
}

export async function getOfflinePillars(): Promise<OfflinePillarsPayload> {
  return await useOfflineFetch<OfflinePillarsPayload>('pillars')
}

export async function getOfflineSentiments(): Promise<OfflineSentimentsPayload> {
  return await useOfflineFetch<OfflineSentimentsPayload>('sentiments')
}

export async function getOfflinePlayerExpectations(): Promise<OfflinePlayerExpectationsPayload> {
  return await useOfflineFetch<OfflinePlayerExpectationsPayload>('playerExpectations')
}

// ---------------------------------------------------------------------------
// Mock authentication (formerly composables/useAuthentication.ts)
// ---------------------------------------------------------------------------

export function useAuthentication() {
  const user = useState<User | null>('auth-user', () => null)
  const checkedLogin = useState<boolean>('checkedLogin', () => true)
  const isLoggedIn = computed(() => user.value !== null)

  async function register(username?: string) {
    user.value = { username: username || 'Study User' } as User
    return true
  }
  async function login(username?: string) {
    user.value = { username: username || 'Study User' } as User
    return true
  }
  async function checkAuthentication() {
    return user.value !== null
  }
  async function logout() {
    user.value = null
    return true
  }

  return {
    user,
    isLoggedIn,
    checkedLogin,
    register,
    login,
    checkAuthentication,
    logout,
  }
}

// ---------------------------------------------------------------------------
// Mock provider + provider hook (formerly data/providers/mockProjectDataProvider.ts + useProjectDataProvider.ts)
// ---------------------------------------------------------------------------

type StudyState = {
  schemaVersion: number
  participantId: string
  lastSavedAt: string | null
  projects: Project[]
  workflowsState?: unknown
  // Per-project persisted state
  projectsState?: Record<
    string,
    {
      pillarsState?: OfflinePillarsPayload
      entities?: Record<string, Record<string, unknown>[]>
    }
  >
  // Legacy (schemaVersion 2): user-scoped persistence
  pillarsState?: OfflinePillarsPayload
  entities?: Record<string, Record<string, unknown>[]>
  // Selected project
  currentProjectId?: string | null
}

function nowIso() {
  return new Date().toISOString()
}

function safeParse(json: string): unknown {
  try {
    return JSON.parse(json)
  } catch {
    return null
  }
}

function isObject(v: unknown): v is Record<string, unknown> {
  return !!v && typeof v === 'object' && !Array.isArray(v)
}

function storageKey() {
  return `${STUDY_STORAGE_NAMESPACE}:state`
}

function readState(): StudyState | null {
  if (!import.meta.client) return null
  const raw = localStorage.getItem(storageKey())
  if (!raw) return null
  const parsed = safeParse(raw)
  if (!isObject(parsed)) return null
  if ((parsed as Record<string, unknown>).schemaVersion !== STUDY_SCHEMA_VERSION) return null
  if (!Array.isArray((parsed as Record<string, unknown>).projects)) return null
  return parsed as StudyState
}

function writeState(state: StudyState) {
  if (!import.meta.client) return
  state.lastSavedAt = nowIso()
  localStorage.setItem(storageKey(), JSON.stringify(state, null, 2))
}

// Helpers for project-scoped buckets
function defaultProjectBucket() {
  return {
    pillarsState: defaultPillarsState(),
    entities: defaultEntities(),
  }
}

function ensureProjectBucket(state: StudyState, projectId: string) {
  if (!state.projectsState) state.projectsState = {}
  if (!state.projectsState[projectId]) state.projectsState[projectId] = defaultProjectBucket()
  const bucket = state.projectsState[projectId]!
  if (!bucket.pillarsState) bucket.pillarsState = defaultPillarsState()
  if (!bucket.entities) bucket.entities = defaultEntities()
  return bucket
}

function getCurrentProjectIdFromState(state: StudyState | null | undefined): string | null {
  const id = state?.currentProjectId
  return typeof id === 'string' && id.trim() ? id : null
}

function getLegacyOrDefaultPillarsState(
  state: StudyState | null | undefined,
): OfflinePillarsPayload {
  const ps = state?.pillarsState
  if (ps && typeof ps === 'object' && Array.isArray(ps.pillars)) return ps
  return defaultPillarsState()
}

function getLegacyOrDefaultEntities(
  state: StudyState | null | undefined,
): Record<string, Record<string, unknown>[]> {
  const e = state?.entities
  if (e && typeof e === 'object') return e
  return defaultEntities()
}

// Helpers for pillars state persistence
// (kept for compatibility; now maps to the current project bucket when available)
function getPillarsStateFromMem(state: StudyState | null | undefined): OfflinePillarsPayload {
  const pid = getCurrentProjectIdFromState(state)
  if (state && pid) {
    const bucket = ensureProjectBucket(state, pid)
    return bucket.pillarsState ?? defaultPillarsState()
  }
  return getLegacyOrDefaultPillarsState(state)
}

// Helpers for generic entity collections
function getEntityCollection(state: StudyState, collection: string): Record<string, unknown>[] {
  const pid = getCurrentProjectIdFromState(state)
  if (pid) {
    const bucket = ensureProjectBucket(state, pid)
    if (!bucket.entities) bucket.entities = defaultEntities()
    if (!bucket.entities[collection]) bucket.entities[collection] = []
    return bucket.entities[collection]!
  }

  // Legacy fallback
  if (!state.entities) state.entities = defaultEntities()
  if (!state.entities[collection]) state.entities[collection] = []
  return state.entities[collection]!
}

export function getPersistedOfflinePillars(): OfflinePillarsPayload {
  if (!import.meta.client) return defaultPillarsState()
  const state = readState() as StudyState | null
  return getPillarsStateFromMem(state)
}

export function setPersistedOfflinePillars(next: OfflinePillarsPayload) {
  if (!import.meta.client) return
  const current = (readState() as StudyState | null) ?? {
    schemaVersion: STUDY_SCHEMA_VERSION,
    participantId: '',
    lastSavedAt: null,
    projects: [],
    currentProjectId: null,
    projectsState: {},
  }

  const pid = getCurrentProjectIdFromState(current)
  const updated: StudyState = {
    ...(current as StudyState),
  }

  if (pid) {
    const bucket = ensureProjectBucket(updated, pid)
    bucket.pillarsState = {
      schemaVersion: next.schemaVersion ?? 1,
      pillars: Array.isArray(next.pillars) ? next.pillars : [],
      designIdea: next.designIdea ?? { description: '' },
    }
  } else {
    // Legacy
    updated.pillarsState = {
      schemaVersion: next.schemaVersion ?? 1,
      pillars: Array.isArray(next.pillars) ? next.pillars : [],
      designIdea: next.designIdea ?? { description: '' },
    }
  }

  writeState(updated)
}

export function createMockProjectDataProvider(): ProjectDataProvider {
  const workflowApi = new WorkflowApiEmulator()
  let ready: Promise<void> | null = null
  let mem: StudyState | null = null

  async function ensureReady() {
    if (!import.meta.client) return
    if (ready) return ready
    ready = (async () => {
      const existing = readState()
      if (existing) {
        mem = existing as StudyState

        // Ensure project-scoped buckets exist
        if (!mem.projectsState) mem.projectsState = {}
        if (typeof mem.currentProjectId === 'undefined') mem.currentProjectId = null

        // Migration: if we have legacy pillars/entities, move them into the first project bucket
        // (best-effort; prevents losing existing user-scoped data)
        const legacyPillars = getLegacyOrDefaultPillarsState(mem)
        const legacyEntities = getLegacyOrDefaultEntities(mem)
        const firstProjectId = mem.projects?.[0]?.id
        if (firstProjectId) {
          const bucket = ensureProjectBucket(mem, firstProjectId)
          // Only migrate if bucket is still empty (avoid overwriting)
          if (
            (bucket.pillarsState?.pillars?.length ?? 0) === 0 &&
            (legacyPillars.pillars?.length ?? 0) > 0
          ) {
            bucket.pillarsState = legacyPillars
          }
          if (
            Object.keys(bucket.entities ?? {}).length === 0 &&
            Object.keys(legacyEntities ?? {}).length > 0
          ) {
            bucket.entities = legacyEntities
          }
          if (!mem.currentProjectId) mem.currentProjectId = firstProjectId
        }

        // Ensure the active project's state exists
        if (mem.currentProjectId) ensureProjectBucket(mem, mem.currentProjectId)

        // Mirror into localStorage field if missing.
        setPersistedOfflinePillars(getPillarsStateFromMem(mem))

        if ((existing as StudyState).workflowsState) {
          try {
            workflowApi.importState((existing as StudyState).workflowsState)
          } catch {
            // ignore
          }
        }
        return
      }

      mem = {
        schemaVersion: STUDY_SCHEMA_VERSION,
        participantId: '',
        lastSavedAt: null,
        projects: [],
        currentProjectId: null,
        projectsState: {},
      }

      writeState(mem)
    })()
    return ready
  }

  function requireMem(): StudyState {
    if (!mem) {
      mem = {
        schemaVersion: STUDY_SCHEMA_VERSION,
        participantId: '',
        lastSavedAt: null,
        projects: [],
        currentProjectId: null,
        projectsState: {},
      }
    }
    if (!mem.projectsState) mem.projectsState = {}
    if (typeof mem.currentProjectId === 'undefined') mem.currentProjectId = null
    if (mem.currentProjectId) ensureProjectBucket(mem, mem.currentProjectId)
    return mem
  }

  function persist() {
    const state = requireMem()
    // Mirror current project's pillarsState into localStorage on every persist.
    setPersistedOfflinePillars(getPillarsStateFromMem(state))

    try {
      state.workflowsState = workflowApi.exportState()
    } catch {
      // ignore
    }
    writeState(state)
  }

  return {
    async getProjects() {
      await ensureReady()
      return requireMem().projects.map((p) => ({ ...p }))
    },
    async getProject(id: string) {
      await ensureReady()
      const p = requireMem().projects.find((x) => x.id === id)
      return p ? { ...p } : null
    },
    async createProject(payload: Partial<Project>) {
      await ensureReady()
      const state = requireMem()
      const created: Project = {
        id: payload.id || `${Date.now()}`,
        name: payload.name || 'Untitled Project',
        shortDescription: payload.shortDescription || '',
        genre: payload.genre || 'Unknown',
        targetPlatform: (payload.targetPlatform as Project['targetPlatform']) ?? 'web',
        created_at: (payload.created_at as string) || nowIso(),
        updated_at: nowIso(),
        icon: (payload.icon as string | null) ?? null,
      }
      state.projects.push(created)

      // Ensure a bucket exists for this project
      ensureProjectBucket(state, created.id)
      // If no project is selected yet, select this one.
      if (!state.currentProjectId) state.currentProjectId = created.id

      persist()
      return { ...created }
    },
    async updateProject(id: string, patch: Partial<Project>) {
      await ensureReady()
      const state = requireMem()
      const idx = state.projects.findIndex((x) => x.id === id)
      if (idx === -1) return null
      const existing = state.projects[idx]!
      const updated: Project = {
        id: existing.id,
        name: patch.name ?? existing.name,
        shortDescription: patch.shortDescription ?? existing.shortDescription,
        genre: patch.genre ?? existing.genre,
        targetPlatform:
          (patch.targetPlatform as Project['targetPlatform']) ?? existing.targetPlatform,
        created_at: existing.created_at,
        updated_at: nowIso(),
        icon: (patch.icon as string | null) ?? existing.icon ?? null,
      }
      state.projects[idx] = updated
      persist()
      return { ...updated }
    },
    async deleteProject(id: string) {
      await ensureReady()
      const state = requireMem()
      const before = state.projects.length
      state.projects = state.projects.filter((x) => x.id !== id)
      if (state.projectsState && state.projectsState[id]) {
        const { [id]: _removed, ...rest } = state.projectsState
        state.projectsState = rest
      }
      if (state.currentProjectId === id) {
        state.currentProjectId = state.projects[0]?.id ?? null
      }
      persist()
      return state.projects.length < before
    },

    async getWorkflowsByProjectId(projectId: string) {
      await ensureReady()
      return await workflowApi.getWorkflowsByProjectId(projectId)
    },
    async seedProjectWorkflows(projectId: string, onboardingAlreadyDone = false) {
      await ensureReady()
      const seeded = await workflowApi.seedProject(projectId, onboardingAlreadyDone)
      persist()
      return seeded
    },
    async saveWorkflow(workflow: WorkflowInstance) {
      await ensureReady()
      await workflowApi.saveWorkflow(workflow)
      persist()
    },
    async getUserOnboardingWorkflow() {
      await ensureReady()
      return await workflowApi.getUserOnboardingWorkflow()
    },
    async completeOnboardingWorkflow() {
      await ensureReady()
      await workflowApi.completeOnboardingWorkflow()
      persist()
    },
    getActiveWorkflowId(scope: string) {
      if (!import.meta.client) return null
      return workflowApi.getActiveWorkflowId(scope)
    },
    setActiveWorkflowId(scope: string, id: string | null) {
      if (!import.meta.client) return
      workflowApi.setActiveWorkflowId(scope, id)
      persist()
    },

    // ── Current project ────────────────────────────────────────────────────
    getCurrentProjectId() {
      return getCurrentProjectIdFromState(mem ?? readState())
    },
    setCurrentProjectId(id: string | null) {
      const state = requireMem()
      state.currentProjectId = typeof id === 'string' && id.trim() ? id : null
      if (state.currentProjectId) ensureProjectBucket(state, state.currentProjectId)
      persist()
    },

    // ── Generic entity CRUD ──────────────────────────────────────────────────
    async getEntities(collection: string) {
      await ensureReady()
      const state = requireMem()
      const pid = getCurrentProjectIdFromState(state)
      const bucket = pid ? ensureProjectBucket(state, pid) : null

      if (collection === 'pillars') {
        const ps = bucket?.pillarsState ?? state.pillarsState ?? defaultPillarsState()
        return ps.pillars.map((x: Pillar) => ({ ...x }))
      }

      const list = getEntityCollection(state, collection)
      return list.map((x: Record<string, unknown>) => ({ ...x }))
    },

    async createEntity(collection: string, payload: Record<string, unknown>) {
      await ensureReady()
      const state = requireMem()
      const pid = getCurrentProjectIdFromState(state)
      const bucket = pid ? ensureProjectBucket(state, pid) : null

      if (collection === 'pillars') {
        const ps = bucket?.pillarsState ?? state.pillarsState ?? defaultPillarsState()
        const now = nowIso()
        const nextId =
          (payload.id as string) ??
          String(
            ps.pillars.reduce((max: number, x: Pillar) => Math.max(max, Number(idOf(x)) || 0), 0) +
              1,
          )
        const created: Record<string, unknown> = {
          ...payload,
          id: nextId,
          created_at: (payload.created_at as string) ?? now,
          updated_at: now,
        }
        ps.pillars = [...ps.pillars, created as unknown as Pillar]
        if (bucket) bucket.pillarsState = ps
        else state.pillarsState = ps
        persist()
        return { ...created }
      }

      const list = getEntityCollection(state, collection)
      const now = nowIso()
      const nextId =
        (payload.id as string) ??
        String(
          list.reduce(
            (max: number, x: Record<string, unknown>) => Math.max(max, Number(idOf(x)) || 0),
            0,
          ) + 1,
        )
      const created: Record<string, unknown> = {
        ...payload,
        id: nextId,
        created_at: (payload.created_at as string) ?? now,
        updated_at: now,
      }
      list.push(created)
      persist()
      return { ...created }
    },

    async updateEntity(collection: string, id: string, patch: Record<string, unknown>) {
      await ensureReady()
      const state = requireMem()
      const pid = getCurrentProjectIdFromState(state)
      const bucket = pid ? ensureProjectBucket(state, pid) : null

      if (collection === 'pillars') {
        const ps = bucket?.pillarsState ?? state.pillarsState ?? defaultPillarsState()
        const idx = ps.pillars.findIndex((x: Pillar) => idOf(x) === String(id))
        if (idx === -1) return null
        const updated: Record<string, unknown> = {
          ...(ps.pillars[idx] as unknown as Record<string, unknown>),
          ...patch,
          id: idOf(ps.pillars[idx]),
          updated_at: nowIso(),
        }
        ps.pillars = [
          ...ps.pillars.slice(0, idx),
          updated as unknown as Pillar,
          ...ps.pillars.slice(idx + 1),
        ]
        if (bucket) bucket.pillarsState = ps
        else state.pillarsState = ps
        persist()
        return { ...updated }
      }

      const list = getEntityCollection(state, collection)
      const idx = list.findIndex((x) => idOf(x) === String(id))
      if (idx === -1) return null
      const updated: Record<string, unknown> = {
        ...list[idx],
        ...patch,
        id: idOf(list[idx]),
        updated_at: nowIso(),
      }
      list[idx] = updated
      persist()
      return { ...updated }
    },

    async deleteEntity(collection: string, id: string) {
      await ensureReady()
      const state = requireMem()
      const pid = getCurrentProjectIdFromState(state)
      const bucket = pid ? ensureProjectBucket(state, pid) : null

      if (collection === 'pillars') {
        const ps = bucket?.pillarsState ?? state.pillarsState ?? defaultPillarsState()
        const before = ps.pillars.length
        ps.pillars = ps.pillars.filter((x: Pillar) => idOf(x) !== String(id))
        if (bucket) bucket.pillarsState = ps
        else state.pillarsState = ps
        persist()
        return ps.pillars.length < before
      }

      const list = getEntityCollection(state, collection)
      const before = list.length
      if (pid) {
        const b = ensureProjectBucket(state, pid)
        if (!b.entities) b.entities = defaultEntities()
        b.entities[collection] = list.filter((x: Record<string, unknown>) => idOf(x) !== String(id))
      } else {
        if (!state.entities) state.entities = defaultEntities()
        state.entities[collection] = list.filter(
          (x: Record<string, unknown>) => idOf(x) !== String(id),
        )
      }
      persist()
      return list.length < before
    },

    async exportState() {
      await ensureReady()
      return JSON.stringify(requireMem(), null, 2)
    },
    async importState(json: string) {
      if (!import.meta.client) return
      const parsed = safeParse(json)
      if (!isObject(parsed)) throw new Error('Invalid JSON')
      const p = parsed as Record<string, unknown>
      if (p.schemaVersion !== STUDY_SCHEMA_VERSION) throw new Error('Unsupported schemaVersion')
      if (!Array.isArray(p.projects)) throw new Error('Missing projects')

      mem = {
        schemaVersion: STUDY_SCHEMA_VERSION,
        participantId: typeof p.participantId === 'string' ? p.participantId : '',
        lastSavedAt: typeof p.lastSavedAt === 'string' ? p.lastSavedAt : null,
        projects: (p.projects as Project[]).map((proj) => ({ ...proj })),
        workflowsState: p.workflowsState,
        currentProjectId:
          typeof p.currentProjectId === 'string' ? (p.currentProjectId as string) : null,
        projectsState: isObject(p.projectsState)
          ? (p.projectsState as StudyState['projectsState'])
          : {},
        // Legacy fields (keep if present)
        pillarsState: isObject(p.pillarsState)
          ? (p.pillarsState as OfflinePillarsPayload)
          : undefined,
        entities: isObject(p.entities)
          ? (p.entities as Record<string, Record<string, unknown>[]>)
          : undefined,
      }

      // Ensure any selected project's bucket exists
      if (mem.currentProjectId) ensureProjectBucket(mem, mem.currentProjectId)

      if (mem.workflowsState) {
        try {
          workflowApi.importState(mem.workflowsState)
        } catch {
          // ignore
        }
      }

      writeState(mem)
      setPersistedOfflinePillars(getPillarsStateFromMem(mem))
    },
    async resetState() {
      if (!import.meta.client) return
      // Clear persisted storage.
      localStorage.removeItem(storageKey())
      // Reset in-memory state.
      mem = null
      ready = null
      // Reset workflow emulator to a clean instance.
      workflowApi.reset()
      // Clear the static mock-data cache so fresh data is loaded after reset.
      cachedMockData = null
      await ensureReady()
    },

    getParticipantId() {
      return readState()?.participantId ?? ''
    },
    setParticipantId(id: string) {
      if (!import.meta.client) return
      const state = readState() ?? {
        schemaVersion: STUDY_SCHEMA_VERSION,
        participantId: '',
        lastSavedAt: null,
        projects: [],
        currentProjectId: null,
        projectsState: {},
      }
      const next: StudyState = {
        ...(state as StudyState),
        participantId: id,
        pillarsState: getPillarsStateFromMem(state as StudyState),
        entities: (state as StudyState).entities ?? defaultEntities(),
      }
      writeState(next)
      mem = next
    },
    getLastSavedAt() {
      return readState()?.lastSavedAt ?? null
    },
  }
}

const NUXT_APP_KEY = 'pixeProjectDataProvider'

export function useProjectDataProvider(): ProjectDataProvider {
  const nuxtApp = useNuxtApp()
  const anyApp = nuxtApp as Record<string, unknown>

  if (anyApp[NUXT_APP_KEY]) return anyApp[NUXT_APP_KEY] as ProjectDataProvider

  const provider = createMockProjectDataProvider()
  anyApp[NUXT_APP_KEY] = provider
  return provider
}

// ---------------------------------------------------------------------------
// UI mock data (formerly in frontend/app/mock_data/*)
// ---------------------------------------------------------------------------

export type MockRecentActivityType = 'edit' | 'create' | 'delete'

export interface MockRecentActivityItem {
  title: string
  timestamp: string
  icon: string
  type?: MockRecentActivityType
}

export const mockRecentActivity: MockRecentActivityItem[] = [
  {
    title: 'Created PX Node “Combat Loop”',
    timestamp: '12 min ago',
    icon: 'i-lucide-plus',
    type: 'create',
  },
  {
    title: 'Updated Design Pillar “Clarity”',
    timestamp: '1 hour ago',
    icon: 'i-lucide-edit',
    type: 'edit',
  },
  {
    title: 'Removed expectation “Too grindy”',
    timestamp: 'Yesterday',
    icon: 'i-lucide-trash',
    type: 'delete',
  },
]

export type MockAiInsightType = 'info' | 'warning' | 'success'

export interface MockAiInsight {
  type: MockAiInsightType
  title: string
  message: string
}

export const mockAiInsights: MockAiInsight[] = [
  {
    type: 'warning',
    title: 'Mid-game pacing dip',
    message: 'A quieter stretch around the midpoint — consider adding a beat or escalation.',
  },
  {
    type: 'success',
    title: 'Strong pillar alignment',
    message: 'Your design pillars map well to your top expectations.',
  },
]

export interface MockWhatsNewItem {
  title: string
  description: string
  icon?: string
}

export const mockWhatsNew: MockWhatsNewItem[] = [
  {
    title: 'Workflow-driven navigation',
    description: 'Pick up where you left off with contextual next steps for each project.',
    icon: 'i-lucide-list-checks',
  },
  {
    title: 'Improved dashboards',
    description: 'Cleaner cards, better layout, and faster access to modules.',
    icon: 'i-lucide-layout-dashboard',
  },
  {
    title: 'More import/export options',
    description: 'Move data between tools with a more flexible import/export flow.',
    icon: 'i-lucide-arrow-left-right',
  },
]

export const MOCK_EXTERNAL_LINKS = {
  wiki: 'https://github.com/gamedevlabs/pix-e/wiki',
  discord: 'https://discord.gg/c2RKBwFrbF',
} as const

// ---------------------------------------------------------------------------
// Workflows (formerly in frontend/app/mock_data/mock_workflow.ts)
// ---------------------------------------------------------------------------

export type WorkflowScope = 'project' | 'user'

export interface WorkflowMeta {
  scope: WorkflowScope
  title: string
  /** Groups workflows into named phases shown in the slideover phase-picker. */
  folder: string
}

/** A workflow instance tied to a specific project (or the standalone user onboarding). */
export type WorkflowInstance = ProjectWorkflow & { meta: WorkflowMeta }

interface SubstepTemplate {
  id: string
  name: string
  description?: string
  route?: string
}

interface StepTemplate {
  id: string
  name: string
  description?: string
  route?: string
  substeps: SubstepTemplate[]
}

export interface PhaseTemplate {
  /** Unique key used as the workflow id suffix and meta.title. */
  id: string
  /** Display title shown in the phase picker. */
  title: string
  /** Folder / phase group shown in the slideover. */
  folder: string
  /** Toast message shown when the user completes this workflow. */
  completionMessage?: string
  steps: StepTemplate[]
}

export const WORKFLOW_TEMPLATE: PhaseTemplate[] = [
  {
    id: 'onboarding',
    title: 'Have a Look Around',
    folder: 'Onboarding',
    completionMessage:
      "Nice exploration! You can continue with the Design Pillars phase whenever you're ready.",
    steps: [
      {
        id: 'onb-1',
        name: 'Getting oriented',
        description: 'Learn where things are and what each module does.',
        route: '/dashboard',
        substeps: [
          { id: 'onb-1-1', name: 'Open any module through the sidebar', route: undefined },
          { id: 'onb-1-2', name: 'Have a look at the project Settings', route: '/edit' },
          { id: 'onb-1-3', name: 'Open the searchbar', route: '/dashboard' },
        ],
      },
    ],
  },
  {
    id: 'pillars',
    title: 'Design Pillars',
    folder: 'Design & Validation',
    completionMessage:
      'Great work on your Design Pillars! Your pillars are shaping the vision. Check out Player Experience next to start mapping the journey.',
    steps: [
      {
        id: 'pillars-1',
        name: 'Create your first pillar',
        description: 'Add a pillar and learn how the editor works.',
        route: '/pillars',
        substeps: [
          { id: 'pillars-1-1', name: 'Open Design Pillars', route: '/pillars' },
          { id: 'pillars-1-2', name: 'Create a new pillar', route: '/pillars' },
        ],
      },
      {
        id: 'pillars-2',
        name: 'LLM Feedback for your Pillar',
        description: 'Generate and act on LLM feedback for your first pillar.',
        route: '/pillars',
        substeps: [
          {
            id: 'pillars-2-1',
            name: 'Generate LLM feedback for your first pillar',
            route: '/pillars',
          },
          {
            id: 'pillars-2-2',
            name: 'Fix a pillar issue with AI',
            route: '/pillars',
          },
        ],
      },
      {
        id: 'pillars-3',
        name: 'Get feedback on a new core idea',
        description: 'Write a core idea, add additional features and generate LLM feedback.',
        route: '/pillars',
        substeps: [
          {
            id: 'pillars-3-1',
            name: 'Write a new core idea, add additional features and then generate LLM feedback',
            route: '/pillars',
          },
        ],
      },
      {
        id: 'pillars-4',
        name: 'Discover additional LLM features',
        description: 'Generate feedback and learn how to interpret it.',
        route: '/pillars',
        substeps: [
          { id: 'pillars-4-1', name: 'Coverage', route: '/pillars' },
          { id: 'pillars-4-2', name: 'Contradictions', route: '/pillars' },
          { id: 'pillars-4-3', name: 'Additions', route: '/pillars' },
        ],
      },
    ],
  },
  {
    id: 'player-experience',
    title: 'Player Experience',
    folder: 'Design & Validation',
    completionMessage:
      'Player Experience complete! Your PX chart and node graph are looking solid. Head over to Player Expectations to validate your design.',
    steps: [
      {
        id: 'px-1',
        name: 'Create your first chart',
        description: 'Build your first chart and understand the canvas.',
        route: '/pxcharts',
        substeps: [
          { id: 'px-1-1', name: 'Open Charts page', route: '/pxcharts' },
          { id: 'px-1-2', name: 'Create a new chart', route: '/pxcharts' },
          { id: 'px-1-3', name: 'Open chart by clicking on its name', route: '/pxcharts' },
          { id: 'px-1-4', name: 'Add a new container via the Add Icon', route: '/pxcharts' },
          { id: 'px-1-5', name: 'Add another container', route: '/pxcharts' },
          { id: 'px-1-6', name: 'Connect both containers', route: '/pxcharts' },
        ],
      },
      {
        id: 'px-2',
        name: 'Setup your first node',
        description: 'Add nodes, connect them, and attach components.',
        route: '/pxnodes',
        substeps: [
          { id: 'px-2-1', name: 'Add a Component Definition', route: '/pxcomponentdefinitions' },
          { id: 'px-2-2', name: 'Create your first node', route: '/pxnodes' },
          { id: 'px-2-3', name: 'Add a component to your new node', route: '/pxnodes' },
          {
            id: 'px-2-4',
            name: 'Open a chart and add a node to any container',
            route: '/pxcharts',
          },
        ],
      },
    ],
  },
  {
    id: 'player-expectations',
    title: 'Player Expectations',
    folder: 'Design & Validation',
    completionMessage:
      "Validation done! You've captured and reviewed your player expectations. Why not explore the Movie Script Evaluator next?",
    steps: [
      {
        id: 'pe-1',
        name: 'Check out Player Expectations',
        description: 'Open the page and inspect the sentiment analysis.',
        route: '/player-expectations',
        substeps: [
          { id: 'pe-1-1', name: 'Open Player Expectations Page', route: '/player-expectations' },
          { id: 'pe-1-2', name: 'Inspect Sentiment Analysis', route: '/sentiments' },
        ],
      },
    ],
  },
  {
    id: 'movie-script-evaluator',
    title: 'Movie Script Evaluator',
    folder: 'Discover More',
    completionMessage:
      "You've completed the Movie Script Evaluator workflow! You're now fully equipped to evaluate scripts for virtual production.",
    steps: [
      {
        id: 'mse-1',
        name: 'Have a look at Movie Script Evaluator',
        description: 'Open the Movie Script Evaluator and explore.',
        route: '/movie-script-evaluator',
        substeps: [
          {
            id: 'mse-1-1',
            name: 'Open Movie Script Evaluator',
            route: '/movie-script-evaluator',
          },
        ],
      },
    ],
  },
]

export const ONBOARDING_TEMPLATE: PhaseTemplate = {
  id: 'user-onboarding',
  title: 'Getting Started',
  folder: 'Onboarding',
  completionMessage:
    "You've completed the Getting Started workflow! Your first project is ready — open it and begin your design journey.",
  steps: [
    {
      id: 'user-onb-1',
      name: 'Create Account and Log In',
      description: 'Sign up for a free account and log in to pix:e.',
      route: '/login',
      substeps: [
        { id: 'user-onb-1-1', name: 'Open the login page', route: '/login' },
        { id: 'user-onb-1-2', name: 'Create an account or log in', route: '/login' },
      ],
    },
    {
      id: 'user-onb-2',
      name: 'Create your first project',
      description: 'Set up a project so you can use the project workflows.',
      route: '/create',
      substeps: [
        { id: 'user-onb-2-0', name: 'Open the Create page', route: '/create' },
        { id: 'user-onb-2-1', name: 'Project Information', route: '/create' },
        { id: 'user-onb-2-2', name: 'Project Details', route: '/create' },
        { id: 'user-onb-2-3', name: 'Review Project Settings', route: '/create' },
      ],
    },
    {
      id: 'user-onb-3',
      name: 'Done',
      description: "You're ready to go!",
      route: '/dashboard',
      substeps: [],
    },
  ],
}

function instantiateSubstep(t: SubstepTemplate, isFirst: boolean): Substep {
  const now = new Date().toISOString()
  return {
    id: t.id,
    name: t.name,
    description: t.description,
    route: t.route,
    status: isFirst ? 'active' : 'pending',
    started_at: isFirst ? now : null,
    finished_at: null,
    timeSpentSeconds: 0,
  }
}

function instantiateStep(t: StepTemplate, isFirst: boolean): WorkflowStep {
  const now = new Date().toISOString()
  return {
    id: t.id,
    name: t.name,
    description: t.description,
    route: t.route,
    orderIndex: 0,
    status: isFirst ? 'active' : 'pending',
    started_at: isFirst ? now : null,
    finished_at: null,
    timeSpentSeconds: 0,
    substeps: t.substeps.map((s, i) => instantiateSubstep(s, isFirst && i === 0)),
  }
}

function instantiatePhase(
  phase: PhaseTemplate,
  projectId: string,
  isFirstPhase: boolean,
): WorkflowInstance {
  const now = new Date().toISOString()
  return {
    id: `wf-${projectId}-${phase.id}`,
    projectId,
    started_at: now,
    finished_at: null,
    currentStepIndex: 0,
    meta: { scope: 'project', title: phase.title, folder: phase.folder },
    steps: phase.steps.map((s, i) => {
      const step = instantiateStep(s, isFirstPhase && i === 0)
      step.orderIndex = i
      return step
    }),
  }
}

function markPhaseComplete(instance: WorkflowInstance): WorkflowInstance {
  const now = new Date().toISOString()
  return {
    ...instance,
    finished_at: now,
    currentStepIndex: instance.steps.length - 1,
    steps: instance.steps.map((step) => ({
      ...step,
      status: 'complete' as StepStatus,
      started_at: step.started_at ?? now,
      finished_at: now,
      substeps: step.substeps.map((ss) => ({
        ...ss,
        status: 'complete' as StepStatus,
        started_at: ss.started_at ?? now,
        finished_at: now,
      })),
    })),
  }
}

export function createProjectWorkflows(
  projectId: string,
  onboardingAlreadyDone: boolean,
  completedUserOnboarding?: WorkflowInstance,
): WorkflowInstance[] {
  const phaseInstances = WORKFLOW_TEMPLATE.map((phase, index) => {
    const isFirstPhase = index === 0
    const instance = instantiatePhase(phase, projectId, isFirstPhase && !onboardingAlreadyDone)
    if (isFirstPhase && onboardingAlreadyDone) {
      return markPhaseComplete(instance)
    }
    return instance
  })

  if (completedUserOnboarding) {
    const snapshot: WorkflowInstance = {
      ...JSON.parse(JSON.stringify(completedUserOnboarding)),
      id: `wf-${projectId}-user-onboarding`,
      projectId,
    }
    return [snapshot, ...phaseInstances]
  }

  return phaseInstances
}

export function createOnboardingWorkflow(): WorkflowInstance {
  const now = new Date().toISOString()
  return {
    id: 'wf-user-onboarding',
    projectId: 'user',
    started_at: now,
    finished_at: null,
    currentStepIndex: 0,
    meta: { scope: 'user', title: ONBOARDING_TEMPLATE.title, folder: ONBOARDING_TEMPLATE.folder },
    steps: ONBOARDING_TEMPLATE.steps.map((s, i) => {
      const step = instantiateStep(s, i === 0)
      step.orderIndex = i
      return step
    }),
  }
}

export class WorkflowApiEmulator {
  private projectWorkflows: Record<string, WorkflowInstance[]> = {}
  private userWorkflows: Record<string, WorkflowInstance> = {}
  private activeWorkflowIds: Record<string, string> = {}

  constructor() {
    // Only seed a fresh onboarding workflow as a default.
    // importState() will overwrite this if persisted state exists.
    this.userWorkflows['default'] = createOnboardingWorkflow()
  }

  // ── Persistence ────────────────────────────────────────────────────────────

  exportState(): unknown {
    return JSON.parse(
      JSON.stringify({
        projectWorkflows: this.projectWorkflows,
        userWorkflows: this.userWorkflows,
        activeWorkflowIds: this.activeWorkflowIds,
      }),
    )
  }

  importState(state: unknown): void {
    if (!state || typeof state !== 'object') return
    const s = state as Record<string, unknown>

    if (s.projectWorkflows && typeof s.projectWorkflows === 'object') {
      this.projectWorkflows = JSON.parse(JSON.stringify(s.projectWorkflows)) as Record<
        string,
        WorkflowInstance[]
      >
    }
    if (s.userWorkflows && typeof s.userWorkflows === 'object') {
      this.userWorkflows = JSON.parse(JSON.stringify(s.userWorkflows)) as Record<
        string,
        WorkflowInstance
      >
      // Ensure a default onboarding workflow always exists
      if (!this.userWorkflows['default']) {
        this.userWorkflows['default'] = createOnboardingWorkflow()
      }
    }
    if (s.activeWorkflowIds && typeof s.activeWorkflowIds === 'object') {
      this.activeWorkflowIds = JSON.parse(JSON.stringify(s.activeWorkflowIds)) as Record<
        string,
        string
      >
    }
  }

  // ── Active workflow id ─────────────────────────────────────────────────────

  getActiveWorkflowId(scopeKey: string): string | null {
    return this.activeWorkflowIds[scopeKey] ?? null
  }

  setActiveWorkflowId(scopeKey: string, id: string | null): void {
    if (id) {
      this.activeWorkflowIds[scopeKey] = id
    } else {
      const { [scopeKey]: _, ...rest } = this.activeWorkflowIds
      this.activeWorkflowIds = rest
    }
  }

  // ── Project workflows ──────────────────────────────────────────────────────

  async getWorkflowsByProjectId(projectId: string): Promise<WorkflowInstance[]> {
    const list = this.projectWorkflows[projectId]
    return list ? JSON.parse(JSON.stringify(list)) : []
  }

  async seedProject(
    projectId: string,
    onboardingAlreadyDone: boolean,
  ): Promise<WorkflowInstance[]> {
    const completedOnboarding = this.userWorkflows['default']
      ? markPhaseComplete(JSON.parse(JSON.stringify(this.userWorkflows['default'])))
      : undefined
    const instances = createProjectWorkflows(projectId, onboardingAlreadyDone, completedOnboarding)
    this.projectWorkflows[projectId] = JSON.parse(JSON.stringify(instances))
    return JSON.parse(JSON.stringify(instances))
  }

  async saveWorkflow(workflow: WorkflowInstance): Promise<WorkflowInstance> {
    if (workflow.projectId === 'user') {
      this.userWorkflows['default'] = JSON.parse(JSON.stringify(workflow))
      return JSON.parse(JSON.stringify(workflow))
    }

    const list = this.projectWorkflows[workflow.projectId] ?? []
    const idx = list.findIndex((w) => w.id === workflow.id)
    if (idx === -1) list.push(JSON.parse(JSON.stringify(workflow)))
    else list[idx] = JSON.parse(JSON.stringify(workflow))
    this.projectWorkflows[workflow.projectId] = list
    return JSON.parse(JSON.stringify(workflow))
  }

  // ── User onboarding workflow ───────────────────────────────────────────────

  async getUserOnboardingWorkflow(userId = 'default'): Promise<WorkflowInstance | null> {
    const w = this.userWorkflows[userId]
    return w ? JSON.parse(JSON.stringify(w)) : null
  }

  async completeOnboardingWorkflow(userId = 'default'): Promise<void> {
    const w = this.userWorkflows[userId]
    if (!w) return
    const completed = markPhaseComplete(w)
    this.userWorkflows[userId] = completed

    for (const [projectId, list] of Object.entries(this.projectWorkflows)) {
      const snapshotId = `wf-${projectId}-user-onboarding`
      const idx = list.findIndex((x) => x.id === snapshotId)
      const fresh: WorkflowInstance = {
        ...JSON.parse(JSON.stringify(completed)),
        id: snapshotId,
        projectId,
      }
      if (idx !== -1) {
        list[idx] = fresh
      } else {
        list.unshift(fresh)
      }
    }
  }

  reset() {
    this.projectWorkflows = {}
    this.userWorkflows = {}
    this.activeWorkflowIds = {}
  }
}
