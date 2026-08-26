<script setup lang="ts">
import { BookOpen } from '@lucide/vue'
import { computed } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useRoute } from 'vue-router'

const route = useRoute()
const isMarkdownReader = computed(
  () => route.name === 'preview' && route.query.kind === 'markdown',
)
</script>

<template>
  <div class="app-shell">
    <header class="top-bar">
      <RouterLink to="/" class="brand" aria-label="返回 Cross Read 首页">
        <span class="brand-mark"><BookOpen :size="19" :stroke-width="2.1" /></span>
        <span>Cross Read</span>
      </RouterLink>
      <span v-if="!isMarkdownReader" class="connection-pill">
        <span class="connection-dot" aria-hidden="true"></span>
        局域网
      </span>
    </header>

    <main class="page-container">
      <RouterView />
    </main>
  </div>
</template>
