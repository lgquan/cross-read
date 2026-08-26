<script setup lang="ts">
import { AudioLines } from '@lucide/vue'
import { computed, ref } from 'vue'

import { getMediaUrl } from '@/api/client'

const props = defineProps<{ shareId: string; path: string }>()
const playbackError = ref('')
const mediaUrl = computed(() => getMediaUrl(props.shareId, props.path))
</script>

<template>
  <div class="audio-reader">
    <span class="audio-reader-icon" aria-hidden="true"><AudioLines :size="30" /></span>
    <audio
      :src="mediaUrl"
      controls
      preload="metadata"
      @error="playbackError = 'Safari 无法播放这个音频，文件内部编码可能不兼容。'"
    >
      当前浏览器不支持 HTML5 音频播放。
    </audio>
    <p v-if="playbackError" class="reader-error">{{ playbackError }}</p>
  </div>
</template>
