<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  NAlert,
  NButton,
  NCard,
  NGrid,
  NGridItem,
  NSpace,
  NTag,
  NText,
  NProgress,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NEmpty,
  useMessage,
} from 'naive-ui'
import { AddOutline, TrashOutline, RefreshOutline } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'

// ─── Types ──────────────────────────────────────────────────────────────────

interface ModelRemain {
  model_name?: string
  model_id?: string
  current_interval_total_count?: number
  current_interval_usage_count?: number
  remains_time?: number
  start_time?: string
  end_time?: string
  [key: string]: unknown
}

interface MiniMaxResponse {
  model_remains?: ModelRemain[]
  [key: string]: unknown
}

interface StoredKeyMeta {
  id: string
  platform: string
  label: string
  key_prefix: string
  key_suffix: string
}

interface BatchResult {
  id: string
  label: string
  platform: string
  ok: boolean
  data: MiniMaxResponse | null
  error: string | null
}

// ─── Platform registry ───────────────────────────────────────────────────────

const PLATFORMS = [
  { id: 'minimax', name: 'MiniMax' },
]

// ─── State ───────────────────────────────────────────────────────────────────

const { t } = useI18n()
const message = useMessage()
const authStore = useAuthStore()
const { isDark } = useTheme()

const keys = ref<StoredKeyMeta[]>([])
const results = ref<Map<string, BatchResult>>(new Map())
const loading = ref(false)
const lastRefreshedAt = ref<number | null>(null)
const autoRefresh = ref(true)
const addModalVisible = ref(false)
const addForm = ref({ platform: 'minimax', label: '', rawKey: '' })
const addLoading = ref(false)
let autoRefreshTimer: ReturnType<typeof setInterval> | null = null

// ─── Helpers ─────────────────────────────────────────────────────────────────

function maskDisplay(k: StoredKeyMeta) {
  return `${k.key_prefix}****${k.key_suffix}`
}

function formatRemainsTime(ms?: number): string {
  if (!ms || ms <= 0) return '已重置'
  const totalMin = Math.floor(ms / 60000)
  const h = Math.floor(totalMin / 60)
  const m = totalMin % 60
  if (h > 0) return `${h}小时${m > 0 ? m + '分钟' : ''}`
  return `${m}分钟`
}

