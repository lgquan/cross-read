function decodeBrowserPath(value: string): string {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

export function resolveMarkdownAssetPath(documentPath: string, assetPath: string): string {
  const rawAsset = assetPath.split(/[?#]/, 1)[0] ?? ''
  const cleanAsset = decodeBrowserPath(rawAsset).replace(/\\/g, '/')
  const segments = documentPath.split('/').slice(0, -1)

  for (const part of cleanAsset.split('/')) {
    if (!part || part === '.') continue
    if (part === '..') segments.pop()
    else segments.push(part)
  }

  return segments.join('/')
}
