# 异步架构规范 (Async Architecture Specification)

## 1. 统一原则

### 核心目标
- 高频页面不再整页阻塞
- 模块级 loading / error / retry / skeleton 统一
- 轮询 / 并发竞态大幅降低
- 后续页面有规范可依

### 三层抽象

| 层 | 抽象 | 职责 |
|---|---|---|
| RPC 层 | `rpcSafe` (useRpcSafe) | 请求安全包装：超时、重试、abort、去重 |
| 模块状态层 | `useAsyncModule` | 模块级状态管理：loading/error/data/refresh/retry |
| 视图层 | `AsyncSection` | 统一 UI 状态渲染：skeleton / loading / error / empty / retry |

### 关键约束
1. **禁止整页 loading**：不得用单一 store loading 或单一 `v-if="loading"` 阻塞整页
2. **禁止人工 setTimeout 做等待**：不得用 `new Promise(setTimeout(...))` 模拟等待
3. **禁止裸 wsStore.rpc 调用**：所有 RPC 必须经过 `rpc.call()` (即 `rpcSafe`)
4. **禁止串行非必要请求**：独立数据必须用 `Promise.allSettled` 并发获取
5. **轮询必须有防竞态**：轮询函数内必须有 `if (loading.value) return` 守卫，或使用 `useAsyncModule` 的 polling 管理

---

## 2. rpcSafe（useRpcSafe）用法

### 签名
```ts
const rpc = useRpcSafe()

// 调用方式
const result = await rpc.call(() => wsStore.rpc.someMethod(args), {
  label: 'someMethod',     // 日志标签（必填）
  timeout: 10000,          // 超时 ms（必填）
  retries: 1,              // 重试次数（默认 0，建议慢接口设 1）
})
```

### 规则
- **所有** `wsStore.rpc.*` 调用必须通过 `rpc.call()` 包装
- 不得直接调用 `wsStore.rpc.method()` 而绕过 rpcSafe
- `label` 用于日志追踪，必须填写
- `timeout` 必须填写，慢查询（listSessions / tailLogs 等）建议 10-20s
- `retries` 对易超时接口（网络不稳定环境）建议设 1

### 禁止示例
```ts
// ❌ 禁止：裸调用，无超时保护
const result = await wsStore.rpc.listSessions()

// ✅ 正确：通过 rpcSafe 调用
const result = await rpc.call(() => wsStore.rpc.listSessions(), {
  label: 'listSessions', timeout: 12000, retries: 1
})
```

---

## 3. useAsyncModule 用法

### 作用
管理一个异步模块的完整生命周期状态：loading / refreshing / error / data / retry。

### 基本用法
```ts
import { useAsyncModule } from '@/composables/useAsyncModule'

// 在组件 setup 中
const agentsState = useAsyncModule(async () => {
  return agentStore.fetchAgents()
})

// 使用状态
agentsState.loading.value   // boolean
agentsState.error.value     // Error | null
agentsState.data.value      // any（fetch 返回值）
agentsState.refresh()        // 手动刷新（设置 refreshing）
agentsState.retry()         // 重试当前操作
```

### polling 管理（自动竞态防护）
```ts
const presenceState = useAsyncModule(async () => {
  return wsStore.rpc.getSystemPresence()
}, {
  pollingInterval: 8000,   // 每 8s 自动轮询
  immediate: true,         // 立即执行一次
})

// 组件卸载时自动清理 timer
onUnmounted(() => presenceState.destroy())
```

### 规则
- `useAsyncModule` 适合**高频、需轮询**的模块
- 简单一次性数据获取可只用 `rpc.call()` + `ref` 手动管理状态
- 返回的 `state` 对象是响应式的，可直接传给 `AsyncSection`

---

## 4. AsyncSection 用法

### 作用
统一渲染异步模块的 UI 状态：skeleton / loading / refreshing / error / empty。

### Props

| Prop | Type | 说明 |
|---|---|---|
| `loading` | `boolean \| Ref<boolean>` | 是否首次加载中 |
| `refreshing` | `boolean \| Ref<boolean>` | 是否刷新中（显示顶部细条） |
| `error` | `Error \| string \| null \| Ref<...>` | 错误信息 |
| `errorLabel` | `string` | 错误卡片标题（默认 "加载失败"） |
| `showSkeleton` | `boolean` | 是否显示骨架屏（默认 false） |
| `skeletonHeight` | `string` | 骨架屏高度（如 "200px"） |
| `empty` | `boolean` | 是否为空（默认 false） |
| `emptyLabel` | `string` | 空状态文案（默认 "暂无数据"） |

