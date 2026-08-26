import { describe, expect, it } from 'vitest'

import { formatFileSize, formatModifiedAt } from './format'

describe('formatFileSize', () => {
  it('distinguishes directories from zero-byte files', () => {
    expect(formatFileSize(null)).toBe('文件夹')
    expect(formatFileSize(0)).toBe('0 B')
  })

  it('uses compact binary units', () => {
    expect(formatFileSize(1536)).toBe('1.5 KB')
    expect(formatFileSize(10 * 1024 * 1024)).toBe('10 MB')
  })
})

describe('formatModifiedAt', () => {
  it('returns an empty value for invalid dates', () => {
    expect(formatModifiedAt('not-a-date')).toBe('')
  })
})
