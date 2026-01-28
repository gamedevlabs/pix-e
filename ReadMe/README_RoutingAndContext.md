# Routing and Project Context System

## Overview

The pix:e application uses a **query-parameter-based routing system** with automatic project context management. This approach was chosen over nested routes because it provides better flexibility and simpler state management in Nuxt 3.

## Routing Scheme

All project-specific routes follow this pattern:

```
/[module]?id=[projectId]
```

### Examples:
- `/dashboard?id=pixe` - Dashboard for project "pixe"
- `/pillars?id=29673` - Pillars module for project "29673"
- `/pxcharts?id=pixe` - PxCharts module for project "pixe"
- `/player-expectations?id=pixe` - Player Expectations dashboard
- `/pxnodes/[nodeId]?id=pixe` - Specific node detail page with project context

## Project Context Management

### 1. Project Handler Composable (`useProjectHandler`)

The central state management for projects is handled by `useProjectHandler()`, which provides:

**State:**
- `currentProjectId` - The currently selected project ID
- `currentProject` - The full project object
- `projects` - List of all available projects
- `isProjectSelected` - Computed boolean indicating if a project is active

**Actions:**
- `selectProject(projectOrId)` - Set the current project
- `unselectProject()` - Clear the current project
- `switchProject(id)` - Switch to a different project and navigate to its dashboard
- `syncProjectFromUrl()` - Sync project context from URL query parameters
- `fetchProjects()` - Load all projects
- `createProject(data)` - Create a new project
- `updateProject(id, data)` - Update a project
- `deleteProject(id)` - Delete a project

### 2. Middleware System

#### Authentication Middleware (`authentication.ts`)
- Checks if the user is logged in
- Redirects to `/login` if not authenticated
- Preserves the intended destination URL

#### Project Context Middleware (`project-context.ts`)
- Ensures a project is selected before accessing project-specific modules
- Syncs the project context from URL query parameters
- **Validates that the project exists** - shows error notification if project ID is invalid
- **Shows warning notification** if user tries to access a module without selecting a project
- Redirects to `/` (projects list) if no project is selected or project doesn't exist
- Automatically sets the project context when a valid `?id=` parameter is present

### 3. Page Protection

All project-specific pages use both middleware:

```typescript
definePageMeta({
  middleware: ['authentication', 'project-context'],
})
```

**Protected Pages:**
- `/dashboard` - Project dashboard
- `/pillars` - Design pillars
- `/player-expectations` - Player expectations dashboard
- `/sentiments` - Sentiment analysis
- `/pxcharts` - PxCharts module and detail pages
- `/pxnodes` - PxNodes module and detail pages
- `/pxcomponents` - PxComponents module and detail pages
- `/pxcomponentdefinitions` - Component definitions module

**Unprotected Pages:**
- `/` - Projects list (home/index)
- `/login` - Login page
- `/create` - Create new project
- `/edit` - Edit project settings
- `/movie-script-evaluator` - Standalone tool (no project context required)

## Navigation Flow

### 1. User Selects a Project
```
User clicks project card → switchProject(id) → navigateTo('/dashboard?id=projectId')
```

### 2. User Navigates to a Module
```
User clicks sidebar link → Navigate to /module?id=currentProjectId
```

### 3. Middleware Execution Order
```
1. Authentication middleware checks login status
2. Project-context middleware checks/syncs project from URL
3. Page loads with guaranteed project context
```

### 4. "No Project" Guard Behavior
If a user tries to access a protected module without a project:
- The `project-context` middleware detects no `?id=` parameter
- User is redirected to `/` (projects list)
- User sees all available projects and must select one

## Layout and Sidebar

The sidebar visibility is controlled by computed logic in `layouts/default.vue`:

**Sidebar Shows When:**
- User is logged in AND
- A project is selected (via `currentProjectId` or URL `?id=` parameter) AND
- Current route is not explicitly hidden (e.g., `/`, `/login`, `/create`, `/movie-script-evaluator`)

**Sidebar Hides When:**
- User is not logged in OR
- No project is selected OR
- On specific routes (home, login, create, movie-script-evaluator)

## Adding a New Project-Specific Module

1. Create your page in `app/pages/[module-name].vue`
2. Add the middleware:
   ```typescript
   definePageMeta({
     middleware: ['authentication', 'project-context'],
   })
   ```
3. Access project context:
   ```typescript
   const { currentProject, currentProjectId } = useProjectHandler()
   ```
4. Add navigation link in `layouts/default.vue`:
   ```typescript
   { label: 'My Module', icon: 'i-lucide-icon', to: `/my-module${projectQuery.value}` }
   ```


## Error Handling

The system provides user-friendly notifications for common routing issues:

### No Project Selected
**Scenario:** User navigates to a project-required module without `?id=` parameter
**Notification:** ⚠️ Warning - "No Project Selected - Please select a project to use this module"
**Action:** Redirects to projects list

### Invalid Project ID
**Scenario:** User navigates with a project ID that doesn't exist (e.g., `?id=1234`)
**Notification:** ❌ Error - "Project Not Found - Project '1234' does not exist"
**Action:** Redirects to projects list

### Valid Navigation
**Scenario:** User navigates with a valid project ID
**Notification:** None (seamless navigation)
**Action:** Loads the module with project context
