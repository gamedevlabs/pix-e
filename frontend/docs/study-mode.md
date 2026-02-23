# Study / Mock Mode

pix:e can run in a fully offline “study prototype” mode.

In this mode, the app:

- Uses **local JSON files** in `public/mock/` for baseline data.
- Persists all study/project changes to **localStorage**.
- Supports **export/import** to move a study session between machines.
- Avoids backend auth and avoids calling the API.

## Switching modes

The mode is controlled by:

- `NUXT_PUBLIC_DATA_MODE=mock` (default)
- `NUXT_PUBLIC_DATA_MODE=real`

If the environment variable is **missing or invalid**, the app **defaults to `mock`**.

The value is read via `useRuntimeConfig().public` in `app/composables/useDataMode.ts`.

## Mock data location

Baseline JSON lives here:

- `frontend/public/mock/projects.json`
- `frontend/public/mock/workflows.json`
- `frontend/public/mock/pillars.json`
- `frontend/public/mock/pxcharts.json`
- `frontend/public/mock/sentiments.json`
- `frontend/public/mock/player-expectations.json`

These files are loaded client-side and only used to seed localStorage on first run.

## localStorage keys

All study persistence lives under the namespace:

- `pixe.study.v1:state`

This stores a JSON object with:

- `schemaVersion`
- `participantId`
- `lastSavedAt`
- `projects`
- optional workflow snapshot data

## Export / Import

Open the **Study** overlay (bottom-left) in mock mode.

### Export

Creates a downloadable JSON file with:

- `schemaVersion`
- `participantId`
- `timestamp`
- `state` (full persisted session state)

### Import

Select a previously exported JSON file.
The overlay validates `schemaVersion` and restores the stored state.

### Reset

“Reset session” wipes the stored state and reseeds from the baseline JSON in `public/mock/`.
The participant id is preserved.

## Vercel / deployments

For a backend-free prototype deployment, do **nothing**: the app defaults to mock mode.

To enable existing backend behavior later, set:

- `NUXT_PUBLIC_DATA_MODE=real`
- plus whatever API/DB environment variables your backend requires.