### Slots

| Slot | 触发条件 | 用途 |
|---|---|---|
| `#skeleton` | `loading === true` | 自定义骨架屏内容 |
| (default) | `loading === false && !error && !empty` | 正常内容（自动渲染） |
| `#error` | `error !== null` | 自定义错误 UI |
| `#empty` | `empty === true` | 自定义空状态 UI |

### Events
- `@retry` — 用户点击重试按钮时触发

### 正确接入模式（重要）

AsyncSection 有两种使用模式，**必须使用第一种**：

#### 模式 A（推荐）：两个 AsyncSection + v-if/v-else

```vue
<!-- loading 时显示骨架 -->
<AsyncSection
  v-if="isLoading"
  :loading="false"
  :show-skeleton="true"
  skeleton-height="200px"
>
  <template #skeleton>
    <div class="my-skeleton">...</div>
  </template>
</AsyncSection>

<!-- 非 loading 时显示内容（自动处理 error/empty） -->
<AsyncSection
  v-else
  :loading="false"
  :error="myError || null"
  error-label="数据加载失败"
  @retry="fetchData"
>
  <MyContent />
</AsyncSection>
```

**原理**：`v-if` 和 `v-else` 是互斥的，同一时间只有一个 AsyncSection 在 DOM 中，避免骨架屏和内容同时渲染。

#### 模式 B（仅简单场景）：单一 AsyncSection

如果内容简单（无复杂状态），可用单一 AsyncSection 配合 `v-if`：

```vue
<AsyncSection
  :loading="isLoading"
  :error="myError || null"
  :show-skeleton="true"
  skeleton-height="200px"
  @retry="fetchData"
>
  <template #skeleton>
    <div class="my-skeleton">...</div>
  </template>
  <MyContent v-if="!isLoading" />
</AsyncSection>
```

### 禁止写法

```vue
<!-- ❌ 错误：skeleton slot 和 default slot 内容同时渲染 -->
<AsyncSection :loading="loading" :show-skeleton="true">
  <template #skeleton>
    <SkeletonCard />
  </template>
  <ActualCard />  <!-- 这个 content 也会渲染到 DOM -->
</AsyncSection>

<!-- ✅ 正确：用 v-if/v-else 互斥 -->
<AsyncSection v-if="loading" ...>...</AsyncSection>
<AsyncSection v-else ...><ActualCard /></AsyncSection>
```

---

## 5. 页面该怎么接

### 步骤 1：在 setup 中定义模块状态

```ts
// 每个独立模块定义自己的加载状态
const statsLoading = ref(true)
const statsError = ref<Error | string | null>(null)

const kpisLoading = ref(true)
const kpisError = ref<Error | string | null>(null)
```

### 步骤 2：fetch 函数设置 loading/error

```ts
async function fetchStats() {
  statsLoading.value = true
  statsError.value = null
  try {
    stats.value = await rpc.call(() => wsStore.rpc.listSessions(), {
      label: 'listSessions', timeout: 12000, retries: 1
    })
  } catch (err) {
    statsError.value = err instanceof Error ? err.message : String(err)
  } finally {
    statsLoading.value = false
  }
}

function retryStats() {
  void fetchStats()
}
```

### 步骤 3：并发获取多个独立模块

```ts
async function loadDashboard() {
  // 5 个独立模块并发获取，互不阻塞
  await Promise.allSettled([
    fetchStats(),
    fetchKpis(),
    fetchTrend(),
    fetchStructure(),
    fetchTop(),
  ])
}

onMounted(() => {
  void loadDashboard()
})
```

### 步骤 4：在模板中用 AsyncSection 包装

```vue
<!-- 每个模块独立渲染，互不阻塞 -->
<AsyncSection v-if="statsLoading" :show-skeleton="true" skeleton-height="88px">
  <template #skeleton><StatCardSkeleton /></template>
</AsyncSection>
<AsyncSection v-else :error="statsError || null" @retry="retryStats">
  <StatCards />
</AsyncSection>
```

### 步骤 5：刷新按钮

```ts
const refreshing = ref(false)

async function handleRefresh() {
  refreshing.value = true
  try {
    await Promise.allSettled([fetchStats(), fetchKpis()])
  } finally {
    refreshing.value = false
  }
}
```

---

## 6. 什么写法禁止继续新增

