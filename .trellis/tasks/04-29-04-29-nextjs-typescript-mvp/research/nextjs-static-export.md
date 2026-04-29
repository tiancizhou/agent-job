# Research: Next.js TypeScript static export preview

- **Query**: Research how to structure a minimal Next.js + TypeScript app for static export preview in an AI-generated project context. Cover required files, next.config static export settings, build command, constraints to avoid runtime/server-only features, and how this maps to this repo's lightweight generated-app preview requirement.
- **Scope**: mixed
- **Date**: 2026-04-29

## Findings

### Files Found

| File Path | Description |
|---|---|
| `backend/main.py` | Serves generated project files from `/generated/{app_id}/project/{file_path:path}` using `FileResponse` and `Cache-Control: no-store`; mounts production frontend static files separately. |
| `backend/services/code_service.py` | Validates, saves, reads, and resolves generated project files under `settings.DATA_DIR/apps/{app_id}/project/`; currently allows only selected static suffixes. |
| `backend/services/ai_service.py` | Current generation prompt asks the LLM to output a pure static multi-file frontend project as JSON with `index.html`, `css/style.css`, and `js/app.js`. |
| `frontend/src/components/ChatPanel.vue` | Renders generated app preview in an iframe and opens `/generated/${appId}/project/index.html`. |
| `.trellis/spec/backend/directory-structure.md` | Documents the generated project storage convention `settings.DATA_DIR/apps/{app_id}/project/`. |
| `.trellis/spec/frontend/directory-structure.md` | Documents the current Vue/Vite frontend and preview integration context. |

### Code Patterns

- Generated project files are served one file at a time from the backend route `GET /generated/{app_id}/project/{file_path:path}`. `backend/main.py:49-56` resolves the requested path via `code_service.resolve_project_file()` and returns `FileResponse(target, headers={"Cache-Control": "no-store"})`.
- The preview UI points directly at the generated static entry file. `frontend/src/components/ChatPanel.vue:667-668` defines `projectPreviewUrl(appId: string): string { return `/generated/${appId}/project/index.html` }`.
- The iframe is sandboxed but permits client-side JavaScript and form interactions. `frontend/src/components/ChatPanel.vue:257-262` renders an iframe with `sandbox="allow-scripts allow-forms allow-popups"`.
- Current generated-project validation requires `index.html`, `css/style.css`, and `js/app.js` for new projects. `backend/services/code_service.py:59-65` checks those paths in `parse_project_json_or_raise()`.
- Current generated-project storage is `Path(data_dir) / "apps" / app_id / "project"`. `backend/services/code_service.py:170-171` defines this path.
- Current file safety only permits `.html`, `.css`, `.js`, `.json`, `.txt`, `.md`, and `.svg`. `backend/services/code_service.py:7` defines `ALLOWED_PROJECT_SUFFIXES`; `backend/services/code_service.py:138-153` rejects absolute paths, traversal, Windows drive paths, empty path segments, and unsupported suffixes.
- Current project-size constraints are small: max 20 files and 300 KB per file. `backend/services/code_service.py:8-10` defines `MAX_PROJECT_FILES = 20`, `MAX_CHANGE_FILES = 10`, and `MAX_FILE_BYTES = 300 * 1024`.
- Current LLM prompt is optimized for no-build static output, not source projects requiring a Next.js build. `backend/services/ai_service.py:28-70` requires JSON files containing plain static frontend assets, relative resource paths, mobile-first 375px support, and `/api/generated/{app_id}/data/{collection}` persistence calls.

### Minimal Next.js + TypeScript Static Export Shape

A minimal App Router Next.js + TypeScript project for static export can be structured as:

| File Path | Purpose |
|---|---|
| `package.json` | Declares scripts and dependencies: `next`, `react`, `react-dom`, `typescript`, `@types/node`, `@types/react`, `@types/react-dom`. |
| `next.config.ts` or `next.config.js` | Enables static export via `output: 'export'`; can set image/static path options. |
| `tsconfig.json` | TypeScript config used by Next.js; can be minimal because Next augments defaults. |
| `next-env.d.ts` | Next-generated TypeScript ambient declarations; for an AI-generated project it may be emitted up front or created by `next build`. |
| `app/layout.tsx` | Required root layout for App Router; must render `<html>` and `<body>`. |
| `app/page.tsx` | Required root page rendered as `/index.html` in exported output. |
| `app/globals.css` | Optional global CSS imported by `app/layout.tsx`; useful for the mobile-first styling requirement. |
| `public/*` | Optional static assets copied through to the export output. |

Equivalent minimal Pages Router shape is also possible:

| File Path | Purpose |
|---|---|
| `pages/index.tsx` | Root page. |
| `pages/_app.tsx` | Imports global CSS and wraps pages. |
| `styles/globals.css` | Global CSS. |

For a new MVP, App Router is the current default Next.js structure, but Pages Router remains simpler for some generated projects because it avoids root layout rules.

### `next.config` Static Export Settings

Minimal static export configuration:

```ts
// next.config.ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'export',
}

export default nextConfig
```

Settings relevant to this repo's nested preview URL `/generated/{app_id}/project/index.html`:

```ts
// next.config.ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'export',
  images: { unoptimized: true },
  trailingSlash: false,
}

export default nextConfig
```

