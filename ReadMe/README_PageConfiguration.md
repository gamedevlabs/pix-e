# Page Configuration Guide

## Overview

Each page in pix:e now has a standardized configuration section at the top of the `<script setup>` block. This makes it easy for developers to configure their module's behavior without hunting through multiple files.

## Page Configuration Section

Every page should include this configuration block at the very top of the script:

```typescript
<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  middleware: ['authentication', 'project-context'],  // Optional, based on page type
  pageConfig: {
    type: 'project-required',  // or 'standalone' or 'public'
    showSidebar: true,         // Optional, defaults based on type
    title: 'My Module',        // Optional, for navigation/SEO
    icon: 'i-lucide-icon',     // Optional, for navigation
  },
})
// ============================================================================

// Your module code starts here...
const myData = ref()
// ...
</script>
```

## Configuration Options

### `type` (Required)

Defines how the page behaves in relation to project context:

#### `'project-required'`
- **Use for:** Modules that work with project data (Pillars, PxCharts, Dashboard, etc.)
- **Behavior:**
  - Requires `?id=projectId` in URL
  - Automatically redirects to `/` if no project is selected
  - Shows sidebar by default (when user is logged in)
- **Middleware:** `['authentication', 'project-context']`
- **Examples:**
  - `/pillars?id=pixe`
  - `/dashboard?id=29673`
  - `/pxcharts?id=myproject`

#### `'standalone'`
- **Use for:** Tools that don't need project context (Movie Script Evaluator, etc.)
- **Behavior:**
  - Works without a project ID
  - Hides sidebar by default
  - Still requires authentication
- **Middleware:** `['authentication']`
- **Examples:**
  - `/movie-script-evaluator`

#### `'public'`
- **Use for:** Public pages accessible without login (Login, Index/Projects list)
- **Behavior:**
  - No authentication required
  - Hides sidebar
  - No middleware needed
- **Middleware:** None or `[]`
- **Examples:**
  - `/` (projects list)
  - `/login`

### `showSidebar` (Optional)

Explicitly control sidebar visibility:

- `true` - Always show sidebar (if user is logged in with a project)
- `false` - Never show sidebar
- `undefined` - Use default behavior based on page type

**Default behavior by type:**
- `project-required` → `true` (if project selected)
- `standalone` → `false`
- `public` → `false`

### `title` (Optional)

Display name for the page (used for navigation, SEO, etc.)

### `icon` (Optional)

Lucide icon name for navigation items (e.g., `'i-lucide-house'`)

## Complete Examples

### Project-Required Module

```vue
<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Design Pillars',
    icon: 'i-lucide-landmark',
  },
})
// ============================================================================

const { currentProject } = useProjectHandler()
const { items, fetchAll } = usePillars()

onMounted(() => {
  fetchAll()
})
</script>

<template>
  <div>
    <h1>Pillars for {{ currentProject?.name }}</h1>
    <!-- Your component code -->
  </div>
</template>
```

### Standalone Module

```vue
<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  middleware: ['authentication'],
  pageConfig: {
    type: 'standalone',
    showSidebar: false,
    title: 'Movie Script Evaluator',
    icon: 'i-lucide-film',
  },
})
// ============================================================================

const { items, fetchAll } = useMovieScriptEvaluator()

onMounted(() => {
  fetchAll()
})
</script>

<template>
  <div>
    <h1>Movie Script Evaluator</h1>
    <!-- Your component code -->
  </div>
</template>
```

### Public Page

```vue
<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  pageConfig: {
    type: 'public',
    showSidebar: false,
    title: 'Projects',
  },
})
// ============================================================================

const { projects } = useProjectHandler()
</script>

<template>
  <div>
    <h1>Select a Project</h1>
    <!-- Your component code -->
  </div>
</template>
```

## Quick Reference Table

| Page Type | Auth Required | Project Required | Default Sidebar | Middleware |
|-----------|---------------|------------------|-----------------|------------|
| `project-required` | ✅ Yes | ✅ Yes | ✅ Show | `['authentication', 'project-context']` |
| `standalone` | ✅ Yes | ❌ No | ❌ Hide | `['authentication']` |
| `public` | ❌ No | ❌ No | ❌ Hide | None |

## Common Patterns

### Page with Custom Sidebar Behavior

```typescript
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: false,  // Override default to hide sidebar
    title: 'Fullscreen Editor',
  },
})
```

### Page with Optional Project

If you want a page that can work both with and without a project:

```typescript
definePageMeta({
  middleware: ['authentication'],  // No project-context middleware
  pageConfig: {
    type: 'standalone',
    showSidebar: false,
  },
})

// Then manually check for project in your code
const { currentProjectId } = useProjectHandler()

if (currentProjectId.value) {
  // Load project-specific data
} else {
  // Show generic view
}
```

## Troubleshooting

**Problem:** Page redirects to `/` when I access it
- **Solution:** Check if your page type is `project-required` but you're not providing `?id=projectId` in the URL

**Problem:** Sidebar doesn't show when expected
- **Solution:** Verify that:
  1. Page type is `project-required`
  2. User is logged in
  3. Project ID is in the URL query (`?id=...`)
  4. `showSidebar` is not explicitly set to `false`

**Problem:** Page requires authentication when it shouldn't
- **Solution:** Change type to `public` and remove authentication middleware
