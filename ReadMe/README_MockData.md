# Mock Data

The frontend currently runs without a backend. All data lives in `app/mock_data/` as in-memory emulators or static data exports.

## Files

| File | What it provides |
|------|------------------|
| `mock_projects.ts` | `ProjectApiEmulator` — projects, with full CRUD persisted in memory. |
| `mock_workflow.ts` | `WorkflowApiEmulator` + `WORKFLOW_TEMPLATE` + `ONBOARDING_TEMPLATE` — onboarding and per-project workflows. |
| `mock_recent-activity.ts` | Static feed used by the dashboard's Recent Activity card. |
| `mock_ai-insights.ts` | Static items used by the AI Insights card. |
| `mock_whats-new.ts` | Static items for the What's New card. |
| `mock_external-links.ts` | URLs used for the Wiki / Discord links in the sidebar footer. |

## Where they're consumed

- `mock_projects.ts` → `composables/useProjectHandler.ts`
- `mock_workflow.ts` → `composables/useProjectWorkflow.ts`
- The static mocks are imported directly by the cards/pages that render them.

The `MockDataBadge` component is shown on cards backed by mock data so it's visible at a glance which UI is mocked.

## Connecting a real backend (Getting Started)

Each emulator class exposes the same async API as a real client (e.g. `fetchAll`, `fetchById`, `create`, `update`, `delete`).

1. Replace the emulator's method bodies with `$fetch` (or your HTTP client) calls to the backend.
2. Keep the public method signatures unchanged — the composables that consume them won't need to change.
3. Remove the `MockDataBadge` from cards once they read live data.

The emulators are the only files that need to change. Each starts with a `TODO: Connect to real backend` comment marking the seam.

## Static mock files

`mock_recent-activity.ts`, `mock_ai-insights.ts`, `mock_whats-new.ts`, and `mock_external-links.ts` are simple data exports. Replace the export with a `useFetch`/composable wrapper when a real endpoint is available, then update the consuming card to await it.
