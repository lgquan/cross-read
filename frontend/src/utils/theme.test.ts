import { describe, expect, it, vi } from 'vitest'

import {
  applyThemePreference,
  parseThemePreference,
  readThemePreference,
  resolveTheme,
  saveThemePreference,
  THEME_STORAGE_KEY,
} from './theme'

describe('theme preference', () => {
  it('falls back to system for unknown stored values', () => {
    expect(parseThemePreference('sepia')).toBe('system')
    expect(readThemePreference({ getItem: () => 'dark' })).toBe('dark')
    expect(readThemePreference({ getItem: () => 'unknown' })).toBe('system')
  })

  it('resolves system mode from the operating system preference', () => {
    expect(resolveTheme('system', true)).toBe('dark')
    expect(resolveTheme('system', false)).toBe('light')
    expect(resolveTheme('light', true)).toBe('light')
  })

  it('applies and saves an explicit preference', () => {
    const root = { dataset: {} as DOMStringMap }
    const setItem = vi.fn()

    applyThemePreference('light', root)
    saveThemePreference('light', { setItem })

    expect(root.dataset.theme).toBe('light')
    expect(setItem).toHaveBeenCalledWith(THEME_STORAGE_KEY, 'light')
  })

  it('tolerates unavailable browser storage', () => {
    expect(readThemePreference({ getItem: () => { throw new Error('blocked') } })).toBe('system')
    expect(() => saveThemePreference('dark', { setItem: () => { throw new Error('blocked') } })).not.toThrow()
  })
})