function formatCycleTime(iso?: string): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const hh = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${mm}/${dd} ${hh}:${min}`
  } catch {
    return iso
  }
}

function remainingPercent(item: ModelRemain): number {
  const total = item.current_interval_total_count ?? 0
  // current_interval_usage_count 实际是剩余额度（用户纠正）
  const remaining = item.current_interval_usage_count ?? 0
  if (total === 0) return 0
  return Math.min(100, Math.round((remaining / total) * 100))
}

function progressColor(pct: number): string {
  if (pct <= 20) return '#ef4444'
  if (pct <= 40) return '#f59e0b'
  return '#22c55e'
}

function modelDisplayName(item: ModelRemain): string {
  return item.model_name ?? item.model_id ?? 'Unknown'
}

// ─── API calls ────────────────────────────────────────────────────────────────

async function fetchKeys() {
  try {
    const token = authStore.getToken()
    const resp = await fetch('/api/quota/keys', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const json = await resp.json() as { keys: StoredKeyMeta[] }
    keys.value = json.keys ?? []
  } catch (err) {
    message.error('读取 Key 列表失败: ' + (err instanceof Error ? err.message : String(err)))
  }
}

async function fetchAllQuotas() {
  if (keys.value.length === 0) {
    results.value = new Map()
    return
  }
  loading.value = true
  try {
    const token = authStore.getToken()
    const resp = await fetch('/api/quota/minimax/batch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ ids: keys.value.map(k => k.id) }),
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const json = await resp.json() as { results: BatchResult[] }
    const m = new Map<string, BatchResult>()
    for (const r of json.results) m.set(r.id, r)
    results.value = m
    lastRefreshedAt.value = Date.now()
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    message.error('查询余量失败: ' + msg)
    const m = new Map<string, BatchResult>()
    for (const k of keys.value) {
      m.set(k.id, { id: k.id, label: k.label, platform: k.platform, ok: false, data: null, error: msg })
    }
    results.value = m
  } finally {
    loading.value = false
  }
}

async function addKey() {
  if (!addForm.value.label.trim() || !addForm.value.rawKey.trim()) return
  addLoading.value = true
  try {
    const token = authStore.getToken()
    const resp = await fetch('/api/quota/keys', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        platform: addForm.value.platform,
        label: addForm.value.label.trim(),
        raw_key: addForm.value.rawKey.trim(),
      }),
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: 'Unknown error' })) as { error: string }
      throw new Error(err.error ?? `HTTP ${resp.status}`)
    }
    await fetchKeys()
    await fetchAllQuotas()
    addModalVisible.value = false
    addForm.value = { platform: 'minimax', label: '', rawKey: '' }
    message.success('Key 添加成功')
  } catch (err) {
    message.error('添加失败: ' + (err instanceof Error ? err.message : String(err)))
  } finally {
    addLoading.value = false
  }
}

async function deleteKey(id: string) {
  try {
    const token = authStore.getToken()
    const resp = await fetch(`/api/quota/keys/${id}`, {
      method: 'DELETE',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    keys.value = keys.value.filter(k => k.id !== id)
    results.value.delete(id)
    results.value = new Map(results.value)
    message.success('已删除')
  } catch (err) {
    message.error('删除失败: ' + (err instanceof Error ? err.message : String(err)))
  }
}

// ─── Lifecycle ───────────────────────────────────────────────────────────────

onMounted(async () => {
  await fetchKeys()
  await fetchAllQuotas()
  if (autoRefresh.value) {
    autoRefreshTimer = setInterval(() => void fetchAllQuotas(), 60_000)
  }
})

onUnmounted(() => {
  if (autoRefreshTimer) clearInterval(autoRefreshTimer)
})

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    autoRefreshTimer = setInterval(() => void fetchAllQuotas(), 60_000)
  } else {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

// ─── Card status ──────────────────────────────────────────────────────────────

function cardStatus(result: BatchResult | undefined): 'ok' | 'error' | 'empty' {
  if (!result || !result.ok) return 'error'
  if (!result.data?.model_remains?.length) return 'empty'
  return 'ok'
}

function keyStatusDot(result: BatchResult | undefined): 'success' | 'error' | 'default' {
  const s = cardStatus(result)
  if (s === 'ok') return 'success'
  if (s === 'error') return 'error'
  return 'default'
}

function keyStatusLabel(result: BatchResult | undefined, k: StoredKeyMeta): string {
  const s = cardStatus(result)
  if (s === 'error') return '查询失败'
  if (s === 'empty') return '无数据'
  return '正常'
}
</script>

<template>
  <NSpace vertical :size="16">
    <!-- Header -->
    <NCard class="app-card" :title="t('pages.modelQuotaMonitor.title')">
      <template #header-extra>
        <NSpace align="center">
          <NText depth="3" style="font-size: 0.82rem">
            {{ lastRefreshedAt ? `上次刷新: ${new Date(lastRefreshedAt).toLocaleTimeString('zh-CN')}` : '' }}
          </NText>
          <NButton
            :type="autoRefresh ? 'primary' : 'default'"
            size="small"
            @click="toggleAutoRefresh"
          >
            <template #icon><RefreshOutline /></template>
            {{ autoRefresh ? '自动刷新中' : '自动刷新暂停' }}
          </NButton>
          <NButton type="primary" size="small" :loading="loading" @click="fetchAllQuotas">
            <template #icon><RefreshOutline /></template>
            刷新
          </NButton>
        </NSpace>
      </template>

      <NSpace vertical :size="8">
        <NText depth="3">管理各平台 API Key，实时查看 Token 额度余量与周期重置时间。</NText>
        <NAlert type="info" :show-icon="true">
          Key 密文存储于服务器数据库，刷新页面后自动从服务器读取，无需重新输入。
        </NAlert>
      </NSpace>
    </NCard>

    <!-- Platform sections -->
    <template v-for="platform in PLATFORMS" :key="platform.id">
      <NCard class="app-card">
        <template #header>
          <NSpace align="center" :size="12">
            <NTag type="info" size="small">{{ platform.name }}</NTag>
            <NText depth="3" style="font-size: 0.82rem">
              {{ keys.filter(k => k.platform === platform.id).length }} 个 Key
            </NText>
          </NSpace>
        </template>
        <template #header-extra>
          <NButton size="small" type="primary" @click="addModalVisible = true">
            <template #icon><AddOutline /></template>
            添加 Key
          </NButton>
        </template>

        <!-- Key cards grid -->
        <NSpace v-if="keys.filter(k => k.platform === platform.id).length > 0" vertical :size="12">
          <NGrid :cols="2" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true">
            <NGridItem
              v-for="k in keys.filter(k => k.platform === platform.id)"
              :key="k.id"
              span="0:24 900:12"
            >
              <NCard
                class="quota-key-card"
                :class="`status-${cardStatus(results.get(k.id))}`"
                size="small"
              >
                <template #header>
                  <NSpace align="center" justify="space-between" style="width: 100%">
                    <NSpace align="center" :size="8">
                      <NTag type="info" size="tiny">{{ k.platform.toUpperCase() }}</NTag>
                      <NText strong style="font-size: 0.9rem">{{ k.label }}</NText>
                    </NSpace>
                    <NSpace align="center" :size="6">
                      <NTag
                        :type="keyStatusDot(results.get(k.id))"
                        size="tiny"
                        round
                      >
                        {{ keyStatusLabel(results.get(k.id), k) }}
                      </NTag>
                      <NButton
                        quaternary
                        size="tiny"
                        circle
                        @click="deleteKey(k.id)"
                        title="删除此 Key"
                      >
                        <template #icon><TrashOutline style="color: #ef4444; font-size: 0.9rem" /></template>
                      </NButton>
                    </NSpace>
                  </NSpace>
                </template>

                <div class="key-masked">{{ maskDisplay(k) }}</div>

                <!-- Loading state -->
                <template v-if="loading">
                  <div class="quota-loading-rows">
                    <div class="quota-skeleton-row" v-for="i in 2" :key="i" />
                  </div>
                </template>

                <!-- Error state -->
                <template v-else-if="cardStatus(results.get(k.id)) === 'error'">
                  <div class="quota-error-msg">
                    ⚠ {{ results.get(k.id)?.error ?? '查询失败' }}
                  </div>
                </template>

                <!-- Empty state -->
                <template v-else-if="cardStatus(results.get(k.id)) === 'empty'">
                  <div class="quota-empty-msg">暂无余量数据</div>
                </template>

                <!-- Data state -->
                <template v-else>
                  <div
                    v-for="(item, idx) in (results.get(k.id)?.data?.model_remains ?? [])"
                    :key="idx"
                    class="quota-model-row"
                  >
                    <div class="quota-model-name">{{ modelDisplayName(item) }}</div>
                    <NProgress
                      type="line"
                      :percentage="remainingPercent(item)"
                      :color="progressColor(remainingPercent(item))"
                      :show-indicator="false"
                      :height="6"
                      :border-radius="4"
                      style="margin: 4px 0"
                    />
                    <NSpace justify="space-between" class="quota-stats-row">
                      <span>剩余 <strong :style="{ color: isDark ? '#f8fafc' : '#0f172a' }">{{ (item.current_interval_usage_count ?? 0).toLocaleString() }}</strong></span>
                      <span>总额 <strong :style="{ color: isDark ? '#f8fafc' : '#0f172a' }">{{ (item.current_interval_total_count ?? 0).toLocaleString() }}</strong></span>
                    </NSpace>
                    <div v-if="item.remains_time" class="quota-reset-text">
                      重置于 {{ formatCycleTime(item.end_time) }}（约 {{ formatRemainsTime(item.remains_time) }}后）
                    </div>
                  </div>
                </template>
              </NCard>
            </NGridItem>
          </NGrid>
        </NSpace>

        <NEmpty v-else description="暂无可用 Key，请点击右上角添加" style="margin: 8px 0" />
      </NCard>
    </template>

    <!-- Add Key Modal -->
    <NModal
      v-model:show="addModalVisible"
      preset="card"
      title="添加 API Key"
      style="width: 480px; max-width: 95vw"
    >
      <NForm label-placement="top">
        <NFormItem label="平台">
          <NSelect
            v-model:value="addForm.platform"
            :options="PLATFORMS.map(p => ({ label: p.name, value: p.id }))"
          />
        </NFormItem>
        <NFormItem label="名称（如：Key 1 / 生产环境）">
          <NInput v-model:value="addForm.label" placeholder="给这个 Key 取个名字" />
        </NFormItem>
        <NFormItem label="API Key">
          <NInput
            v-model:value="addForm.rawKey"
            type="password"
            placeholder="粘贴 API Key（仅存入服务器，不在前端留存）"
            show-password-on="click"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="addModalVisible = false">取消</NButton>
          <NButton type="primary" :loading="addLoading" @click="addKey">添加</NButton>
        </NSpace>
      </template>
    </NModal>
  </NSpace>
</template>

<style scoped>
.quota-key-card {
  border-radius: 12px;
}

:deep(.dark) .quota-key-card,
:deep([data-theme='dark']) .quota-key-card {
  background: rgba(24, 24, 28, 0.92);
}
.quota-key-card.status-error {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(254, 242, 242, 0.5);
}
.quota-key-card.status-empty {
  opacity: 0.75;
}

.key-masked {
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  font-size: 0.78rem;
  color: #64748b;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 6px;
  display: inline-block;
  margin-bottom: 8px;
}

.quota-model-row {
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
}
.quota-model-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.quota-model-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quota-stats-row {
  font-size: 0.78rem;
  color: #64748b;
}

.quota-strong-value {
  color: #0f172a;
}

.quota-reset-text {
  font-size: 0.72rem;
  color: #94a3b8;
  margin-top: 2px;
}

:deep(.dark) .quota-model-name,
:deep([data-theme='dark']) .quota-model-name {
  color: #e5e7eb;
}

:deep(.dark) .quota-stats-row,
:deep([data-theme='dark']) .quota-stats-row {
  color: #cbd5e1;
}

:deep(.dark) .quota-reset-text,
:deep([data-theme='dark']) .quota-reset-text {
  color: #94a3b8;
}

:deep(.dark) .key-masked,
:deep([data-theme='dark']) .key-masked {
  background: #1f2937;
  color: #e5e7eb;
}

.quota-loading-rows {
  display: grid;
  gap: 8px;
}

.quota-skeleton-row {
  height: 52px;
  border-radius: 8px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.quota-error-msg {
  font-size: 0.82rem;
  color: #dc2626;
  padding: 4px 0;
}

.quota-empty-msg {
  font-size: 0.82rem;
  color: #94a3b8;
  padding: 4px 0;
}
</style>