- `output: 'export'` makes `next build` write a static export to `out/`.
- `images: { unoptimized: true }` avoids the default Next Image Optimization server dependency if generated code uses `next/image`.
- `trailingSlash` controls whether routes export as `/route.html` or `/route/index.html`; either can work if links and serving rules match. For the current repo, direct `index.html` preview is the key entry.
- `assetPrefix` and `basePath` are usually not appropriate for arbitrary app IDs at generation time unless the generated project knows the exact deployment prefix. Static exports can avoid this by using relative links/assets and plain `public` paths or by not relying on Next-generated absolute asset URLs outside the copied `out/` tree.

### Build Command

Typical commands:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "latest",
    "react": "latest",
    "react-dom": "latest"
  },
  "devDependencies": {
    "typescript": "latest",
    "@types/node": "latest",
    "@types/react": "latest",
    "@types/react-dom": "latest"
  }
}
```

For static export, the build artifact is `out/` after `npm run build`. In an AI-generated preview pipeline, the previewable files are the contents of `out/`, not the source files. The backend would need to serve copied/exported output such as:

```text
out/
├── index.html
├── 404.html
└── _next/static/...
```

### Static Export Constraints: Avoid Runtime / Server-Only Features

Static export requires that all routes can be rendered at build time. Generated apps should avoid or constrain:

- Server-side request-time rendering (`getServerSideProps` in Pages Router) because it requires a Node.js server.
- Route Handlers/API routes (`app/api/*` or `pages/api/*`) because static export has no backend runtime for them.
- Middleware because it runs at request time.
- Dynamic routes without static parameter generation. In App Router, dynamic routes need `generateStaticParams()` for all exported params; in Pages Router, they need `getStaticPaths()` with static paths.
- Runtime cookie/header/session access for page rendering, such as `cookies()` or `headers()` in server components, because exported HTML cannot depend on per-request state.
- Server Actions and other server-only mutation patterns because the generated preview is static and this repo already provides persistence through `/api/generated/{app_id}/data/{collection}`.
- Default optimized `next/image` behavior unless configured with `images.unoptimized = true` or replaced with plain `<img>`.
- Rewrites, redirects, and headers that depend on a Next.js server. Static hosts may need separate host configuration for these, which this repo's generated-file route does not provide.
- Node.js-only modules in client code (`fs`, `path`, direct database clients, server SDKs). Generated interactivity should run in the browser and call existing `/api/...` endpoints with `fetch`.

Client components may use browser-only APIs when marked with `'use client'`, but generated pages should keep persistence and user interaction in browser code that runs after static HTML loads.

### Mapping to This Repo's Lightweight Generated-App Preview Requirement

Current repo behavior is lightweight because generated apps are already static files:

- The model returns file contents as JSON.
- `code_service.save_project()` writes those files under `data/apps/{app_id}/project/`.
- FastAPI serves files from `/generated/{app_id}/project/...` with no build step.
- `ChatPanel.vue` previews `/generated/{app_id}/project/index.html` in a sandboxed iframe.

A Next.js + TypeScript generated-app flow changes the artifact boundary:

1. The AI-generated source project would include Next source files (`package.json`, `next.config`, `app/*` or `pages/*`).
2. A build step would run `npm install`/dependency preparation and `npm run build`.
3. The static export output directory `out/` would become the preview artifact.
4. The backend preview route would need to serve files copied from `out/` into the existing project preview directory, or the route would need to point at the export output directory.
5. The iframe can continue using `/generated/{app_id}/project/index.html` if exported files are placed under `settings.DATA_DIR/apps/{app_id}/project/` with `index.html` at the root.

For the current lightweight preview model, the simplest compatibility target is therefore not "serve a Next.js app" at runtime; it is "generate/build a Next.js source project, then serve only its static `out/` output". The generated app must still follow the repo's existing browser-side persistence rule: call `/api/generated/{app_id}/data/{collection}` from client code instead of using Next API routes or server actions.

### External References

- [Next.js Static Exports documentation](https://nextjs.org/docs/app/building-your-application/deploying/static-exports) — documents `output: 'export'`, `next build` producing `out/`, supported static features, unsupported server/runtime features, and static host behavior.
- [Next.js `next.config.js` `output` option](https://nextjs.org/docs/app/api-reference/config/next-config-js/output) — documents output modes, including static export.
- [Next.js Image component static export note](https://nextjs.org/docs/app/api-reference/components/image#unoptimized) — relevant because default image optimization requires a server unless images are unoptimized or plain `<img>` is used.
- [Next.js App Router project organization](https://nextjs.org/docs/app/getting-started/project-structure) — documents `app/layout.tsx`, `app/page.tsx`, `public`, and route file conventions.

### Related Specs

- `.trellis/spec/backend/directory-structure.md` — generated files should preserve `settings.DATA_DIR/apps/{app_id}/project/`, accessed through `code_service.project_dir_for()` and `code_service.resolve_project_file()`.
- `.trellis/spec/frontend/directory-structure.md` — current frontend is a Vue/Vite SPA; preview behavior lives in `ChatPanel.vue` and points to generated static files.

## Caveats / Not Found

- No external web-search MCP tool was available in this tool environment, so external references are based on known official Next.js documentation URLs rather than live retrieval.
- Current backend validation does not accept `.ts`, `.tsx`, `.mjs`, `.ico`, `.png`, `.jpg`, `.webp`, or `_next/static` build output extensions beyond `.html`, `.css`, `.js`, `.json`, `.txt`, `.md`, and `.svg`; this is a mapping observation, not an implementation recommendation.
- Current generated-project limits of 20 files and 300 KB per file are smaller than many real Next.js export outputs.
- This research describes static export structure and constraints only; it does not modify code or define a build sandbox/security model for running generated dependencies.