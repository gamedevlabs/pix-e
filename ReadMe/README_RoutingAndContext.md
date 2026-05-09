# Routing & Project Context

How project-scoped routes work and how the current project flows through the app.

## URL pattern

Project-scoped routes carry the project id as a query parameter:

```
/[module]?id=[projectId]
```

Examples: `/dashboard?id=pixe`, `/pillars?id=pixe`, `/settings?id=pixe`.

Why query params instead of nested routes: simpler state in Nuxt, easier link sharing, no route-tree duplication per project.

## useProjectHandler

Singleton composable that holds project state. Use it anywhere you need the current project.

State:
- `currentProjectId` — the selected project id
- `currentProject` — the full project object
- `projects` — list of all projects
- `isProjectSelected` — derived boolean

Actions:
- `selectProject(projectOrId)` — set the current project
- `unselectProject()`
- `switchProject(id)` — set the current project and navigate to its dashboard
- `syncProjectFromUrl()` — copy `?id=` from the URL into state
- `fetchProjects()`, `fetchProjectById(id)`, `createProject(data)`, `updateProject(id, data)`, `deleteProject(id)`

The data is currently served from `mock_data/mock_projects.ts` — see README_MockData.md.

## Middleware

`authentication` — redirects to `/login` if no user is logged in.

`project-context` — for `project-required` pages: reads `?id=` from the URL, checks that the project exists, syncs `useProjectHandler`. Redirects to `/` if the id is missing or invalid.

Pages opt in via `definePageMeta`:

```ts
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: { type: 'project-required', /* ... */ },
})
```

## Navigation flow

1. User picks a project on `/` → `switchProject(id)` → `/dashboard?id=...`
2. User clicks a sidebar link → navigated to `/[module]?id=...` (the sidebar appends the current project id automatically; see `useNavigationLinks`)
3. Middleware order on every navigation: `authentication` → `project-context` → page

## Sidebar visibility

Decided by `useSidebarVisibility`. The default per page type lives in the table in README_LayoutAndPages.md. A page can override with `pageConfig.showSidebar`.