### ❌ 禁止 1：整页 NSpin 阻塞
```vue
<!-- ❌ 禁止：单一 loading 阻塞整页 -->
<NSpin :show="store.loading">
  <AllContent />
</NSpin>

<!-- ✅ 改为：每个模块独立 -->
<AsyncSection v-if="agentsLoading" ...>...</AsyncSection>
<AsyncSection v-else ...>...</AsyncSection>
```

### ❌ 禁止 2：人工 setTimeout 模拟等待
```ts
// ❌ 禁止
await new Promise(resolve => setTimeout(resolve, 1000))
doSomething()

// ✅ 改为：直接调用，让 rpcSafe 处理超时
await rpc.call(() => doSomething(), { timeout: 5000 })
```

### ❌ 禁止 3：串行请求链（可并发的场景）
```ts
// ❌ 禁止
const agents = await fetchAgents()
const sessions = await fetchSessions()

// ✅ 改为：并发
const [agents, sessions] = await Promise.allSettled([
  fetchAgents(),
  fetchSessions(),
])
```

### ❌ 禁止 4：轮询无竞态保护
```ts
// ❌ 禁止：快速连续触发可能产生竞态
setInterval(async () => {
  await fetchData() // 如果上次还没完成，会叠加
}, 2000)

// ✅ 改为：守卫检查
setInterval(() => {
  if (loading.value) return
  void fetchData()
}, 2000)
```

### ❌ 禁止 5：裸 wsStore.rpc 调用
```ts
// ❌ 禁止
const data = await wsStore.rpc.listSessions()

// ✅ 改为
const data = await rpc.call(() => wsStore.rpc.listSessions(), {
  label: 'listSessions', timeout: 12000, retries: 1
})
```

### ❌ 禁止 6：try/catch 吞掉错误不处理
```ts
// ❌ 禁止：错误静默消失
try {
  await rpc.call(...)
} catch {}

// ✅ 改为：记录错误并设置 error 状态
try {
  await rpc.call(...)
} catch (err) {
  error.value = err instanceof Error ? err.message : String(err)
}
```

---

## 7. 轮询规范

### 基础模式
```ts
let timer: ReturnType<typeof setInterval> | null = null

function startPolling() {
  stopPolling() // 先清理
  timer = setInterval(() => {
    if (isLoading.value) return  // 防竞态
    void fetchData()
  }, intervalMs)
}

function stopPolling() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onMounted(() => startPolling())
onUnmounted(() => stopPolling())

// Tab 切换时启停轮询
watch(activeTab, (tab) => {
  if (tab === 'presence') startPolling()
  else stopPolling()
})
```

### 使用 useAsyncModule 管理轮询（推荐）
```ts
const state = useAsyncModule(async () => {
  return wsStore.rpc.getSystemPresence()
}, {
  pollingInterval: 8000,
  immediate: true,
})

// 自动处理：loading 竞态、timer 清理、refreshing 状态
onUnmounted(() => state.destroy())
```

---

## 8. 后续迁移建议

### 已迁移页面
- ✅ Dashboard (src/views/Dashboard.vue)
- ✅ MonitorPage (src/views/monitor/MonitorPage.vue)
- ✅ OfficePage (src/views/office/OfficePage.vue)

### 待迁移页面
以下页面尚未接入 AsyncSection，建议按以下顺序迁移：

1. **FilesPage** — 文件页面，加载慢时可分模块 skeleton
2. **Settings 相关页面** — 配置页面，每个 section 独立加载
3. **SessionStore / ChatStore** — 考虑暴露 `useAsyncModule` 给页面使用

### 迁移检查清单
- [ ] 所有 `wsStore.rpc.*` 调用是否都通过 `rpc.call()`？
- [ ] 是否有新的 `setTimeout` 人工延迟需要清理？
- [ ] 是否有新的串行请求链可以改为 `Promise.allSettled`？
- [ ] 轮询是否有 `if (loading) return` 守卫？
- [ ] AsyncSection 是否使用了 v-if/v-else 双组件模式？
- [ ] Build 是否通过？

---

## 9. 相关文件索引

| 文件 | 说明 |
|---|---|
| `src/composables/useRpcSafe.ts` | RPC 安全包装器 |
| `src/composables/useAsyncModule.ts` | 模块级异步状态管理 |
| `src/components/common/AsyncSection.vue` | 统一异步 UI 组件 |
| `src/views/Dashboard.vue` | 异步架构落地示例 |
| `src/views/monitor/MonitorPage.vue` | 异步架构落地示例（+ 轮询管理） |
| `src/views/office/OfficePage.vue` | 模块级 loading 落地示例 |
