# Pages Overview

Every route in the app and what it does. See README_LayoutAndPages.md for how pages are wired up and README_RoutingAndContext.md for URL rules and middleware.

## Public

| Route | File | Purpose |
|-------|------|---------|
| `/` | `pages/index.vue` | Landing page. Logged-out users see marketing + public modules; logged-in users see their project list. |
| `/login` | `pages/login.vue` | Login. |

## Project lifecycle

| Route | File | Purpose |
|-------|------|---------|
| `/create` | `pages/create/index.vue` | Three-step wizard to create a project. `?duplicate=<id>` pre-fills the form from an existing project. |

## Project-scoped (need `?id=<projectId>`)

| Route | File | Purpose |
|-------|------|---------|
| `/dashboard` | `pages/dashboard/index.vue` | Project home. Project header, module preview cards, workflow, recent activity, AI insights. |
| `/settings` | `pages/settings/index.vue` | Edit project basics, genre, target platforms, icon. Shows read-only metadata. |
| `/pillars` | `pages/pillars.vue` | Manage Design Pillars. |
| `/pxcharts` | `pages/pxcharts/` | List of player-experience charts. `[id]` opens the chart editor. |
| `/pxnodes` | `pages/pxnodes/` | PX nodes list and detail. |
| `/pxcomponents` | `pages/pxcomponents/` | PX components list and detail. |
| `/pxcomponentdefinitions` | `pages/pxcomponentdefinitions/` | Reusable component definitions. |
| `/player-expectations` | `pages/player-expectations.vue` | Aspect + sentiment dashboard for the project. |
| `/player-expectations-landing` | `pages/player-expectations-landing.vue` | Entry/landing page for Player Expectations. |
| `/player-expectations-new/dashboard` | `pages/player-expectations-new/dashboard.vue` | New aspect/sentiment dashboard. |
| `/player-expectations-new/dataset-explorer` | `pages/player-expectations-new/dataset-explorer.vue` | Drill into the underlying dataset. |
| `/player-expectations-new/prior-findings` | `pages/player-expectations-new/prior-findings.vue` | Reference findings. |
| `/player-experience` | `pages/player-experience.vue` | Player experience overview. |
| `/sentiments` | `pages/sentiments.vue` | Sentiment table view. |

## Standalone (auth required, no project)

| Route | File | Purpose |
|-------|------|---------|
| `/movie-script-evaluator` | `pages/movie-script-evaluator/` | LLM script evaluator. Works without a selected project. |
