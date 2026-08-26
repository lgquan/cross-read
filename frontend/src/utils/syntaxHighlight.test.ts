import { describe, expect, it } from 'vitest'

import {
  getLanguageFromPath,
  getLanguageLabel,
  highlightCode,
  highlightMarkdownCode,
} from './syntaxHighlight'

describe('syntax highlighting', () => {
  it('detects languages from common source file names', () => {
    expect(getLanguageFromPath('scripts/train.py')).toBe('python')
    expect(getLanguageFromPath('web/App.tsx')).toBe('typescript')
    expect(getLanguageFromPath('deploy/Dockerfile')).toBe('dockerfile')
    expect(getLanguageFromPath('notes.txt')).toBeNull()
  })

  it('returns readable labels', () => {
    expect(getLanguageLabel('python')).toBe('Python')
    expect(getLanguageLabel('cpp')).toBe('C++')
  })

  it('highlights known languages and escapes source HTML', () => {
    const result = highlightCode('def greet(name):\n    return f"<b>{name}</b>"', 'python')
    expect(result).toContain('hljs-keyword')
    expect(result).toContain('&lt;b&gt;')
  })

  it('falls back for missing or unknown language names', () => {
    expect(highlightCode('plain text', '')).toBeNull()
    expect(highlightCode('plain text', 'unknown-language')).toBeNull()
  })

  it('auto-detects unlabeled Markdown fences but preserves explicit unknown languages', () => {
    expect(highlightMarkdownCode('def greet():\n    return True', '')).toContain('hljs-keyword')
    expect(highlightMarkdownCode('graph TD; A --> B', 'mermaid')).toBe('')
  })
})
