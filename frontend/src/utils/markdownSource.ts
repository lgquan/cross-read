export function normalizeMarkdownSource(source: string): string {
  return source
    .replace(/(\S)\*\*\u200B+/g, '$1** ')
    .replace(/\u200B/g, '')
}
