# Async Architecture Migration Guide

> 飞书后台管理端的异步架构规范。本规范定义了页面异步加载的标准模式，确保所有页面使用统一的三层抽象。

## 1. 背景

### 问题

在异步架构迁移之前，页面存在以下问题：

1. **全局 `pageLoading` / 全局 `NSpin`**：整页阻塞式加载，用户体验差
2. **裸 `Promise.all` 无超时**：并行请求一个失败全部报错
3. **人工 `setTimeout` 等待后端**：不合理地假设后端响应时间
4. **重复 `fetch` 无去重**：快速切换/点击时产生竞态
5. **`timer` 不清理**：组件销毁后定时器继续运行，造成内存泄漏

### 解决

引入三层抽象：`rpcSafe` / `useAsyncModule` / `AsyncSection`，分别处理 RPC 调用安全封装、模块级状态管理、UI 加载态展示。

---

## 2. 三层抽象

### Layer 1: `rpcSafe` — RPC 调用安全封装

**职责**：为所有 WebSocket RPC 调用提供统一的超时、重试、错误处理。

**导入**：
```ts
import { useRpcSafe } from '@/composables/useRpcSafe'

const rpc = useRpcSafe()
```

**标准调用方式**：
```ts
// ✅ 正确：传入返回 Promise 的函数
const data = await rpc.call(
  () => wsStore.rpc.someMethod(arg),
  { label: 'someMethod', timeout: 10000, retries: 1 }
)

// ✅ 正确：HTTP fetch 也可以用 rpcSafe 包装（带超时）
const data = await rpc.call(
  () => fetch('/api/endpoint', { headers: getAuthHeaders() }).then(r => r.json()),
  { label: 'endpoint', timeout: 15000, retries: 1 }
)

// ❌ 错误：直接传入 Promise
const data = await rpc.call(wsStore.rpc.someMethod(arg), {...})
```

**`options` 参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `label` | `string` | — | 日志标签，必填 |
| `timeout` | `number` | `0` (不禁用) | 超时毫秒数，`0` 表示不限 |
| `retries` | `number` | `0` | 重试次数 |

### Layer 2: `useAsyncModule` — 模块级状态管理

**职责**：封装模块（如 SessionStore）的高频操作，提供统一的 loading / error / data 管理。

**使用场景**：高频使用的聚合数据抽象（如 SessionStore 的会话列表、Token 使用量）。

**标准用法**（参见 `src/stores/session.ts`）：
```ts
// 模块内部使用 rpcSafe 封装高频路径
async function fetchSessions() {
  await asyncModule.call(() => rpc.getSessions({ ... }), {
    label: 'getSessions',
    timeout: 8000,
    retries: 1,
  })
}
```

### Layer 3: `AsyncSection` — UI 加载态展示

**职责**：在 UI 层展示加载骨架屏 / 错误重试，而不是整页阻塞。

**导入**：
```ts
import AsyncSection from '@/components/common/AsyncSection.vue'
```

**标准用法**：
```vue
<!-- ✅ 正确：替换全局 NSpin -->
<AsyncSection :loading="store.loading" error-title="Failed to load data" @retry="store.fetchData()">
  <!-- 内容 -->
</AsyncSection>

<!-- ✅ 正确：多状态组合 -->
<AsyncSection :loading="loading && !data" error-title="Failed to load" @retry="loadData()">
  <div v-if="data">{{ data }}</div>
</AsyncSection>

<!-- ✅ 正确：使用 class 透传 -->
<AsyncSection :loading="loading" class="my-spin-class">
  <NDataTable :data="data" />
</AsyncSection>
```

**`AsyncSection` Props**：
| Prop | 类型 | 说明 |
|------|------|------|
| `loading` | `boolean` | 是否显示骨架屏 |
| `errorTitle` | `string` | 错误状态时显示的标题 |
| `errorDescription` | `string` | 错误状态时显示的描述（可选） |

**`AsyncSection` Events**：
| Event | 说明 |
|--------|------|
| `@retry` | 用户点击重试按钮时触发 |

**`AsyncSection` Slots**：
| Slot | 条件 |
|------|------|
| `default` | 正常内容（loading=false 且无 error） |
| `loading` | 加载中（loading=true） |
| `error` | 发生错误（error 存在） |

