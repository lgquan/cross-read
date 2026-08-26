<script setup lang="ts">
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import { nextTick, onMounted, ref, watch } from 'vue'

import { getContentUrl, getTextContent } from '@/api/client'
import { resolveMarkdownAssetPath } from '@/utils/markdownAssets'
import ReaderStatus from './ReaderStatus.vue'

const props = defineProps<{
  shareId: string
  path: string
}>()

const html = ref('')
const loading = ref(true)
const error = ref('')
const article = ref<HTMLElement | null>(null)
let diagramSequence = 0

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
})

function isExternal(value: string): boolean {
  return /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(value)
}

function rewriteAssets(value: string): string {
  const wrapper = document.createElement('div')
  wrapper.innerHTML = value
  for (const image of wrapper.querySelectorAll('img')) {
    const source = image.getAttribute('src')
    if (source && !isExternal(source)) {
      image.src = getContentUrl(props.shareId, resolveMarkdownAssetPath(props.path, source))
    }
    image.loading = 'lazy'
  }
  for (const link of wrapper.querySelectorAll('a')) {
    if (link.href.startsWith('http://') || link.href.startsWith('https://')) {
      link.target = '_blank'
      link.rel = 'noopener noreferrer'
    }
  }
  for (const code of wrapper.querySelectorAll('pre > code.language-mermaid')) {
    const diagram = document.createElement('div')
    diagram.className = 'mermaid-diagram'
    diagram.textContent = code.textContent
    code.parentElement?.replaceWith(diagram)
  }
  return wrapper.innerHTML
}

function centerMermaidContent(node: HTMLElement): void {
  const svg = node.querySelector<SVGSVGElement>('svg')
  const graph = svg?.querySelector<SVGGElement>(':scope > g')
  const viewBox = svg?.getAttribute('viewBox')?.trim().split(/\s+/).map(Number)
  if (!svg || !graph || !viewBox || viewBox.length !== 4 || viewBox.some((value) => !Number.isFinite(value))) {
    return
  }

  const [x, y, width, height] = viewBox as [number, number, number, number]
  const svgRect = svg.getBoundingClientRect()
  const graphRect = graph.getBoundingClientRect()
  if (!svgRect.width || !svgRect.height || !graphRect.width || !graphRect.height) return

  const horizontalOffset = graphRect.left + graphRect.width / 2 - (svgRect.left + svgRect.width / 2)
  const verticalOffset = graphRect.top + graphRect.height / 2 - (svgRect.top + svgRect.height / 2)
  const centeredX = x + horizontalOffset * (width / svgRect.width)
  const centeredY = y + verticalOffset * (height / svgRect.height)
  svg.setAttribute('viewBox', `${centeredX} ${centeredY} ${width} ${height}`)
}

async function renderMermaidDiagrams() {
  const nodes = Array.from(article.value?.querySelectorAll<HTMLElement>('.mermaid-diagram') ?? [])
  if (nodes.length === 0) return

  const mermaid = (await import('mermaid')).default
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default',
    flowchart: { htmlLabels: true, useMaxWidth: true },
  })

  for (const node of nodes) {
    const source = node.textContent ?? ''
    try {
      diagramSequence += 1
      const result = await mermaid.render(`cross-read-diagram-${diagramSequence}`, source)
      node.innerHTML = result.svg
      result.bindFunctions?.(node)
    } catch {
      node.replaceChildren()
      const message = document.createElement('p')
      message.className = 'mermaid-error'
      message.textContent = '流程图语法无法解析，下面保留原始内容。'
      const fallback = document.createElement('pre')
      fallback.textContent = source
      node.append(message, fallback)
    }
  }

  await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())))
  for (const node of nodes) centerMermaidContent(node)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const source = await getTextContent(props.shareId, props.path)
    const safe = DOMPurify.sanitize(markdown.render(source), {
      USE_PROFILES: { html: true },
    })
    html.value = rewriteAssets(safe)
    loading.value = false
    await nextTick()
    await renderMermaidDiagrams()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '无法渲染 Markdown 文件'
  } finally {
    loading.value = false
  }
}

watch(() => [props.shareId, props.path], load)
onMounted(load)
</script>

<template>
  <ReaderStatus :loading="loading" :error="error" />
  <!-- Sanitized with DOMPurify before rendering. -->
  <article
    v-if="!loading && !error"
    ref="article"
    class="markdown-body"
    v-html="html"
  ></article>
</template>
