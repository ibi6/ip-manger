# NetLedger Theme System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an accessible light, dark, and system-following theme that applies before first paint and works on login and authenticated pages.

**Architecture:** Pure functions in `theme.ts` define valid preferences and resolution. A focused provider owns persistence and system listeners, while a shared toggle renders the interaction. CSS design tokens and semantic surface utilities make the visual theme consistent without duplicating page components.

**Tech Stack:** React 19, TypeScript 6, Tailwind CSS 4, Node test runner, Vite.

---

### Task 1: Theme domain logic

**Files:**
- Create: `frontend/tests/theme.test.ts`
- Create: `frontend/src/lib/theme.ts`

- [ ] **Step 1: Write the failing unit tests**

```ts
import assert from 'node:assert/strict'
import test from 'node:test'
import { normalizeTheme, nextTheme, resolveTheme } from '../src/lib/theme.ts'

test('normalizeTheme rejects damaged stored preferences', () => {
  assert.equal(normalizeTheme('dark'), 'dark')
  assert.equal(normalizeTheme('unexpected'), 'system')
  assert.equal(normalizeTheme(null), 'system')
})

test('resolveTheme follows the operating system only in system mode', () => {
  assert.equal(resolveTheme('system', true), 'dark')
  assert.equal(resolveTheme('system', false), 'light')
  assert.equal(resolveTheme('light', true), 'light')
})

test('nextTheme cycles system, light, and dark', () => {
  assert.equal(nextTheme('system'), 'light')
  assert.equal(nextTheme('light'), 'dark')
  assert.equal(nextTheme('dark'), 'system')
})
```

- [ ] **Step 2: Run the test and verify RED**

Run: `cd frontend && npm test`

Expected: FAIL because `src/lib/theme.ts` does not exist.

- [ ] **Step 3: Implement the pure theme API**

```ts
export type ThemePreference = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'
export const THEME_STORAGE_KEY = 'netledger_theme'

export function normalizeTheme(value: string | null): ThemePreference {
  return value === 'light' || value === 'dark' || value === 'system' ? value : 'system'
}

export function resolveTheme(preference: ThemePreference, systemDark: boolean): ResolvedTheme {
  return preference === 'system' ? (systemDark ? 'dark' : 'light') : preference
}

export function nextTheme(preference: ThemePreference): ThemePreference {
  return preference === 'system' ? 'light' : preference === 'light' ? 'dark' : 'system'
}
```

- [ ] **Step 4: Run `npm test` and verify GREEN**

Expected: all theme and existing frontend tests pass.

### Task 2: Provider and pre-paint initialization

**Files:**
- Create: `frontend/src/lib/theme-context.ts`
- Create: `frontend/src/lib/theme-provider.tsx`
- Create: `frontend/public/theme-init.js`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/index.html`

- [ ] **Step 1: Define the context contract**

```ts
export interface ThemeContextValue {
  preference: ThemePreference
  resolvedTheme: ResolvedTheme
  setPreference: (preference: ThemePreference) => void
}
```

- [ ] **Step 2: Implement ThemeProvider**

The provider reads `netledger_theme` with a guarded storage helper, listens to `matchMedia('(prefers-color-scheme: dark)')`, writes `data-theme` and `colorScheme` to `document.documentElement`, and persists explicit changes. Storage and media failures fall back to `system` and light rendering.

- [ ] **Step 3: Add the CSP-compatible pre-paint script**

```js
;(function () {
  try {
    var stored = localStorage.getItem('netledger_theme')
    var preference = stored === 'light' || stored === 'dark' ? stored : 'system'
    var systemDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    var resolved = preference === 'system' ? (systemDark ? 'dark' : 'light') : preference
    document.documentElement.dataset.theme = resolved
    document.documentElement.style.colorScheme = resolved
  } catch (_) {
    document.documentElement.dataset.theme = 'light'
    document.documentElement.style.colorScheme = 'light'
  }
})()
```

- [ ] **Step 4: Load initialization before the Vite module and mount the provider**

Add `<script src="/theme-init.js"></script>` in `<head>` and wrap `AuthProvider` with `ThemeProvider` in `main.tsx`.

- [ ] **Step 5: Run TypeScript and lint**

Run: `cd frontend && npm run lint && npm run build`

Expected: exit 0 with no unused symbols or unsafe imports.

### Task 3: Theme toggle and semantic dark design

**Files:**
- Create: `frontend/src/components/ui/ThemeToggle.tsx`
- Modify: `frontend/src/components/layout/AppShell.tsx`
- Modify: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/components/ui/Button.tsx`
- Modify: `frontend/src/components/ui/Input.tsx`
- Modify: `frontend/src/components/ui/Card.tsx`
- Modify: `frontend/src/components/ui/EmptyState.tsx`
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Build the shared toggle**

Use `Monitor`, `Sun`, and `Moon` from Lucide. Render one 44px button that cycles with `nextTheme`, includes current mode text on larger screens, and exposes `aria-label="当前主题：…；切换为：…"` plus a matching title.

- [ ] **Step 2: Place both entry points**

Place the toggle at the login canvas top-right and in the application header before the primary action. Preserve the existing mobile menu and 44px touch targets.

- [ ] **Step 3: Add theme tokens**

Define semantic surface variables for canvas, elevated cards, subtle surfaces, tracks, borders, text, and shadows. Override them in `html[data-theme='dark']` with navy/teal values, then update shared components and Dashboard hardcoded surfaces to semantic utility classes.

- [ ] **Step 4: Add controlled transitions**

Transition background, border, color, and shadow for theme surfaces. Keep the existing `prefers-reduced-motion` override so users requesting reduced motion see immediate changes.

- [ ] **Step 5: Run frontend gates**

Run: `cd frontend && npm test && npm run lint && npm run build`

Expected: all tests pass, oxlint exits 0, and Vite produces `dist`.

### Task 4: Runtime verification and documentation

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Document theme behavior**

Add the three modes, persistence key behavior, and the UI locations to README and the 1.6.0 changelog.

- [ ] **Step 2: Verify in the browser**

At 375×812, 768×1024, and 1440×900: switch all three modes on the login page and dashboard, reload to verify persistence, confirm no page-level horizontal overflow, and inspect console errors.

- [ ] **Step 3: Run final repository checks**

Run:

```powershell
cd frontend
npm test
npm run lint
npm run build
cd ..
git diff --check
```

Expected: 0 failures and no whitespace errors.
