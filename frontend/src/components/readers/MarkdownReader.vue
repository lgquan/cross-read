<script setup lang="ts">
import { ListTree, X } from '@lucide/vue'
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { getContentUrl, getTextContent } from '@/api/client'
import { resolveMarkdownAssetPath } from '@/utils/markdownAssets'
import { createHeadingId } from '@/utils/markdownHeadings'
import { parseThemePreference, resolveTheme, THEME_CHANGE_EVENT } from '@/utils/theme'
import ReaderStatus from './ReaderStatus.vue'

interface TocHeading {
  id: string
  level: number
  text: string
}

const props = defineProps<{
  shareId: string
  path: string
}>()

const html = ref('')
const loading = ref(true)
const error = ref('')
const article = ref<HTMLElement | null>(null)
const tocOpen = ref(false)
const headings = ref<TocHeading[]>([])
const activeHeadingId = ref('')
const tocTrigger = ref<HTMLButtonElement | null>(null)
const tocPanel = ref<HTMLElement | null>(null)
let diagramSequence = 0
let activeFrame = 0
let renderRequest = 0
let colorSchemeQuery: MediaQueryList | null = null

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
    diagram.dataset.mermaidSource = code.textContent ?? ''
    diagram.textContent = diagram.dataset.mermaidSource
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

function updateActiveHeading(): void {
  activeFrame = 0
  const elements = headings.value
    .map((heading) => document.getElementById(heading.id))
    .filter((heading): heading is HTMLElement => heading !== null)
  const first = elements[0]
  if (!first) {
    activeHeadingId.value = ''
    return
  }

  const anchor = Number.parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--reader-anchor')) || 80
  let current = first
  for (const heading of elements) {
    if (heading.getBoundingClientRect().top > anchor + 2) break
    current = heading
  }
  activeHeadingId.value = current.id
}

function scheduleActiveHeading(): void {
  if (activeFrame) return
  activeFrame = requestAnimationFrame(updateActiveHeading)
}

function collectHeadings(): void {
  const counts = new Map<string, number>()
  const elements = Array.from(article.value?.querySelectorAll<HTMLElement>('h1, h2, h3, h4, h5, h6') ?? [])
  headings.value = elements
    .map((heading) => {
      const text = heading.textContent?.trim() ?? ''
      if (!text) return null
      const id = createHeadingId(text, counts)
      heading.id = id
      return { id, level: Number(heading.tagName.slice(1)), text }
    })
    .filter((heading): heading is TocHeading => heading !== null)
  updateActiveHeading()
}

function openToc(): void {
  tocOpen.value = true
  void nextTick(() => {
    tocPanel.value?.querySelector<HTMLButtonElement>('.toc-close')?.focus()
    requestAnimationFrame(() => {
      tocPanel.value?.querySelector<HTMLElement>('.toc-item--active')?.scrollIntoView({ block: 'center' })
    })
  })
}

function closeToc(restoreFocus = true): void {
  tocOpen.value = false
  if (restoreFocus) void nextTick(() => tocTrigger.value?.focus())
}

function jumpToHeading(id: string): void {
  closeToc(false)
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  activeHeadingId.value = id
}

function tocItemStyle(level: number): Record<string, string> {
  return { '--toc-depth': String(level - 1) }
}

function handleTocKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    closeToc()
    return
  }
  if (event.key !== 'Tab' || !tocPanel.value) return

  const focusable = Array.from(tocPanel.value.querySelectorAll<HTMLButtonElement>('button:not(:disabled)'))
  if (focusable.length === 0) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last?.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first?.focus()
  }
}

