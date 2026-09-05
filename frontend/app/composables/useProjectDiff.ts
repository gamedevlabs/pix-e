// Structured diff between an exported project file and the current DB state of
// the matched project. Everything is matched BY ID within each collection.

export type DiffStatus = 'new' | 'modified' | 'deleted' | 'unchanged'

export interface FieldChange {
  field: string
  old: unknown
  new: unknown
}

export interface DiffEntry {
  id: string
  name: string
  status: DiffStatus
  changes: FieldChange[]
}

export interface DiffSection {
  key: string
  label: string
  entries: DiffEntry[]
  changeCount: number
}

export interface ProjectDiff {
  fileProjectId: unknown
  sections: DiffSection[]
  metadata: DiffEntry // single "Project metadata" row
  counts: { new: number; modified: number; deleted: number }
}

type Row = Record<string, unknown>
type Payload = Record<string, unknown> & { project?: Row }

// Order + labels mirror the Unity import dialog. Layouts are folded into the
// Containers section (not its own collection).
const COLLECTIONS: { key: string; label: string }[] = [
  // Pillars are diffed like everything else. Their ids are DB-local ints rather
  // than uuids, so the backend rebuilds the set rather than preserving them -
  // see overwrite_project.py. Without this entry the merged payload carried no
  // pillars at all and an overwrite silently kept the target's old ones.
  { key: 'pillars', label: 'Design Pillars' },
  { key: 'px_component_definitions', label: 'Component Definitions' },
  { key: 'px_nodes', label: 'Nodes' },
  { key: 'px_components', label: 'Components' },
  { key: 'px_charts', label: 'Charts' },
  { key: 'px_chart_containers', label: 'Containers' },
  { key: 'px_chart_edges', label: 'Edges' },
  { key: 'px_key_definitions', label: 'Keys' },
  { key: 'px_key_assignments', label: 'Key Assignments' },
  { key: 'px_lock_definitions', label: 'Locks' },
  { key: 'px_lock_assignments', label: 'Lock Assignments' },
]

const LAYOUT_FIELDS = ['position_x', 'position_y', 'width', 'height']
const META_FIELDS = ['name', 'description', 'genres', 'target_platforms']

function rows(payload: Payload, key: string): Row[] {
  const v = payload[key]
  return Array.isArray(v) ? (v as Row[]) : []
}

function byId(list: Row[]): Map<string, Row> {
  const m = new Map<string, Row>()
  for (const r of list) m.set(String(r.id), r)
  return m
}

// Stable comparison; arrays compared order-insensitively (e.g. unlocked_by).
function norm(v: unknown): string {
  if (Array.isArray(v)) return JSON.stringify([...v].map((x) => JSON.stringify(x)).sort())
  return JSON.stringify(v ?? null)
}

function fieldChanges(fileRow: Row, dbRow: Row, skip: string[] = ['id']): FieldChange[] {
  const keys = new Set([...Object.keys(fileRow), ...Object.keys(dbRow)])
  const out: FieldChange[] = []
  for (const k of keys) {
    if (skip.includes(k)) continue
    if (norm(fileRow[k]) !== norm(dbRow[k]))
      out.push({ field: k, old: dbRow[k], new: fileRow[k] })
  }
  return out
}

function labeler(fileData: Payload, dbData: Payload) {
  const names = new Map<string, string>()
  const put = (key: string, field = 'name') => {
    for (const r of [...rows(fileData, key), ...rows(dbData, key)])
      names.set(`${key}:${r.id}`, String(r[field] ?? r.id))
  }
  put('px_nodes')
  put('px_component_definitions')
  put('px_charts')
  put('px_chart_containers')
  put('px_key_definitions')
  put('px_lock_definitions')

  const nm = (key: string, id: unknown) =>
    id == null ? '—' : (names.get(`${key}:${id}`) ?? String(id))

  return (key: string, row: Row): string => {
    switch (key) {
      case 'px_components':
        return `${nm('px_nodes', row.node)} · ${nm('px_component_definitions', row.definition)}`
      case 'px_key_assignments':
        return `${nm('px_nodes', row.node)} · ${nm('px_key_definitions', row.definition)}`
      case 'px_chart_edges':
        return `${nm('px_chart_containers', row.source)} → ${nm('px_chart_containers', row.target)}`
      case 'px_lock_assignments':
        return `${nm('px_lock_definitions', row.definition)} × ${row.count ?? ''}`
      default:
        return String(row.name ?? row.id)
    }
  }
}

