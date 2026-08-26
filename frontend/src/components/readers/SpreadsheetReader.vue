<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { getContentUrl } from '@/api/client'
import { parseSpreadsheet, type PreviewSheet } from '@/utils/spreadsheet'
import ReaderStatus from './ReaderStatus.vue'

const props = defineProps<{ shareId: string; path: string }>()
const sheets = ref<PreviewSheet[]>([])
const activeSheetIndex = ref(0)
const loading = ref(true)
const error = ref('')
const activeSheet = computed(() => sheets.value[activeSheetIndex.value])

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  sheets.value = []
  activeSheetIndex.value = 0
  try {
    const response = await fetch(getContentUrl(props.shareId, props.path))
    if (!response.ok) throw new Error('无法读取表格文件')
    sheets.value = await parseSpreadsheet(await response.arrayBuffer(), props.path)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '无法预览表格文件'
  } finally {
    loading.value = false
  }
}

watch(() => [props.shareId, props.path], load)
onMounted(load)
</script>

<template>
  <ReaderStatus :loading="loading" :error="error" />
  <div v-if="!loading && !error" class="spreadsheet-reader">
    <nav v-if="sheets.length > 1" class="sheet-tabs" role="tablist" aria-label="工作表">
      <button
        v-for="(sheet, index) in sheets"
        :key="`${sheet.name}-${index}`"
        type="button"
        role="tab"
        :aria-selected="activeSheetIndex === index"
        @click="activeSheetIndex = index"
      >
        {{ sheet.name }}
      </button>
    </nav>

    <div v-if="activeSheet?.rows.length" class="sheet-table-wrap">
      <table class="sheet-table">
        <thead>
          <tr>
            <th class="sheet-row-number" scope="col">1</th>
            <th v-for="(cell, index) in activeSheet.rows[0]" :key="index" scope="col">
              {{ cell }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in activeSheet.rows.slice(1)" :key="rowIndex">
            <th class="sheet-row-number" scope="row">{{ rowIndex + 2 }}</th>
            <td v-for="(cell, cellIndex) in row" :key="cellIndex">{{ cell }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="reader-empty">这个工作表没有可显示的单元格。</div>

    <p v-if="activeSheet?.truncatedRows || activeSheet?.truncatedColumns" class="preview-limit-note">
      表格较大，当前显示前 2000 行、100 列。
    </p>
  </div>
</template>
