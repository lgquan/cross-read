export interface PreviewSlide {
  number: number
  paragraphs: string[]
}

function slideNumber(path: string): number {
  const match = /\/slide(\d+)\.xml$/i.exec(path)
  return match?.[1] ? Number.parseInt(match[1], 10) : Number.MAX_SAFE_INTEGER
}

export function sortSlidePaths(paths: string[]): string[] {
  return paths
    .filter((path) => /^ppt\/slides\/slide\d+\.xml$/i.test(path))
    .sort((left, right) => slideNumber(left) - slideNumber(right))
}

function extractParagraphs(source: string): string[] {
  const document = new DOMParser().parseFromString(source, 'application/xml')
  if (document.querySelector('parsererror')) throw new Error('PPTX 幻灯片内容无法解析')

  return Array.from(document.getElementsByTagName('a:p'))
    .map((paragraph) => Array.from(paragraph.getElementsByTagName('a:t'))
      .map((node) => node.textContent ?? '')
      .join('')
      .trim())
    .filter(Boolean)
}

export async function parsePresentation(buffer: ArrayBuffer): Promise<PreviewSlide[]> {
  const { strFromU8, unzipSync } = await import('fflate')
  const archive = unzipSync(new Uint8Array(buffer))
  return sortSlidePaths(Object.keys(archive)).map((path) => ({
    number: slideNumber(path),
    paragraphs: extractParagraphs(strFromU8(archive[path]!)),
  }))
}