---

## 3. 正确用法

### 3.1 页面初始加载

```vue
<template>
  <AsyncSection :loading="store.loading" error-title="Failed to load" @retry="store.fetchData()">
    <NDataTable :data="store.items" />
  </AsyncSection>
</template>

<script setup>
import { useMyStore } from '@/stores/mystore'
import AsyncSection from '@/components/common/AsyncSection.vue'

const store = useMyStore()

onMounted(() => {
  store.fetchData()
})
</script>
```

### 3.2 并行请求（推荐 `Promise.allSettled`）

```ts
// ✅ 正确：任意一个失败不影响其他
await Promise.allSettled([
  storeA.fetchA(),
  storeB.fetchB(),
  storeC.fetchC(),
])

// ❌ 错误：裸 Promise.all，一个失败全部报错
await Promise.all([
  storeA.fetchA(),
  storeB.fetchB(), // 如果这里失败，整个 Promise.all reject
])
```

### 3.3 单个带超时的 fetch

```ts
// ✅ 正确：带 AbortController 超时
const controller = new AbortController()
const timeoutId = setTimeout(() => controller.abort(), 10000)
const response = await fetch(url, { signal: controller.signal })
clearTimeout(timeoutId)

// ✅ 正确：使用 rpcSafe 封装
const data = await rpc.call(
  () => fetch(url).then(r => r.json()),
  { label: 'myFetch', timeout: 10000, retries: 1 }
)
```

### 3.4 定时器清理

```ts
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(fetchMetrics, 5000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
```

---

## 4. 禁止模式

以下模式**明确禁止**新增，发现即修复：

### 4.1 禁止全局 `pageLoading` / 全局 `NSpin` 整页阻塞

```vue
<!-- ❌ 禁止：整页 NSpin 阻塞用户交互 -->
<NSpin :show="pageLoading">
  <AllContent />
</NSpin>

<!-- ✅ 正确：按区域使用 AsyncSection -->
<AsyncSection :loading="sectionLoading">
  <SectionContent />
</AsyncSection>
```

### 4.2 禁止裸 `Promise.all` 无超时

```ts
// ❌ 禁止：一个请求失败全部挂
await Promise.all([
  fetchA(),
  fetchB(),
])
fetchC() // 永远不会执行

// ✅ 正确：Promise.allSettled
const results = await Promise.allSettled([fetchA(), fetchB()])
// 即使 A 失败，B 的结果仍然可用
```

### 4.3 禁止人工 `setTimeout` 等待后端

```ts
// ❌ 禁止：假设后端在 500ms 内响应
await fetchData()
await new Promise(r => setTimeout(r, 500))
// 网络慢时数据还没回来

// ✅ 正确：直接使用，不人为等待
await fetchData()
// 如果需要重试，用 rpc.call 的 retries 参数
```

### 4.4 禁止重复 `fetch` 无去重

```ts
// ❌ 禁止：快速切换时产生竞态
watch(selectedId, () => fetchData()) // 两次快速切换，两个请求

// ✅ 正确：使用 rpcSafe 的自动去重，或在 store 层面处理
watch(selectedId, () => rpc.call(() => store.fetchById(selectedId), {...}))
```

### 4.5 禁止 `timer` 不清理

```ts
// ❌ 禁止：组件销毁后定时器仍在运行
onMounted(() => {
  timer = setInterval(doSomething, 5000)
})

// ✅ 正确：onUnmounted 中清理
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
```

---

## 5. 页面迁移状态清单

