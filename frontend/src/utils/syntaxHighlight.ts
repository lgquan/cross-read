import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import c from 'highlight.js/lib/languages/c'
import cpp from 'highlight.js/lib/languages/cpp'
import css from 'highlight.js/lib/languages/css'
import dockerfile from 'highlight.js/lib/languages/dockerfile'
import go from 'highlight.js/lib/languages/go'
import ini from 'highlight.js/lib/languages/ini'
import java from 'highlight.js/lib/languages/java'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'
import powershell from 'highlight.js/lib/languages/powershell'
import python from 'highlight.js/lib/languages/python'
import rust from 'highlight.js/lib/languages/rust'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'

const languages = {
  bash,
  c,
  cpp,
  css,
  dockerfile,
  go,
  ini,
  java,
  javascript,
  json,
  markdown,
  powershell,
  python,
  rust,
  sql,
  typescript,
  xml,
  yaml,
}

for (const [name, language] of Object.entries(languages)) {
  hljs.registerLanguage(name, language)
}

const extensionLanguages: Record<string, string> = {
  bash: 'bash',
  c: 'c',
  cc: 'cpp',
  cfg: 'ini',
  cjs: 'javascript',
  conf: 'ini',
  cpp: 'cpp',
  css: 'css',
  cts: 'typescript',
  cxx: 'cpp',
  go: 'go',
  h: 'c',
  hpp: 'cpp',
  htm: 'xml',
  html: 'xml',
  ini: 'ini',
  java: 'java',
  js: 'javascript',
  json: 'json',
  jsonl: 'json',
  jsonc: 'json',
  jsx: 'javascript',
  md: 'markdown',
  mjs: 'javascript',
  mts: 'typescript',
  ps1: 'powershell',
  psd1: 'powershell',
  psm1: 'powershell',
  py: 'python',
  pyw: 'python',
  rs: 'rust',
  sh: 'bash',
  sql: 'sql',
  toml: 'ini',
  ts: 'typescript',
  tsx: 'typescript',
  vue: 'xml',
  xml: 'xml',
  yaml: 'yaml',
  yml: 'yaml',
  zsh: 'bash',
}

const languageLabels: Record<string, string> = {
  bash: 'Shell',
  c: 'C',
  cpp: 'C++',
  css: 'CSS',
  dockerfile: 'Dockerfile',
  go: 'Go',
  ini: 'INI / TOML',
  java: 'Java',
  javascript: 'JavaScript',
  json: 'JSON',
  markdown: 'Markdown',
  powershell: 'PowerShell',
  python: 'Python',
  rust: 'Rust',
  sql: 'SQL',
  typescript: 'TypeScript',
  xml: 'HTML / XML',
  yaml: 'YAML',
}

const autoDetectionLanguages = [
  'bash',
  'c',
  'cpp',
  'css',
  'dockerfile',
  'go',
  'ini',
  'java',
  'javascript',
  'json',
  'powershell',
  'python',
  'rust',
  'sql',
  'typescript',
  'xml',
  'yaml',
]

export function getLanguageFromPath(path: string): string | null {
  const fileName = path.split('/').pop()?.toLowerCase() ?? ''
  if (fileName === 'dockerfile') return 'dockerfile'
  const extension = fileName.includes('.') ? fileName.split('.').pop() ?? '' : ''
  return extensionLanguages[extension] ?? null
}

export function getLanguageLabel(language: string): string {
  return languageLabels[language] ?? language.toUpperCase()
}

export function highlightCode(source: string, language: string): string | null {
  const normalized = language.trim().toLowerCase()
  if (!normalized || !hljs.getLanguage(normalized)) return null
  return hljs.highlight(source, { language: normalized, ignoreIllegals: true }).value
}

export function highlightMarkdownCode(source: string, language: string): string {
  const explicit = highlightCode(source, language)
  if (explicit !== null) return explicit
  if (language.trim()) return ''
  return hljs.highlightAuto(source, autoDetectionLanguages).value
}