async function renderMermaidDiagrams() {
  const nodes = Array.from(article.value?.querySelectorAll<HTMLElement>('.mermaid-diagram') ?? [])
  if (nodes.length === 0) return

  const request = ++renderRequest
  const preference = parseThemePreference(document.documentElement.dataset.theme)
  const prefersDark = colorSchemeQuery?.matches ?? window.matchMedia('(prefers-color-scheme: dark)').matches
  const mermaid = (await import('mermaid')).default
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: resolveTheme(preference, prefersDark) === 'dark' ? 'dark' : 'default',
    flowchart: { htmlLabels: true, useMaxWidth: true },
  })

  for (const node of nodes) {
    const source = node.dataset.mermaidSource ?? node.textContent ?? ''
    try {
      diagramSequence += 1
      const result = await mermaid.render(`cross-read-diagram-${diagramSequence}`, source)
      if (request !== renderRequest || !node.isConnected) return
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

function handleThemeChange(): void {
  void renderMermaidDiagrams()
}

function handleSystemThemeChange(): void {
  if (document.documentElement.dataset.theme === 'system') void renderMermaidDiagrams()
}

async function load() {
  loading.value = true
  error.value = ''
  headings.value = []
  activeHeadingId.value = ''
  tocOpen.value = false
  try {
    const source = await getTextContent(props.shareId, props.path)
    const safe = DOMPurify.sanitize(markdown.render(source), {
      USE_PROFILES: { html: true },
    })
    html.value = rewriteAssets(safe)
    loading.value = false
    await nextTick()
    collectHeadings()
    await renderMermaidDiagrams()
    updateActiveHeading()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '无法渲染 Markdown 文件'
  } finally {
    loading.value = false
  }
}

watch(() => [props.shareId, props.path], load)
watch(tocOpen, (open) => document.documentElement.classList.toggle('toc-open', open))
onMounted(() => {
  colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)')
  window.addEventListener('scroll', scheduleActiveHeading, { passive: true })
  window.addEventListener('resize', scheduleActiveHeading)
  window.addEventListener(THEME_CHANGE_EVENT, handleThemeChange)
  colorSchemeQuery.addEventListener('change', handleSystemThemeChange)
  void load()
})
onBeforeUnmount(() => {
  renderRequest += 1
  document.documentElement.classList.remove('toc-open')
  window.removeEventListener('scroll', scheduleActiveHeading)
  window.removeEventListener('resize', scheduleActiveHeading)
  window.removeEventListener(THEME_CHANGE_EVENT, handleThemeChange)
  colorSchemeQuery?.removeEventListener('change', handleSystemThemeChange)
  if (activeFrame) cancelAnimationFrame(activeFrame)
})
</script>

<template>
  <Teleport to="body">
    <button
      v-if="headings.length > 0"
      ref="tocTrigger"
      class="reader-toc-trigger"
      type="button"
      aria-label="打开目录"
      aria-controls="markdown-toc"
      :aria-expanded="tocOpen"
      title="目录"
      @click="openToc"
    >
      <ListTree :size="21" />
    </button>

    <Transition name="toc-sheet">
      <div v-if="tocOpen" class="toc-overlay" @click.self="closeToc()">
        <aside
          id="markdown-toc"
          ref="tocPanel"
          class="toc-panel"
          role="dialog"
          aria-modal="true"
          aria-labelledby="markdown-toc-title"
          @keydown="handleTocKeydown"
        >
          <div class="toc-handle" aria-hidden="true"></div>
          <header class="toc-header">
            <div>
              <p class="toc-eyebrow">当前文档</p>
              <h2 id="markdown-toc-title">目录</h2>
            </div>
            <button class="toc-close" type="button" aria-label="关闭目录" title="关闭" @click="closeToc()">
              <X :size="21" />
            </button>
          </header>
          <nav class="toc-list" aria-label="文档目录">
            <button
              v-for="heading in headings"
              :key="heading.id"
              class="toc-item"
              :class="{ 'toc-item--active': heading.id === activeHeadingId }"
              :style="tocItemStyle(heading.level)"
              type="button"
              :aria-current="heading.id === activeHeadingId ? 'location' : undefined"
              @click="jumpToHeading(heading.id)"
            >
              <span class="toc-level">H{{ heading.level }}</span>
              <span>{{ heading.text }}</span>
            </button>
          </nav>
        </aside>
      </div>
    </Transition>
  </Teleport>

  <ReaderStatus :loading="loading" :error="error" />
  <!-- Sanitized with DOMPurify before rendering. -->
  <article
    v-if="!loading && !error"
    ref="article"
    class="markdown-body"
    v-html="html"
  ></article>
</template>
