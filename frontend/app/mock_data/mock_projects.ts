// TODO: Connect mock data to real backend (project-layer)

import type { Project } from '~/utils/project'

export class ProjectApiEmulator {
  private projects: Project[] = []

  constructor() {
    const now = new Date().toISOString()
    this.projects = [
      {
        id: 'pixe',
        name: 'pix:e',
        shortDescription: 'This project contains all the old data from the other pix:e devs.',
        genre: 'Tool',
        targetPlatform: 'web',
        created_at: '2024-01-01T10:00:00.000Z',
        updated_at: now,
        icon: null,
      },
      {
        id: '29673',
        name: 'Demo Project',
        shortDescription: 'An experimental narrative project with example scenes.',
        genre: 'Narrative, Adventure, Story-Driven',
        targetPlatform: 'desktop, web, console',
        created_at: '2024-06-15T08:30:00.000Z',
        updated_at: '2024-07-18T08:30:00.000Z',
        icon: null,
      },
      {
        id: '1648843',
        name: 'Mobile Game',
        shortDescription: 'Mock mobile-oriented project.',
        genre: 'Puzzle, Casual, Strategy',
        targetPlatform: 'mobile',
        created_at: '2025-02-10T12:00:00.000Z',
        updated_at: '2026-01-03T12:00:00.000Z',
        icon: null,
      },
    ]
  }

  async getAll(): Promise<Project[]> {
    return this.projects.map((p) => ({ ...p }))
  }

  async getById(id: string): Promise<Project | null> {
    const p = this.projects.find((x) => x.id === id)
    return p ? { ...p } : null
  }

  async create(data: Partial<Project>): Promise<Project> {
    const now = new Date().toISOString()
    const newProject: Project = {
      id: data.id || `${Date.now()}`,
      name: data.name || 'Untitled Project',
      shortDescription: data.shortDescription || '',
      genre: data.genre || 'Unknown',
      targetPlatform: (data.targetPlatform as Project['targetPlatform']) ?? 'web',
      created_at: (data.created_at as string) || now,
      updated_at: (data.updated_at as string) || now,
      // carry through optional icon (data URL or URL)
      icon: (data.icon as string | null) ?? null,
    }
    this.projects.push(newProject)
    return { ...newProject }
  }

  async update(id: string, data: Partial<Project>): Promise<Project | null> {
    const idx = this.projects.findIndex((x) => x.id === id)
    if (idx === -1) return null
    const existing = this.projects[idx]!
    // Build a fully-typed Project object, don't spread Partial<Project> over Project
    const updated: Project = {
      id: existing.id,
      name: data.name ?? existing.name,
      shortDescription: data.shortDescription ?? existing.shortDescription,
      genre: data.genre ?? existing.genre,
      targetPlatform: (data.targetPlatform as Project['targetPlatform']) ?? existing.targetPlatform,
      created_at: existing.created_at,
      updated_at: new Date().toISOString(),
      icon: (data.icon as string | null) ?? existing.icon ?? null,
    }
    this.projects[idx] = updated
    return { ...updated }
  }

  async delete(id: string): Promise<boolean> {
    const lenBefore = this.projects.length
    this.projects = this.projects.filter((x) => x.id !== id)
    return this.projects.length < lenBefore
  }
}