| 页面 | 全局 NSpin | 直接 fetch | Promise.all | AsyncSection | 状态 |
|------|-----------|-----------|-------------|-------------|------|
| Dashboard | ✅ 无 | ✅ 无 | ✅ 无 | ✅ 已接入 | **已完成** |
| MonitorPage | ✅ 无 | ✅ 无 | ✅ 无 | ✅ 已接入 | **已完成** |
| OfficePage | ✅ 无 | ✅ 无 | ✅ 无 | ✅ 已接入 | **已完成** |
| SessionStore | ✅ 无 | ✅ 无 | ✅ 无 | N/A | **已完成** |
| ChatPage | ✅ 无 | ✅ 无 | ✅ 无 | ✅ 已接入 | **已完成** |
| ConfigPage | ✅ 已移除 | ✅ 无 | ✅ 无 | ✅ 已接入 | **已完成** |
| SkillsPage | ✅ 已移除 | ✅ 无 | ✅ 无 | ✅ 已接入 | **已完成** |
| NodesPage | ✅ 已移除 | ✅ 无 | ✅ 无 | ✅ 已接入 | **已完成** |
| ChannelsPage | ✅ 已移除 | ✅ 无 | ✅ 无 | ✅ 已接入 | **已完成** |
| SettingsPage | ✅ 已移除 | ✅ 已添加超时 | ✅ 无 | ✅ 已接入 | **已完成** |
| BackupPage | ✅ 已移除 | ⚠️ 部分保留 | ✅ 无 | ✅ 已接入 | **已完成** |
| SystemPage | ✅ 已移除 | ✅ 已添加超时 | ✅ 无 | ✅ 已接入 | **已完成** |
| ToolsPage | ✅ 无（未使用） | ✅ 无 | ✅ 无 | N/A（DataTable 自行处理） | **已完成** |
| CronPage | ✅ 无 | ✅ 无（store 使用 rpc.call） | ✅ 已改为 allSettled | ⚠️ 可选（store 已有加载态） | **已完成** |
| AgentsPage | ✅ 无（未使用） | ✅ 无 | ✅ 已改为 allSettled | ⚠️ 可选（store 已有加载态） | **已完成** |
| ModelsPage | ✅ 无 | ✅ 无 | ✅ 无 | ⚠️ 可选 | **已完成** |
| MemoryPage | ✅ 无 | ✅ 无 | ✅ 无 | ✅ 已接入 | **已完成** |
| SessionDetailPage | ✅ 已移除 | ✅ 无 | ✅ 无 | ✅ 已接入 | **已完成** |
| FilesPage | ✅ 已移除 | ✅ 已迁移到 rpcSafe | ✅ 无 | ✅ 已接入 | **已完成** |
| TerminalPage | ⚠️ 连接状态 | ✅ 无 | ✅ 无 | ⚠️ 不适用（连接生命周期） | **不适用** |
| RemoteDesktopPage | ⚠️ 连接状态 | ✅ 无 | ✅ 无 | ⚠️ 不适用（连接生命周期） | **不适用** |

**说明**：
- "全局 NSpin" 指包裹整个页面内容的 NSpin（初始加载后不消失的那种）
- TerminalPage / RemoteDesktopPage 使用连接状态而非数据加载态，不适合 AsyncSection
- FilesPage 的文件上传操作保留直接 fetch（FormData + NUpload 自带进度）

---

## 6. 新页面接入规范

### Step 1：导入依赖

```ts
import AsyncSection from '@/components/common/AsyncSection.vue'
import { useRpcSafe } from '@/composables/useRpcSafe'
```

### Step 2：初始化

```ts
const store = useMyStore()
const rpc = useRpcSafe()
```

### Step 3：替换全局 NSpin

找到包裹整个页面内容的 `<NSpin :show="loading">`，替换为：

```vue
<AsyncSection :loading="loading" error-title="Failed to load" @retry="store.fetchData()">
  <!-- 所有内容 -->
</AsyncSection>
```

### Step 4：迁移直接 fetch 到 rpcSafe

```ts
// Before
const response = await fetch('/api/data')
const data = await response.json()

// After
const data = await rpc.call(
  () => fetch('/api/data').then(r => r.json()),
  { label: 'getData', timeout: 10000, retries: 1 }
)
```

### Step 5：使用 Promise.allSettled 处理并行请求

```ts
// Before
await Promise.all([storeA.fetch(), storeB.fetch()])

// After
await Promise.allSettled([storeA.fetch(), storeB.fetch()])
```

---

## 7. 常见问题 FAQ

### Q: `rpc.call` 和直接 `fetch` 怎么选？

**`rpc.call`**: WebSocket RPC 调用（`wsStore.rpc.*`），已有超时/重试。  
**`rpcSafe fetch`**: HTTP fetch 调用，传入 `timeout`。  
**直接 `fetch`**: 仅限文件上传（FormData）等无法用 rpcSafe 包装的场景，**必须手动加 AbortController 超时**。

