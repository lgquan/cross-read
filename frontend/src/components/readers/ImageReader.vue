<script setup lang="ts">
import { RotateCcw, ZoomIn, ZoomOut } from '@lucide/vue'
import { computed, ref } from 'vue'

import { getContentUrl } from '@/api/client'

const props = defineProps<{ shareId: string; path: string; alt: string }>()
const scale = ref(1)
const imageUrl = computed(() => getContentUrl(props.shareId, props.path))

function changeScale(amount: number) {
  scale.value = Math.min(4, Math.max(0.25, scale.value + amount))
}
</script>

<template>
  <div class="reader-toolbar" aria-label="图片缩放">
    <button type="button" aria-label="缩小" @click="changeScale(-0.25)"><ZoomOut :size="18" /></button>
    <span>{{ Math.round(scale * 100) }}%</span>
    <button type="button" aria-label="放大" @click="changeScale(0.25)"><ZoomIn :size="18" /></button>
    <button type="button" aria-label="恢复原始缩放" @click="scale = 1"><RotateCcw :size="17" /></button>
  </div>
  <div class="image-reader">
    <img :src="imageUrl" :alt="alt" :style="{ transform: `scale(${scale})` }" />
  </div>
</template>