export function useProjectDiff() {
  function computeDiff(fileData: Payload, dbData: Payload): ProjectDiff {
    const nameOf = labeler(fileData, dbData)
    const counts = { new: 0, modified: 0, deleted: 0 }
    const sections: DiffSection[] = []

    // Layouts keyed by container id, folded into the Containers section.
    const fileLayouts = byId(rows(fileData, 'px_chart_container_layouts'))
    const dbLayouts = byId(rows(dbData, 'px_chart_container_layouts'))
    // ponytail: layout matched by `container`, not its DB-local numeric id.
    const relayout = (m: Map<string, Row>) => {
      const out = new Map<string, Row>()
      for (const r of m.values()) out.set(String(r.container), r)
      return out
    }
    const fileLayoutByContainer = relayout(fileLayouts)
    const dbLayoutByContainer = relayout(dbLayouts)

    for (const { key, label } of COLLECTIONS) {
      const fileMap = byId(rows(fileData, key))
      const dbMap = byId(rows(dbData, key))
      const ids = new Set([...fileMap.keys(), ...dbMap.keys()])
      const entries: DiffEntry[] = []

      for (const id of ids) {
        const f = fileMap.get(id)
        const d = dbMap.get(id)
        let status: DiffStatus
        let changes: FieldChange[] = []
        let source: Row

        if (f && d) {
          changes = fieldChanges(f, d)
          if (key === 'px_chart_containers') {
            const fl = fileLayoutByContainer.get(id)
            const dl = dbLayoutByContainer.get(id)
            if (fl && dl)
              changes.push(...fieldChanges(fl, dl, ['id', 'container']))
            else if (fl || dl)
              for (const lf of LAYOUT_FIELDS)
                changes.push({ field: lf, old: dl?.[lf], new: fl?.[lf] })
          }
          status = changes.length ? 'modified' : 'unchanged'
          source = f
        } else if (f) {
          status = 'new'
          source = f
        } else {
          status = 'deleted'
          source = d as Row
        }

        if (status === 'new') counts.new++
        else if (status === 'modified') counts.modified++
        else if (status === 'deleted') counts.deleted++

        entries.push({ id, name: nameOf(key, source), status, changes })
      }

      entries.sort((a, b) => rank(a.status) - rank(b.status) || a.name.localeCompare(b.name))
      const changeCount = entries.filter((e) => e.status !== 'unchanged').length
      if (entries.length) sections.push({ key, label, entries, changeCount })
    }

    // Project metadata as its own single-row section.
    const fileMeta = (fileData.project ?? {}) as Row
    const dbMeta = (dbData.project ?? {}) as Row
    const metaChanges = fieldChanges(fileMeta, dbMeta, ['id', ...allBut(META_FIELDS, fileMeta, dbMeta)])
    const metadata: DiffEntry = {
      id: 'project',
      name: String(fileMeta.name ?? 'Project'),
      status: metaChanges.length ? 'modified' : 'unchanged',
      changes: metaChanges,
    }
    if (metadata.status === 'modified') counts.modified++

    return { fileProjectId: fileMeta.id, sections, metadata, counts }
  }

  // Build the merged desired state to POST to the overwrite endpoint.
  // `ticks` holds "collectionKey:id" for each change the user kept, plus
  // "project:meta" for project metadata.
  function buildMergedPayload(
    fileData: Payload,
    dbData: Payload,
    ticks: Set<string>,
  ): Payload {
    const dbMeta = (dbData.project ?? {}) as Row
    const fileMeta = (fileData.project ?? {}) as Row
    const merged: Payload = {
      version: 2,
      project: ticks.has('project:meta') ? { ...fileMeta } : { ...dbMeta },
    }
    // Preserve the DB project id regardless (match-only, read-only server-side).
    ;(merged.project as Row).id = dbMeta.id

    // The concept is a single row, not a collection, so it follows the project
    // metadata tick rather than getting one of its own. Omitting it would drop
    // the target's concept on every overwrite.
    merged.game_concept = ticks.has('project:meta') ? fileData.game_concept : dbData.game_concept

    const containerSource = new Map<string, 'file' | 'db'>()

    for (const { key } of COLLECTIONS) {
      const fileMap = byId(rows(fileData, key))
      const dbMap = byId(rows(dbData, key))
      const ids = new Set([...fileMap.keys(), ...dbMap.keys()])
      const out: Row[] = []

      for (const id of ids) {
        const f = fileMap.get(id)
        const d = dbMap.get(id)
        const ticked = ticks.has(`${key}:${id}`)
        let chosen: Row | undefined
        let src: 'file' | 'db' | undefined

        if (f && d) {
          const changed = fieldChanges(f, d).length > 0 || layoutChanged(key, id, fileData, dbData)
          if (!changed) {
            chosen = f
            src = 'file'
          } else {
            chosen = ticked ? f : d
            src = ticked ? 'file' : 'db'
          }
        } else if (f) {
          if (ticked) {
            chosen = f
            src = 'file'
          }
        } else if (d) {
          if (!ticked) {
            chosen = d
            src = 'db'
          }
        }

        if (chosen) {
          out.push(chosen)
          if (key === 'px_chart_containers' && src) containerSource.set(id, src)
        }
      }
      merged[key] = out
    }

    // Layouts follow their container's chosen source.
    const fileLayouts = new Map<string, Row>()
    const dbLayouts = new Map<string, Row>()
    for (const r of rows(fileData, 'px_chart_container_layouts')) fileLayouts.set(String(r.container), r)
    for (const r of rows(dbData, 'px_chart_container_layouts')) dbLayouts.set(String(r.container), r)

    const layouts: Row[] = []
    for (const [containerId, src] of containerSource) {
      const layout = src === 'file' ? fileLayouts.get(containerId) : dbLayouts.get(containerId)
      if (layout) layouts.push(layout)
    }
    merged.px_chart_container_layouts = layouts

    return merged
  }

  return { computeDiff, buildMergedPayload }
}

function layoutChanged(key: string, id: string, fileData: Payload, dbData: Payload): boolean {
  if (key !== 'px_chart_containers') return false
  const fl = rows(fileData, 'px_chart_container_layouts').find((r) => String(r.container) === id)
  const dl = rows(dbData, 'px_chart_container_layouts').find((r) => String(r.container) === id)
  if (!fl && !dl) return false
  if (!fl || !dl) return true
  return LAYOUT_FIELDS.some((f) => norm(fl[f]) !== norm(dl[f]))
}

function allBut(fields: string[], a: Row, b: Row): string[] {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)])
  return [...keys].filter((k) => !fields.includes(k))
}

function rank(s: DiffStatus): number {
  return { new: 0, modified: 1, deleted: 2, unchanged: 3 }[s]
}
