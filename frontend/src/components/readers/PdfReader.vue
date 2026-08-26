<script setup lang="ts">
import { ChevronLeft, ChevronRight, Search, ZoomIn, ZoomOut } from '@lucide/vue'
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { getContentUrl } from '@/api/client'
import ReaderStatus from './ReaderStatus.vue'

const props = defineProps<{ shareId: string; path: string }>()
const canvas = ref<HTMLCanvasElement | null>(null)
const document = ref<PDFDocumentProxy | null>(null)
const pageNumber = ref(1)
const pageCount = ref(0)
const scale = ref(1.25)
const loading = ref(true)
const error = ref('')
const searchQuery = ref('')
const searchMessage = ref('')
let renderTask: ReturnType<PDFPageProxy['render']> | null = null

const pageLabel = computed(() => `${pageNumber.value} / ${pageCount.value || '—'}`)

async function renderPage() {
  if (!document.value || !canvas.value) return
  renderTask?.cancel()
  const page = await document.value.getPage(pageNumber.value)
  const viewport = page.getViewport({ scale: scale.value })
  const context = canvas.value.getContext('2d')
  if (!context) throw new Error('浏览器无法创建 PDF 画布')
  const ratio = window.devicePixelRatio || 1
  canvas.value.width = Math.floor(viewport.width * ratio)
  canvas.value.height = Math.floor(viewport.height * ratio)
  canvas.value.style.width = `${viewport.width}px`
  canvas.value.style.height = `${viewport.height}px`
  const transform: [number, number, number, number, number, number] | undefined =
    ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0]
  renderTask = page.render({ canvas: canvas.value, canvasContext: context, viewport, transform })
  try {
    await renderTask.promise
  } catch (reason) {
    if (!(reason instanceof Error) || reason.name !== 'RenderingCancelledException') throw reason
  }
}

async function load() {
  loading.value = true
  error.value = ''
  searchMessage.value = ''
  try {
    const pdfjs = await import('pdfjs-dist')
    const workerUrl = (await import('pdfjs-dist/build/pdf.worker.min.mjs?url')).default
    pdfjs.GlobalWorkerOptions.workerSrc = workerUrl
    document.value = await pdfjs.getDocument(getContentUrl(props.shareId, props.path)).promise
    pageCount.value = document.value.numPages
    pageNumber.value = 1
    await nextTick()
    await renderPage()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '无法打开 PDF 文件'
  } finally {
    loading.value = false
  }
}

async function goToPage(value: number) {
  pageNumber.value = Math.min(pageCount.value, Math.max(1, value))
  await renderPage()
}

async function changeScale(amount: number) {
  scale.value = Math.min(3, Math.max(0.6, scale.value + amount))
  await renderPage()
}

async function searchDocument() {
  const query = searchQuery.value.trim().toLocaleLowerCase()
  if (!query || !document.value) return
  searchMessage.value = '正在搜索…'
  let matches = 0
  let firstPage = 0
  for (let index = 1; index <= document.value.numPages; index += 1) {
    const page = await document.value.getPage(index)
    const content = await page.getTextContent()
    const text = content.items
      .map((item) => ('str' in item ? item.str : ''))
      .join(' ')
      .toLocaleLowerCase()
    if (text.includes(query)) {
      matches += 1
      if (!firstPage) firstPage = index
    }
  }
  if (firstPage) await goToPage(firstPage)
  searchMessage.value = matches ? `在 ${matches} 页中找到，已跳到第 ${firstPage} 页` : '没有找到相关内容'
}

watch(() => [props.shareId, props.path], load)
onMounted(load)
onBeforeUnmount(() => {
  renderTask?.cancel()
  void document.value?.destroy()
})
</script>

<template>
  <ReaderStatus :loading="loading" :error="error" />
  <template v-if="!loading && !error">
    <div class="pdf-controls">
      <div class="pdf-control-group">
        <button type="button" aria-label="上一页" :disabled="pageNumber <= 1" @click="goToPage(pageNumber - 1)">
          <ChevronLeft :size="18" />
        </button>
        <span>{{ pageLabel }}</span>
        <button type="button" aria-label="下一页" :disabled="pageNumber >= pageCount" @click="goToPage(pageNumber + 1)">
          <ChevronRight :size="18" />
        </button>
      </div>
      <div class="pdf-control-group">
        <button type="button" aria-label="缩小" @click="changeScale(-0.15)"><ZoomOut :size="18" /></button>
        <span>{{ Math.round(scale * 100) }}%</span>
        <button type="button" aria-label="放大" @click="changeScale(0.15)"><ZoomIn :size="18" /></button>
      </div>
    </div>
    <form class="pdf-search" @submit.prevent="searchDocument">
      <Search :size="17" />
      <input v-model="searchQuery" type="search" placeholder="搜索 PDF 文本" />
      <button type="submit">查找</button>
    </form>
    <p v-if="searchMessage" class="pdf-search-result" role="status">{{ searchMessage }}</p>
    <div class="pdf-canvas-wrap">
      <canvas ref="canvas"></canvas>
    </div>
  </template>
</template>
