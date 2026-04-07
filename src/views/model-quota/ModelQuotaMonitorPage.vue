<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import {
  NAlert,
  NButton,
  NCard,
  NDataTable,
  NEmpty,
  NGrid,
  NGridItem,
  NSpace,
  NStatistic,
  NTag,
  NText,
  useMessage,
} from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import AsyncSection from '@/components/common/AsyncSection.vue'
import { useModelStore } from '@/stores/model'
import { useWebSocketStore } from '@/stores/websocket'
import { formatCompactNumber, formatDateTime } from '@/utils/format'
import type { DataTableColumns, TagProps } from 'naive-ui'
import type { SessionsUsageResult } from '@/api/types'

type RowStatus = 'healthy' | 'warning' | 'danger' | 'unknown'

type QuotaRow = {
  key: string
  model: string
  provider: string
  contextWindow: number | null
  usedTokens: number
  remainingTokens: number | null
  remainingPercent: number | null
  sessionCount: number
  status: RowStatus
}

const { t } = useI18n()
const message = useMessage()
const modelStore = useModelStore()
const wsStore = useWebSocketStore()

const loading = ref(false)
const lastError = ref<string | null>(null)
const lastUpdatedAt = ref<number | null>(null)
const usageDays = ref(7)
const sessionLimit = ref(100)
const usageResult = ref<SessionsUsageResult | null>(null)

const quotaRows = computed<QuotaRow[]>(() => {
  const models = modelStore.models
  const usage = usageResult.value
  const byModel = usage?.aggregates.byModel ?? []

  return models
    .map((model) => {
      const aggregate = byModel.find((item) => {
        const modelName = item.model?.trim()
        if (!modelName) return false
        return modelName === model.id || modelName === model.label
      })

      const contextWindow = typeof model.contextWindow === 'number' && model.contextWindow > 0
        ? model.contextWindow
        : null
      const usedTokens = aggregate?.totals.totalTokens ?? 0
      const remainingTokens = contextWindow != null ? Math.max(contextWindow - usedTokens, 0) : null
      const remainingPercent = contextWindow != null && contextWindow > 0
        ? Math.max(0, Math.min(100, Number((((remainingTokens ?? 0) / contextWindow) * 100).toFixed(1))))
        : null

      let status: RowStatus = 'unknown'
      if (remainingPercent != null) {
        if (remainingPercent <= 20) status = 'danger'
        else if (remainingPercent <= 40) status = 'warning'
        else status = 'healthy'
      }

      return {
        key: `${model.provider || 'unknown'}:${model.id}`,
        model: model.label || model.id,
        provider: model.provider || t('pages.modelQuotaMonitor.unknown'),
        contextWindow,
        usedTokens,
        remainingTokens,
        remainingPercent,
        sessionCount: aggregate?.count ?? 0,
        status,
      }
    })
    .sort((a, b) => {
      const aPercent = a.remainingPercent ?? -1
      const bPercent = b.remainingPercent ?? -1
      return aPercent - bPercent
    })
})

const activeRows = computed(() => quotaRows.value.filter((row) => row.sessionCount > 0))
const totalTokens = computed(() => usageResult.value?.totals.totalTokens ?? 0)
const activeSessions = computed(() => usageResult.value?.sessions.length ?? 0)

const statusTagType: Record<RowStatus, TagProps['type']> = {
  healthy: 'success',
  warning: 'warning',
  danger: 'error',
  unknown: 'default',
}

