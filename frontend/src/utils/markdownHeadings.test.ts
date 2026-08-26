import { describe, expect, it } from 'vitest'

import { createHeadingId } from './markdownHeadings'

describe('createHeadingId', () => {
  it('keeps readable Chinese and Latin characters', () => {
    expect(createHeadingId('  三层 IR：规则引擎  ', new Map())).toBe('section-三层-ir规则引擎')
  })

  it('makes repeated headings unique', () => {
    const counts = new Map<string, number>()
    expect(createHeadingId('实现方案', counts)).toBe('section-实现方案')
    expect(createHeadingId('实现方案', counts)).toBe('section-实现方案-2')
  })

  it('provides a fallback for punctuation-only headings', () => {
    expect(createHeadingId('---', new Map())).toBe('section-section')
  })
})
