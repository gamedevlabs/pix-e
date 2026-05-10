# Layout & Pages

How the app is structured, how to add a new page, and what each page must declare.

## Folder structure

```
app/
  layouts/default.vue        Shell: header + sidebar + content slot
  pages/                     One folder per route (Nuxt file-based routing)
  components/
    layout/                  AppHeader, AppSidebar
    landing/                 Landing page parts
    create-project/          Create-project wizard parts
    settings/                Settings page cards
    dashboard/               Dashboard module cards + project header
    cards/                   Reusable cards (workflow, history, insights, ...)
  composables/               State + behaviour per feature
  middleware/                Route guards (authentication, project-context)
  mock_data/                 In-memory data emulators (see README_MockData.md)
  types/                     Shared types (e.g. PageConfig)
  utils/                     Pure helpers + .d.ts type definitions
```

## How a page is rendered

`layouts/default.vue` is the only layout. It composes `AppHeader`, an optional `AppSidebar`, and the page slot. The sidebar visibility and the navigation tree are both derived from each page's `pageConfig` — there is no manually maintained nav list.

Key composables behind the layout:

- `useSidebarVisibility` — decides whether to render the sidebar for the current route.
- `useNavigationLinks` — builds the sidebar nav tree from every page's `pageConfig`.
- `useOnboardingProgress` — auto-completes the "Getting Oriented" workflow as the user explores.

## Adding a new page (Getting Started)

1. Create `app/pages/my-module/index.vue`.
2. Add `pageConfig` at the top of `<script setup>`:

```vue
<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    title: 'My Module',
    icon: 'i-lucide-star',
    navGroup: 'main',
    navOrder: 5,
    showInNav: true,
  },
})
</script>
```

3. The page now appears in the sidebar automatically. No other file changes needed.

## pageConfig fields

| Field         | Required        | Purpose |
|---------------|-----------------|---------|
| `type`        | yes             | `'project-required'`, `'standalone'`, or `'public'`. Drives sidebar visibility and the project guard. |
| `title`       | yes (for nav)   | Label shown in the sidebar and command palette. |
| `icon`        | yes (for nav)   | Lucide icon name (e.g. `i-lucide-house`). |
| `navGroup`    | optional        | `'main'` (default) or `'tools'` — which sidebar section the link goes in. |
| `navOrder`    | optional        | Sort order within the group. Lower = higher up. |
| `navParent`   | optional        | Parent route path (without leading `/`) when this page is a child item. |
| `showInNav`   | optional        | Set to `false` to omit the page from the sidebar/search. |
| `showSidebar` | optional        | Override the sidebar visibility default for this route. |

## Page types

| Type               | Auth | Needs project | Sidebar default | Middleware |
|--------------------|------|---------------|-----------------|------------|
| `project-required` | yes  | yes           | shown           | `['authentication', 'project-context']` |
| `standalone`       | yes  | no            | hidden          | `['authentication']` |
| `public`           | no   | no            | hidden          | none |

## Header & sidebar

Both live in `components/layout/`.

- `AppHeader.vue` — logo, color mode switch, LLM picker, login/user menu.
- `AppSidebar.vue` — project picker, search button, two navigation menus (main + standalone tools), onboarding trigger, external links footer.