const columns = computed<DataTableColumns<QuotaRow>>(() => [
  {
    title: t('pages.modelQuotaMonitor.table.model'),
    key: 'model',
    minWidth: 220,
  },
  {
    title: t('pages.modelQuotaMonitor.table.provider'),
    key: 'provider',
    width: 140,
  },
  {
    title: t('pages.modelQuotaMonitor.table.contextWindow'),
    key: 'contextWindow',
    width: 140,
    render: (row) => row.contextWindow != null ? formatCompactNumber(row.contextWindow) : t('pages.modelQuotaMonitor.unknown'),
  },
  {
    title: t('pages.modelQuotaMonitor.table.usedTokens'),
    key: 'usedTokens',
    width: 140,
    render: (row) => formatCompactNumber(row.usedTokens),
  },
  {
    title: t('pages.modelQuotaMonitor.table.remainingTokens'),
    key: 'remainingTokens',
    width: 140,
    render: (row) => row.remainingTokens != null ? formatCompactNumber(row.remainingTokens) : t('pages.modelQuotaMonitor.unknown'),
  },
  {
    title: t('pages.modelQuotaMonitor.table.remainingPercent'),
    key: 'remainingPercent',
    width: 120,
    render: (row) => row.remainingPercent != null ? `${row.remainingPercent}%` : '--',
  },
  {
    title: t('pages.modelQuotaMonitor.table.sessionCount'),
    key: 'sessionCount',
    width: 100,
  },
  {
    title: t('pages.modelQuotaMonitor.table.status'),
    key: 'status',
    width: 140,
    render: (row) => h(
      NTag,
      { type: statusTagType[row.status], bordered: false },
      { default: () => t(`pages.modelQuotaMonitor.status.${row.status}`) },
    ),
  },
])

async function loadQuotaMonitor() {
  loading.value = true
  lastError.value = null
  try {
    await modelStore.fetchModels()
    const end = new Date()
    const start = new Date()
    start.setDate(end.getDate() - Math.max(usageDays.value - 1, 0))
    usageResult.value = await wsStore.rpc.getSessionsUsage({
      startDate: start.toISOString().slice(0, 10),
      endDate: end.toISOString().slice(0, 10),
      limit: sessionLimit.value,
    })
    lastUpdatedAt.value = Date.now()
  } catch (error) {
    const text = error instanceof Error ? error.message : String(error)
    lastError.value = text
    message.error(text)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadQuotaMonitor()
})
</script>

<template>
  <NSpace vertical :size="16">
    <NCard class="app-card" :title="t('pages.modelQuotaMonitor.title')">
      <template #header-extra>
        <NSpace align="center">
          <NText depth="3">{{ t('pages.modelQuotaMonitor.lastUpdated', { time: lastUpdatedAt ? formatDateTime(lastUpdatedAt) : '--' }) }}</NText>
          <NButton secondary @click="loadQuotaMonitor">
            <template #icon><RefreshOutline /></template>
            {{ t('pages.modelQuotaMonitor.refresh') }}
          </NButton>
        </NSpace>
      </template>
      <NSpace vertical :size="8">
        <NText depth="3">{{ t('pages.modelQuotaMonitor.subtitle') }}</NText>
        <NAlert type="info" :show-icon="true">{{ t('pages.modelQuotaMonitor.hints.estimation') }}</NAlert>
        <NAlert type="warning" :show-icon="true">{{ t('pages.modelQuotaMonitor.hints.missingContext') }}</NAlert>
      </NSpace>
    </NCard>

    <NGrid :cols="4" :x-gap="16">
      <NGridItem>
        <NCard class="app-card">
          <NStatistic :label="t('pages.modelQuotaMonitor.cards.models')" :value="quotaRows.length" />
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="app-card">
          <NStatistic :label="t('pages.modelQuotaMonitor.cards.activeModels')" :value="activeRows.length" />
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="app-card">
          <NStatistic :label="t('pages.modelQuotaMonitor.cards.activeSessions')" :value="activeSessions" />
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="app-card">
          <NStatistic :label="t('pages.modelQuotaMonitor.cards.totalTokens')" :value="formatCompactNumber(totalTokens)" />
        </NCard>
      </NGridItem>
    </NGrid>

    <NCard class="app-card" :title="t('pages.modelQuotaMonitor.title')">
      <template #header-extra>
        <NText depth="3">{{ t('pages.modelQuotaMonitor.limitLabel') }}: {{ sessionLimit }} ｜ {{ t('pages.modelQuotaMonitor.dateRangeDays') }}: {{ usageDays }}</NText>
      </template>
      <AsyncSection :loading="loading" :error-title="lastError || ''" @retry="loadQuotaMonitor">
        <template v-if="quotaRows.length">
          <NDataTable :columns="columns" :data="quotaRows" :pagination="{ pageSize: 20 }" :scroll-x="1100" />
        </template>
        <NEmpty v-else :description="t('pages.modelQuotaMonitor.noData')" />
      </AsyncSection>
    </NCard>
  </NSpace>
</template>
