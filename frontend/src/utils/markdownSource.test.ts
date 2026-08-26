import { describe, expect, it } from 'vitest'

import { normalizeMarkdownSource } from './markdownSource'

describe('normalizeMarkdownSource', () => {
  it('removes copied zero-width spaces that break Markdown delimiters', () => {
    expect(normalizeMarkdownSource('**一句话概括：**\u200B\u200BGraph Engineering')).toBe(
      '**一句话概括：** Graph Engineering',
    )
  })

  it('removes zero-width spaces outside Markdown delimiters without adding gaps', () => {
    expect(normalizeMarkdownSource('正在\u200B\u200B形成中的概念\u200B\u200B。')).toBe('正在形成中的概念。')
  })

  it('leaves ordinary Markdown unchanged', () => {
    expect(normalizeMarkdownSource('**加粗**\n\n正文')).toBe('**加粗**\n\n正文')
  })
})
