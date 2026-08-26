import { describe, expect, it } from 'vitest'

import { sortSlidePaths } from './presentation'

describe('presentation preview', () => {
  it('keeps only slide XML files and sorts them numerically', () => {
    expect(sortSlidePaths([
      'ppt/slides/slide10.xml',
      'ppt/notesSlides/notesSlide1.xml',
      'ppt/slides/_rels/slide1.xml.rels',
      'ppt/slides/slide2.xml',
      'ppt/slides/slide1.xml',
    ])).toEqual([
      'ppt/slides/slide1.xml',
      'ppt/slides/slide2.xml',
      'ppt/slides/slide10.xml',
    ])
  })
})
