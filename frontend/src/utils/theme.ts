export const THEME_STORAGE_KEY = 'cross-read-theme'
export const THEME_CHANGE_EVENT = 'cross-read-theme-change'

export type ThemePreference = 'system' | 'light' | 'dark'
export type ResolvedTheme = 'light' | 'dark'

export function parseThemePreference(value: unknown): ThemePreference {
  return value === 'light' || value === 'dark' || value === 'system' ? value : 'system'
}

export function readThemePreference(storage?: Pick<Storage, 'getItem'> | null): ThemePreference {
  const target = storage ?? (typeof window === 'undefined' ? null : window.localStorage)
  if (!target) return 'system'

  try {
    return parseThemePreference(target.getItem(THEME_STORAGE_KEY))
  } catch {
    return 'system'
  }
}

export function resolveTheme(preference: ThemePreference, prefersDark: boolean): ResolvedTheme {
  return preference === 'system' ? (prefersDark ? 'dark' : 'light') : preference
}

export function applyThemePreference(
  preference: ThemePreference,
  root?: Pick<HTMLElement, 'dataset'> | null,
): void {
  const target = root ?? (typeof document === 'undefined' ? null : document.documentElement)
  if (target) target.dataset.theme = preference
}

export function saveThemePreference(
  preference: ThemePreference,
  storage?: Pick<Storage, 'setItem'> | null,
): void {
  const target = storage ?? (typeof window === 'undefined' ? null : window.localStorage)
  if (!target) return

  try {
    target.setItem(THEME_STORAGE_KEY, preference)
  } catch {
    // The selected theme still applies for this session when storage is unavailable.
  }
}

export function setThemePreference(preference: ThemePreference): void {
  applyThemePreference(preference)
  saveThemePreference(preference)
  window.dispatchEvent(new CustomEvent<ThemePreference>(THEME_CHANGE_EVENT, { detail: preference }))
}
