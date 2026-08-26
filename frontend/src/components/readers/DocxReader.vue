<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { getContentUrl } from '@/api/client'
import ReaderStatus from './ReaderStatus.vue'

const props = defineProps<{ shareId: string; path: string }>()
const container = ref<HTMLElement | null>(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  if (container.value) container.value.replaceChildren()
  try {
    const [{ renderAsync }, response] = await Promise.all([
      import('docx-preview'),
      fetch(getContentUrl(props.shareId, props.path)),
    ])
    if (!response.ok) throw new Error('无法读取 Word 文档')
    if (!container.value) return
    await renderAsync(await response.arrayBuffer(), container.value, undefined, {
      className: 'docx-document',
      inWrapper: true,
      ignoreWidth: false,
      ignoreHeight: false,
      breakPages: true,
      useBase64URL: true,
    })
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '无法预览 Word 文档'
  } finally {
    loading.value = false
  }
}

watch(() => [props.shareId, props.path], load)
onMounted(load)
</script>

<template>
  <ReaderStatus :loading="loading" :error="error" />
  <div v-show="!error" ref="container" class="docx-reader"></div>
</template>
