import { describe, expect, it } from 'vitest'

import { createPreviewSheet, parseSpreadsheet } from './spreadsheet'

describe('spreadsheet preview', () => {
  it('normalizes uneven rows and cell values', () => {
    const sheet = createPreviewSheet('Sheet 1', [
      ['姓名', '年龄'],
      ['小林', 28, true],
    ])

    expect(sheet.rows).toEqual([
      ['姓名', '年龄', ''],
      ['小林', '28', 'true'],
    ])
  })

  it('parses quoted CSV cells', async () => {
    const source = new TextEncoder().encode('姓名,备注\n小林,"熟悉 Python, SQL"')
    const sheet = (await parseSpreadsheet(source.buffer, 'report.csv'))[0]

    expect(sheet?.rows[1]).toEqual(['小林', '熟悉 Python, SQL'])
  })
})
