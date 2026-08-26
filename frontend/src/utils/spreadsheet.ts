export interface PreviewSheet {
  name: string
  rows: string[][]
  truncatedRows: boolean
  truncatedColumns: boolean
}

const MAX_PREVIEW_ROWS = 2000
const MAX_PREVIEW_COLUMNS = 100

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (value instanceof Date) return value.toLocaleString()
  return String(value)
}

export function createPreviewSheet(name: string, sourceRows: unknown[][]): PreviewSheet {
  const columnCount = Math.min(
    MAX_PREVIEW_COLUMNS,
    sourceRows.reduce((largest, row) => Math.max(largest, row.length), 0),
  )
  const rows = sourceRows.slice(0, MAX_PREVIEW_ROWS).map((row) =>
    Array.from({ length: columnCount }, (_, index) => formatCell(row[index])),
  )
  return {
    name,
    rows,
    truncatedRows: sourceRows.length > MAX_PREVIEW_ROWS,
    truncatedColumns: sourceRows.some((row) => row.length > MAX_PREVIEW_COLUMNS),
  }
}

function decodeCsv(buffer: ArrayBuffer): string {
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(buffer)
  } catch {
    return new TextDecoder('gb18030').decode(buffer)
  }
}

export async function parseSpreadsheet(buffer: ArrayBuffer, path: string): Promise<PreviewSheet[]> {
  if (path.toLocaleLowerCase().endsWith('.csv')) {
    const Papa = (await import('papaparse')).default
    const result = Papa.parse<string[]>(decodeCsv(buffer), { skipEmptyLines: false })
    if (result.errors.length > 0 && result.data.length === 0) {
      throw new Error(result.errors[0]?.message ?? 'CSV 内容无法解析')
    }
    return [createPreviewSheet('CSV', result.data)]
  }

  const readXlsxFile = (await import('read-excel-file/browser')).default
  const workbook = await readXlsxFile(buffer)
  return workbook.map((sheet) => createPreviewSheet(sheet.sheet, sheet.data))
}
