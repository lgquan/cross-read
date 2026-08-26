<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { getContentUrl } from '@/api/client'
import { parsePresentation, type PreviewSlide } from '@/utils/presentation'
import ReaderStatus from './ReaderStatus.vue'

const props = defineProps<{ shareId: string; path: string }>()
const slides = ref<PreviewSlide[]>([])
const loading = ref(true)
const error = ref('')

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  slides.value = []
  try {
    const response = await fetch(getContentUrl(props.shareId, props.path))
    if (!response.ok) throw new Error('无法读取 PowerPoint 文件')
    slides.value = await parsePresentation(await response.arrayBuffer())
    if (slides.value.length === 0) throw new Error('这个 PowerPoint 中没有可读取的幻灯片')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '无法预览 PowerPoint 文件'
  } finally {
    loading.value = false
  }
}

watch(() => [props.shareId, props.path], load)
onMounted(load)
</script>

<template>
  <ReaderStatus :loading="loading" :error="error" />
  <div v-if="!loading && !error" class="presentation-reader">
    <header class="presentation-summary-header">
      <strong>文字摘要</strong>
      <span>{{ slides.length }} 页</span>
    </header>
    <section v-for="slide in slides" :key="slide.number" class="presentation-slide">
      <h2>第 {{ slide.number }} 页</h2>
      <div v-if="slide.paragraphs.length" class="presentation-slide-text">
        <p v-for="(paragraph, index) in slide.paragraphs" :key="index">{{ paragraph }}</p>
      </div>
      <p v-else class="presentation-slide-empty">这一页没有可提取的文字。</p>
    </section>
  </div>
</template>
