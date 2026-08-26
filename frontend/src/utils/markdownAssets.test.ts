import { describe, expect, it } from 'vitest'

import { resolveMarkdownAssetPath } from './markdownAssets'

const documentPath = 'PPT/02_项目/临床筛查PPT.md'

describe('resolveMarkdownAssetPath', () => {
  it('decodes browser-normalized Chinese asset paths once', () => {
    expect(
      resolveMarkdownAssetPath(
        documentPath,
        '%E4%B8%B4%E5%BA%8A%E7%AD%9B%E6%9F%A5PPT/%E6%88%AA%E5%9B%BE/clinical-trial-01.jpg',
      ),
    ).toBe('PPT/02_项目/临床筛查PPT/截图/clinical-trial-01.jpg')
  })

  it('resolves parent segments and Windows separators', () => {
    expect(resolveMarkdownAssetPath(documentPath, '..\\images\\slide%201.jpg')).toBe(
      'PPT/images/slide 1.jpg',
    )
  })

  it('keeps malformed percent sequences as literal filename characters', () => {
    expect(resolveMarkdownAssetPath(documentPath, 'images/100%.png')).toBe(
      'PPT/02_项目/images/100%.png',
    )
  })
})