### Q: `Promise.all` 和 `Promise.allSettled` 怎么选？

**`Promise.allSettled`**: 并行发出多个独立请求，希望全部执行完再看结果。  
**`Promise.all`**: 严格要求所有请求成功才继续（很少用到）。  
**结论**：99% 的场景用 `Promise.allSettled`。

### Q: AsyncSection 的 `loading` 状态从哪来？

优先使用 Store 的 `loading` 状态：
```ts
// 优先从 store 取
<AsyncSection :loading="store.loading">

// 如果 store 没有 loading，手动维护
const loading = ref(false)
<AsyncSection :loading="loading">
```

### Q: AsyncSection 包裹内容过多会怎样？

AsyncSection 只在 `loading=true` 时显示骨架屏，不影响内容渲染。放心包裹整个页面主体内容。

### Q: TerminalPage / RemoteDesktopPage 为什么不用 AsyncSection？

这类页面管理持久连接（WebSocket / RDP），连接状态由连接生命周期管理，不适合用 AsyncSection 的"数据加载"模式。

### Q: 文件上传为什么不用 rpcSafe？

文件上传使用 `FormData` + `NUpload` 组件自带进度跟踪，且大文件无法被 `rpc.call` 正确序列化。保留直接 `fetch` 但配合 `NUpload` 的 `onError` 处理。

### Q: 迁移后 TypeScript 报错 `Property 'xxx' does not exist`？

通常是 RPC 返回类型与 HTTP 响应类型不同。检查 `rpc.call` 的实际返回类型，用 `(data as any)` 或类型断言临时解决，或检查 API 类型定义。

---

## 8. Commit Message 规范

### 格式

```
<type>(<scope>): <subject>

[optional body]
```

### Type

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 重构（行为不变） |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `perf` | 性能优化 |

### Scope（本次迁移使用）

| Scope | 说明 |
|-------|------|
| `async` | 异步架构相关（规范文档） |
| `files-page` | FilesPage 迁移 |
| `chat-page` | ChatPage 迁移 |
| `settings-page` | SettingsPage 迁移 |
| `backup-page` | BackupPage 迁移 |
| `system-page` | SystemPage 迁移 |
| `cron-page` | CronPage 迁移 |
| `agents-page` | AgentsPage 迁移 |
| `memory-page` | MemoryPage 迁移 |
| `session-detail-page` | SessionDetailPage 迁移 |
| `channels-page` | ChannelsPage 迁移 |
| `nodes-page` | NodesPage 迁移 |
| `config-page` | ConfigPage 迁移 |
| `skills-page` | SkillsPage 迁移 |
| `tools-page` | ToolsPage 迁移 |
| `models-page` | ModelsPage 迁移 |

### 示例

```bash
# 简单迁移（移除 NSpin + 接入 AsyncSection）
git commit -m "refactor(skills-page): replace NSpin with AsyncSection"

# 迁移 fetch 到 rpcSafe
git commit -m "refactor(files-page): migrate fetch calls to rpcSafe with timeout"

# Promise.allSettled 改造
git commit -m "refactor(cron-page): use Promise.allSettled for parallel fetches"

# 规范文档
git commit -m "docs(async): add ASYNC-MIGRATION-GUIDE with complete rules"

# 修复 TS 错误
git commit -m "fix(settings-page): fix type error in loadConfig RPC call"
```

### 提交粒度

- **按页面提交**：一个页面完成迁移后提交一次
- **不要大坨子**：不要把所有页面一次性提交
- **按主题提交**：多个页面使用同一模式时可用一个 commit

---

## 9. 附录：rpc.call 完整签名

```ts
function call<T = unknown>(
  fn: () => Promise<T>,
  options: {
    label: string
    timeout?: number   // ms，0=不限，默认 0
    retries?: number    // 重试次数，默认 0
  }
): Promise<T>
```

## 10. 附录：AsyncSection 完整 Props

```ts
interface AsyncSectionProps {
  loading: boolean
  errorTitle?: string
  errorDescription?: string
  skeletonLines?: number     // 骨架屏行数，默认 3
  skeletonHeight?: string     // 每行高度，默认 '20px'
}
```
