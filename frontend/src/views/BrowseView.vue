<script setup lang="ts">
import { ChevronLeft, ChevronRight, Home, Search, X } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getEntries, searchEntries } from '@/api/client'
import FileKindIcon from '@/components/FileKindIcon.vue'
import StatePanel from '@/components/StatePanel.vue'
import type { DirectoryResponse, FileEntry } from '@/types/files'
import { formatFileSize, formatModifiedAt } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const data = ref<DirectoryResponse | null>(null)
const loading = ref(true)
const error = ref('')
const search = ref('')
const searchMode = ref<'current' | 'recursive'>('current')
const recursiveItems = ref<FileEntry[]>([])
const recursiveLoading = ref(false)
const recursiveError = ref('')
const recursiveTruncated = ref(false)
let searchGeneration = 0

const shareId = computed(() => String(route.params.shareId))
const currentPath = computed(() => (typeof route.query.path === 'string' ? route.query.path : ''))
const pathParts = computed(() => currentPath.value.split('/').filter(Boolean))
const visibleItems = computed(() => {
  const query = search.value.trim().toLocaleLowerCase()
  if (!query) return data.value?.items ?? []
  return (data.value?.items ?? []).filter((item) => item.name.toLocaleLowerCase().includes(query))
})
const showingRecursiveResults = computed(
  () => searchMode.value === 'recursive' && search.value.trim().length > 0,
)
const displayedItems = computed(() =>
  showingRecursiveResults.value ? recursiveItems.value : visibleItems.value,
)

function pathAt(index: number): string {
  return pathParts.value.slice(0, index + 1).join('/')
}

function goToPath(path: string) {
  void router.push({ name: 'browse', params: { shareId: shareId.value }, query: path ? { path } : {} })
}

function goUp() {
  if (pathParts.value.length === 0) {
    void router.push({ name: 'home' })
    return
  }
  goToPath(pathParts.value.slice(0, -1).join('/'))
}

function openEntry(entry: FileEntry) {
  if (entry.is_directory) {
    goToPath(entry.path)
    return
  }
  void router.push({
    name: 'preview',
    params: { shareId: shareId.value },
    query: { path: entry.path, kind: entry.kind },
  })
}

async function loadRecursiveResults() {
  const query = search.value.trim()
  const generation = ++searchGeneration
  recursiveError.value = ''
  recursiveTruncated.value = false
  if (!query || searchMode.value !== 'recursive') {
    recursiveItems.value = []
    recursiveLoading.value = false
    return
  }

  recursiveLoading.value = true
  try {
    const result = await searchEntries(shareId.value, currentPath.value, query)
    if (generation !== searchGeneration) return
    recursiveItems.value = result.items
    recursiveTruncated.value = result.truncated
  } catch (reason) {
    if (generation !== searchGeneration) return
    recursiveError.value = reason instanceof Error ? reason.message : '搜索失败，请稍后重试'
    recursiveItems.value = []
  } finally {
    if (generation === searchGeneration) recursiveLoading.value = false
  }
}

async function loadEntries() {
  loading.value = true
  error.value = ''
  search.value = ''
  searchMode.value = 'current'
  recursiveItems.value = []
  recursiveError.value = ''
  recursiveTruncated.value = false
  searchGeneration += 1
  try {
    data.value = await getEntries(shareId.value, currentPath.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '无法打开这个文件夹'
  } finally {
    loading.value = false
  }
}

watch([shareId, currentPath], loadEntries)
watch([search, searchMode, shareId, currentPath], loadRecursiveResults)
onMounted(loadEntries)
</script>

<template>
  <section class="browse-header">
    <button class="icon-button back-button" type="button" aria-label="返回上一级" @click="goUp">
      <ChevronLeft :size="23" />
    </button>
    <div class="browse-title">
      <p class="eyebrow">{{ data?.share.name ?? '资料库' }}</p>
      <h1>{{ pathParts[pathParts.length - 1] ?? data?.share.name ?? '正在加载' }}</h1>
    </div>
  </section>

  <nav v-if="data" class="breadcrumbs" aria-label="当前位置">
    <button type="button" title="资料库根目录" @click="goToPath('')">
      <Home :size="15" />
    </button>
    <template v-for="(part, index) in pathParts" :key="pathAt(index)">
      <ChevronRight :size="14" aria-hidden="true" />
      <button type="button" @click="goToPath(pathAt(index))">{{ part }}</button>
    </template>
  </nav>

  <div v-if="data && data.items.length > 0" class="search-tools">
    <label class="search-field">
      <Search :size="18" aria-hidden="true" />
      <input
        v-model="search"
        type="search"
        :placeholder="searchMode === 'recursive' ? '搜索当前文件夹及子文件夹' : '筛选当前文件夹'"
        autocomplete="off"
      />
      <button v-if="search" type="button" aria-label="清除筛选" @click="search = ''">
        <X :size="16" />
      </button>
    </label>
    <div class="search-scope" role="group" aria-label="搜索范围">
      <button
        type="button"
        :aria-pressed="searchMode === 'current'"
        @click="searchMode = 'current'"
      >
        当前文件夹
      </button>
      <button
        type="button"
        :aria-pressed="searchMode === 'recursive'"
        @click="searchMode = 'recursive'"
      >
        包含子文件夹
      </button>
    </div>
  </div>

  <p v-if="showingRecursiveResults && recursiveTruncated" class="search-note">
    匹配结果较多，仅显示前 500 项。
  </p>

  <div v-if="loading" class="file-list" aria-label="正在加载">
    <div v-for="index in 5" :key="index" class="file-row skeleton-row"></div>
  </div>

  <StatePanel
    v-else-if="error"
    kind="error"
    title="无法打开文件夹"
    :message="error"
    retryable
    @retry="loadEntries"
  />

  <StatePanel
    v-else-if="data?.items.length === 0"
    title="这里还没有文件"
    message="这个文件夹是空的。"
  />

  <StatePanel
    v-else-if="showingRecursiveResults && recursiveLoading"
    title="正在搜索"
    message="正在查找当前文件夹及其子文件夹。"
  />

  <StatePanel
    v-else-if="showingRecursiveResults && recursiveError"
    kind="error"
    title="搜索失败"
    :message="recursiveError"
    retryable
    @retry="loadRecursiveResults"
  />

  <StatePanel
    v-else-if="displayedItems.length === 0"
    title="没有匹配的文件"
    message="换一个关键词试试。"
  />

  <section v-else class="file-list" aria-label="文件列表">
    <button
      v-for="entry in displayedItems"
      :key="entry.path"
      class="file-row"
      type="button"
      @click="openEntry(entry)"
    >
      <FileKindIcon :kind="entry.kind" />
      <span class="file-copy">
        <strong>{{ entry.name }}</strong>
        <small>
          <template v-if="showingRecursiveResults">
            {{ entry.path }}
          </template>
          <template v-else>
            {{ formatFileSize(entry.size) }}
            <span aria-hidden="true"> · </span>
            {{ formatModifiedAt(entry.modified_at) }}
          </template>
        </small>
      </span>
      <ChevronRight class="row-chevron" :size="18" aria-hidden="true" />
    </button>
  </section>
</template>
