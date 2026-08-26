<script setup lang="ts">
import { ChevronLeft, FileQuestion } from '@lucide/vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DocxReader from '@/components/readers/DocxReader.vue'
import ImageReader from '@/components/readers/ImageReader.vue'
import MarkdownReader from '@/components/readers/MarkdownReader.vue'
import PdfReader from '@/components/readers/PdfReader.vue'
import TextReader from '@/components/readers/TextReader.vue'
import VideoReader from '@/components/readers/VideoReader.vue'
import type { FileKind } from '@/types/files'

const route = useRoute()
const router = useRouter()
const path = computed(() => (typeof route.query.path === 'string' ? route.query.path : ''))
const kind = computed<FileKind>(() => {
  const value = typeof route.query.kind === 'string' ? route.query.kind : 'unsupported'
  const valid: FileKind[] = ['markdown', 'pdf', 'docx', 'image', 'text', 'video', 'unsupported', 'directory']
  return valid.includes(value as FileKind) ? (value as FileKind) : 'unsupported'
})
const shareId = computed(() => String(route.params.shareId))
const fileName = computed(() => {
  const parts = path.value.split('/')
  return parts[parts.length - 1] || '文件'
})

function goBack() {
  const parent = path.value.split('/').slice(0, -1).join('/')
  void router.push({
    name: 'browse',
    params: { shareId: route.params.shareId },
    query: parent ? { path: parent } : {},
  })
}
</script>

<template>
  <section class="browse-header">
    <button class="icon-button back-button" type="button" aria-label="返回文件夹" @click="goBack">
      <ChevronLeft :size="23" />
    </button>
    <div class="browse-title">
      <p class="eyebrow">文件预览</p>
      <h1>{{ fileName }}</h1>
    </div>
  </section>

  <section class="reader-surface" :class="`reader-surface--${kind}`">
    <MarkdownReader v-if="kind === 'markdown'" :share-id="shareId" :path="path" />
    <TextReader v-else-if="kind === 'text'" :share-id="shareId" :path="path" />
    <ImageReader v-else-if="kind === 'image'" :share-id="shareId" :path="path" :alt="fileName" />
    <VideoReader v-else-if="kind === 'video'" :share-id="shareId" :path="path" />
    <PdfReader v-else-if="kind === 'pdf'" :share-id="shareId" :path="path" />
    <DocxReader v-else-if="kind === 'docx'" :share-id="shareId" :path="path" />
    <div v-else class="state-panel preview-placeholder">
      <span class="state-icon"><FileQuestion :size="28" /></span>
      <h2>暂不支持预览</h2>
      <p>这个文件类型目前不能在浏览器中阅读。</p>
      <button class="button button--primary" type="button" @click="goBack">返回文件夹</button>
    </div>
  </section>
</template>
