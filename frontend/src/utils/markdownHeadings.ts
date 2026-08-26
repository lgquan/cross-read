export function createHeadingId(text: string, counts: Map<string, number>): string {
  const base =
    text
      .normalize('NFKC')
      .trim()
      .toLocaleLowerCase()
      .replace(/\s+/g, '-')
      .replace(/[^\p{Letter}\p{Number}_-]+/gu, '')
      .replace(/^-+|-+$/g, '') || 'section'
  const count = counts.get(base) ?? 0
  counts.set(base, count + 1)
  return `section-${base}${count === 0 ? '' : `-${count + 1}`}`
}
