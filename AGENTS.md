# OpenClaw Admin - AI Agent Management Platform

> This document is intended for AI coding agents working on the OpenClaw Admin project.
> Language: Chinese (zh-CN) - matching the primary project language.

## 1. 项目概览 (Project Overview)

OpenClaw Admin 是一个基于 Vue 3 构建的现代化 AI 智能体管理平台，为 OpenClaw Gateway 提供完整的 Web 管理界面。通过直观的可视化操作，用户可以轻松管理 AI 智能体、会话、模型、频道、技能等核心功能。

### 版本兼容性

| OpenClaw Admin | OpenClaw Gateway | 状态    |
| -------------- | ---------------- | ----- |
| 0.2.6          | 2026.4.5         | ✅ 已验证 |

### 核心功能模块

- **仪表盘**：运行总览、Token 使用趋势、会话活跃度统计
- **在线对话**：实时聊天、斜杠命令支持、Token 使用量统计
- **会话管理**：会话列表、详情查看、重置、删除、消息导出
- **记忆管理**：智能体文档管理（AGENTS/SOUL/IDENTITY/USER）
- **任务计划**：Cron 表达式、固定间隔、指定时间的定时任务
- **模型管理**：多模型渠道配置、API Key 安全管理、模型探测
- **频道管理**：QQ、飞书、钉钉、企业微信渠道配置
- **技能管理**：技能插件列表、内置/用户技能分类、安装更新
- **多智能体**：智能体创建、身份配置、工具权限、工作区文件
- **智能体工坊**：多智能体协作空间、场景创建、任务委派
- **虚拟公司**：可视化办公场景、角色交互
- **远程终端**：SSE 协议远程终端、多节点支持
- **远程桌面**：Linux/Windows 远程桌面、实时画面传输
- **文件浏览器**：工作区文件浏览、编辑、上传下载
- **系统监控**：CPU、内存、磁盘、网络监控
- **系统设置**：连接配置、外观主题、环境变量

## 2. 技术栈 (Technology Stack)

### 前端技术栈

| 技术         | 版本    | 说明                  |
| ---------- | ----- | ------------------- |
| Vue        | 3.5.x | 渐进式 JavaScript 框架   |
| Vue Router | 4.x   | 官方路由管理器             |
| Pinia      | 3.x   | 状态管理库               |
| TypeScript | 5.x   | 类型安全的 JavaScript 超集 |
| Vite       | 7.x   | 下一代前端构建工具           |
| Naive UI   | 2.43.x| Vue 3 组件库            |
| vue-i18n   | 9.x   | 国际化支持               |

### 后端技术栈

| 技术             | 版本   | 说明             |
| -------------- | ---- | -------------- |
| Node.js        | >=18 | JavaScript 运行时 |
| Express        | 5.x  | Node.js Web 框架 |
| ws             | 8.x  | WebSocket 实现   |
| better-sqlite3 | 12.x | SQLite 数据库     |
| node-pty       | 1.x  | 伪终端支持          |
| ssh2           | 1.x  | SSH 客户端        |

### 构建与开发工具

- **Vite**: 前端构建工具
- **vue-tsc**: TypeScript 类型检查
- **Vitest**: 单元测试框架
- **Playwright**: E2E 测试框架
- **concurrently**: 同时运行多个命令

## 3. 项目结构 (Project Structure)

```
openclaw-admin/
├── src/                          # 前端源码
│   ├── api/                      # API 层
│   │   ├── types/                # TypeScript 类型定义
│   │   │   ├── index.ts          # 类型导出
│   │   │   ├── rpc.ts            # RPC 相关类型
│   │   │   ├── session.ts        # 会话类型
│   │   │   ├── channel.ts        # 频道类型
│   │   │   ├── config.ts         # 配置类型
│   │   │   ├── terminal.ts       # 终端类型
│   │   │   ├── remote-desktop.ts # 远程桌面类型
│   │   │   └── backup.ts         # 备份类型
│   │   ├── connect.ts            # 连接管理
│   │   ├── rpc-client.ts         # RPC 客户端封装
│   │   ├── websocket.ts          # WebSocket 封装
│   │   └── http-client.ts        # HTTP 客户端
│   │
│   ├── assets/                   # 静态资源
│   │   └── styles/
│   │       └── main.css          # 全局样式、CSS 变量
│   │
│   ├── components/               # 组件
│   │   ├── common/               # 通用组件
│   │   │   ├── AsyncSection.vue
│   │   │   ├── ConnectionStatus.vue
│   │   │   ├── EmptyState.vue
│   │   │   ├── StatCard.vue
│   │   │   └── ...
│   │   ├── layout/               # 布局组件
│   │   │   ├── AppHeader.vue
│   │   │   └── AppSidebar.vue
│   │   └── office/               # 办公场景组件
│   │       ├── AgentCharacter.vue
│   │       ├── OfficeScene3D.vue
│   │       └── ...
│   │
│   ├── composables/              # 组合式函数
│   │   ├── useAsyncModule.ts     # 异步模块状态管理
│   │   ├── useEventStream.ts     # SSE 事件流
│   │   ├── useResizable.ts       # 尺寸调整
│   │   ├── useRpcSafe.ts         # RPC 安全调用
│   │   └── useTheme.ts           # 主题管理
│   │
│   ├── i18n/                     # 国际化
│   │   ├── messages/
│   │   │   ├── zh-CN.ts          # 中文
│   │   │   └── en-US.ts          # 英文
│   │   └── index.ts
│   │
│   ├── layouts/                  # 布局
│   │   └── DefaultLayout.vue
│   │
│   ├── router/                   # 路由
│   │   ├── index.ts              # 路由守卫与初始化
│   │   └── routes.ts             # 路由定义
│   │
│   ├── stores/                   # Pinia 状态管理
│   │   ├── agent.ts              # 智能体管理
│   │   ├── auth.ts               # 认证状态
│   │   ├── backup.ts             # 备份管理
│   │   ├── channel.ts            # 频道状态
│   │   ├── channel-management.ts # 频道配置管理
│   │   ├── chat.ts               # 聊天状态
│   │   ├── config.ts             # 系统配置
│   │   ├── cron.ts               # 定时任务
│   │   ├── locale.ts             # 语言设置
│   │   ├── memory.ts             # 记忆管理
│   │   ├── model.ts              # 模型管理
│   │   ├── monitor.ts            # 运维监控
│   │   ├── node.ts               # 节点管理
│   │   ├── office.ts             # 智能体工坊
│   │   ├── remote-desktop.ts     # 远程桌面
│   │   ├── session.ts            # 会话管理
│   │   ├── skill.ts              # 技能管理
│   │   ├── terminal.ts           # 终端管理
│   │   ├── theme.ts              # 主题设置
│   │   ├── websocket.ts          # WebSocket 连接状态
│   │   ├── wideMode.ts           # 宽屏模式
│   │   └── wizard.ts             # 场景向导
│   │
│   ├── utils/                    # 工具函数
│   │   ├── channel-config.ts     # 频道配置处理
│   │   ├── format.ts             # 格式化工具
│   │   ├── markdown.ts           # Markdown 处理
│   │   └── secret-mask.ts        # 凭证脱敏
│   │
│   ├── views/                    # 页面视图
│   │   ├── agents/               # 多智能体管理
│   │   ├── backup/               # 备份恢复
│   │   ├── channels/             # 频道管理
│   │   ├── chat/                 # 在线对话
│   │   ├── config/               # 配置页面
│   │   ├── cron/                 # 任务计划
│   │   ├── files/                # 文件浏览器
│   │   ├── memory/               # 记忆管理
│   │   ├── model-quota/          # 模型配额监控
│   │   ├── models/               # 模型管理
│   │   ├── monitor/              # 运维中心
│   │   ├── myworld/              # 虚拟公司
│   │   ├── nodes/                # 节点管理
│   │   ├── office/               # 智能体工坊
│   │   ├── remote-desktop/       # 远程桌面
│   │   ├── sessions/             # 会话管理
│   │   ├── settings/             # 系统设置
│   │   ├── skills/               # 技能管理
│   │   ├── system/               # 系统监控
│   │   ├── terminal/             # 远程终端
│   │   ├── tools/                # 工具管理
│   │   ├── Dashboard.vue         # 仪表盘
│   │   └── Login.vue             # 登录页
│   │
│   ├── App.vue                   # 根组件
│   ├── main.ts                   # 入口文件
│   └── env.d.ts                  # 环境类型声明
│
├── server/                       # 后端服务
│   ├── index.js                  # 服务入口（Express 应用）
│   ├── gateway.js                # Gateway WebSocket 连接
│   └── database.js               # SQLite 数据库操作
│
├── data/                         # 数据存储
│   └── wizard.db                 # SQLite 数据库文件
│
├── dist/                         # 构建输出目录
├── public/                       # 公共静态资源
├── docs/                         # 项目文档
│   ├── TECH_ARCHITECTURE.md      # 技术架构文档
│   ├── async-architecture.md     # 异步架构规范
│   └── ASYNC-MIGRATION-GUIDE.md  # 异步架构迁移指南
│
├── .env                          # 本地环境变量
├── .env.example                  # 环境变量示例
├── vite.config.ts                # Vite 配置
├── tsconfig.json                 # TypeScript 配置
├── tsconfig.app.json             # 应用 TypeScript 配置
├── tsconfig.node.json            # Node 端 TypeScript 配置
└── package.json                  # 项目配置
```

## 4. 构建、测试与开发命令

### 环境要求

- Node.js >= 18.0.0
- npm >= 9.0.0

### 安装依赖

```bash
npm install
```

### 初始化环境变量

```bash
cp .env.example .env
```

### 开发模式

**启动前端开发服务器：**
```bash
npm run dev
# 默认端口: 3001
# 访问: http://localhost:3001
```

**启动后端服务：**
```bash
npm run dev:server
# 默认端口: 3000
```

**同时启动前后端：**
```bash
npm run dev:all
# 使用 concurrently 同时启动前端和后端
```

### 生产构建

```bash
npm run build
# 执行 vue-tsc 类型检查 + vite build
# 输出到 dist/ 目录
```

### 预览构建结果

```bash
npm run preview
# 本地预览生产构建
```

### 生产启动

```bash
npm start
# 或
node --env-file=.env server/index.js
```

## 5. 代码风格与命名规范

### Vue 3 风格

- 使用 **Vue 3 Composition API** + `<script setup lang="ts">`
- 优先使用组合式函数（composables）封装可复用逻辑

### 代码格式

- **缩进**: 2 空格
- **引号**: 单引号
- **尾随逗号**: 使用
- **分号**: 不使用
- **最大行宽**: 建议 100-120 字符

### 导入规范

- `src` 路径优先使用 `@/` 别名导入
- 示例: `import { useAuthStore } from '@/stores/auth'`

### 命名约定

| 类型         | 命名规范           | 示例                     |
| ---------- | -------------- | ---------------------- |
| 组件         | PascalCase.vue | `ConnectionStatus.vue` |
| 路由页面       | \*Page.vue     | `SessionsPage.vue`     |
| Store      | camelCase.ts   | `session.ts`           |
| Composable | use\*.ts       | `useTheme.ts`          |
| 类型定义       | PascalCase     | `interface UserConfig` |
| 工具函数       | camelCase      | `formatDate()`         |

### CSS 变量使用

全局样式变量定义在 `src/assets/styles/main.css`：

```css
/* 亮色主题 */
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f7fa;
  --bg-card: #ffffff;
  --text-primary: #1a1a2e;
  --text-secondary: #64748b;
  --border-color: #e2e8f0;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07);
}

/* 暗色主题 */
[data-theme='dark'] {
  --bg-primary: #101014;
  --bg-secondary: #18181c;
  --bg-card: #1e1e22;
  --text-primary: #ffffffde;
  --text-secondary: #a0a0b0;
  --border-color: #2c2c32;
}
```

**重要**: 样式优先复用全局变量，避免硬编码颜色。

## 6. 测试要求

### 当前测试状态

- 已配置 Vitest 和 Playwright 依赖
- 但尚未配置完整的自动化测试套件

### 合并前检查清单

必须确保以下步骤通过：

1. **类型检查与构建：**
   ```bash
   npm run build
   ```
   必须无类型错误和构建错误。

2. **手工冒烟测试：**
   - 登录功能
   - WebSocket 连接
   - 相关页面的基本功能
   - 连接可用的 Gateway（`ws://127.0.0.1:18789`）

### 后续测试计划

对于非简单逻辑改动，请在 PR 中附测试计划：

- 测试步骤
- 预期结果
- 影响范围
- 回归点

后续迭代优先补充：

- Store 层单元测试（Vitest）
- 关键组件测试
- 路由级 smoke test
- 关键 API 的后端集成测试

## 7. 安全与配置

### 敏感信息处理

- ⚠️ **禁止提交**真实的 Gateway Token、凭证或其他敏感信息到代码仓库
- 凭证字段采用掩码显示，不回显明文
- API Key 仅在输入新值时提交，未输入则保持原值

### 环境变量

运行时配置放在 `.env` 文件中，关键变量：

```env
# 应用配置
VITE_APP_TITLE=OpenClaw-Admin

# Gateway 连接
OPENCLAW_WS_URL=ws://localhost:18789
OPENCLAW_AUTH_TOKEN=           # Gateway Token
OPENCLAW_AUTH_PASSWORD=        # Gateway 密码（与 Token 二选一）

# 服务端口
PORT=3000                      # 后端端口
DEV_PORT=3001                  # 前端开发端口

# 认证配置
AUTH_USERNAME=admin            # 管理后台用户名
AUTH_PASSWORD=admin            # 管理后台密码

# 日志级别
LOG_LEVEL=INFO                 # DEBUG/INFO/WARN/ERROR

# 可选配置
# OPENCLAW_HOME=/path/to/.openclaw
# MEDIA_DIR=/path/to/media
```

### 新增环境变量

新增 `VITE_` 前缀变量需同步记录到 `README.md`。

## 8. 架构说明

### 前后端通信架构

```
浏览器 (Vue 3 SPA)
    ↓ HTTP / SSE / WebSocket
Express Backend (server/index.js)
    ├─ 本地文件系统访问
    ├─ SQLite (better-sqlite3)
    ├─ PTY / SSH / 终端 / 远程桌面
    └─ WebSocket Client (server/gateway.js)
          ↓ WebSocket RPC
    OpenClaw Gateway
```

**重要事实：**

- 前端**不直接连接** OpenClaw Gateway
- 前端先连接本项目后端，后端再作为 Gateway 的 operator 客户端
- 后端同时承担：静态资源服务、认证、文件读写、终端/桌面流服务、Gateway RPC 代理层
- 本地 SQLite 仅承载 Admin 自己的业务数据（scenarios、tasks、backup_records、quota_keys）

### 前端状态管理

采用 **Pinia store** 为主状态中心，典型数据流：

```
View (Vue Component)
  ↓
Store (Pinia)
  ↓
API Layer (api/websocket.ts, rpc-client.ts, http-client.ts)
  ↓
Backend API / SSE / Gateway proxy
```

### 异步架构规范

项目已有异步架构规范，核心约定：

- 通过 `useRpcSafe` 包装 RPC 调用
- 通过 `useAsyncModule` 管理异步状态
- 通过 `AsyncSection` 统一 loading/error/empty UI
- 倡导并发加载而非整页阻塞

详见：`docs/async-architecture.md`

## 9. 提交与 PR 规范

### 提交信息

建议使用 Conventional Commit 前缀：

- `feat:` - 新功能
- `fix:` - 修复
- `refactor:` - 重构
- `docs:` - 文档
- `chore:` - 杂项
- `test:` - 测试
- `style:` - 代码格式

**要求：**

- 每个提交只关注一个主题
- 避免占位式提交信息（如 "update"、"fix"）
- 提交信息使用中文或英文，保持一致

### PR 要求

PR 需包含：

1. **目标**：本次改动的目的
2. **关键改动**：主要修改内容
3. **关联任务/Issue**：如有
4. **验证步骤**：如何测试
5. **UI 改动**：截图/GIF（如有）

## 10. 开发守则 (Codex Constitution)

### 核心原则

1. **事实优先**
   - 先读现状再改代码
   - 不得基于猜测修改 RPC、类型或页面行为
   - 查看现有代码实现后再做改动

2. **单一来源**
   - 同一能力只保留一个权威入口与实现
   - 避免页面与 store 双重定义

3. **兼容优先**
   - 优先适配现有 Gateway RPC 形态
   - 不引入未经验证的新协议分支

4. **渐进改造**
   - 先打通最小闭环（可用）
   - 再做视觉与体验增强
   - 避免一次性过度重构

5. **安全默认**
   - 凭证永不明文回显
   - 未输入新值不得提交凭证 patch

6. **主题一致**
   - 样式优先复用全局变量（`--bg-*`、`--text-*`、`--border-color`）
   - 避免硬编码颜色

7. **渲染边界清晰**
   - 凡是 `v-html` 注入内容，若页面使用 `<style scoped>`，必须使用 `:deep(...)` 覆盖其内部元素
   - 禁止误以为 scoped 选择器可直接命中运行时注入节点

8. **可验证**
   - 每次改动后至少保证可构建
   - 说明影响面与回归点

## 11. 实施教训与最佳实践

### UI 开发

- **组件默认样式有"首项特例"**：如 `Collapse` 的 first-child 规则，改间距前必须先核对组件源码
- **间距系统必须"单机制"管理**：统一使用 gap 或 margin，混用会造成首行/后续行视觉不一致
- **暗色适配不能只改颜色值**：应以主题变量驱动并限制选择器作用域，避免污染其他页面
- **Spacing 问题排查**：通常同时涉及 `margin/padding/border` 叠加，需要逐层排查
- **UI 微调顺序**：先保证信息架构不变，再收敛 spacing 与密度，避免视觉改善引发交互回归

### RPC 调用

- 使用 `useRpcSafe` composable 进行安全调用
- 处理超时、重试、错误边界
- 关注 Gateway 连接状态变化

### 状态管理

- Store 应聚焦领域状态，避免与具体页面结构过度耦合
- 跨页面共享状态放 Store，页面私有状态用 composables 或组件内部
- 异步状态使用 `useAsyncModule` 统一管理

## 12. 常见问题与故障排查

### 构建失败

1. **类型错误**：运行 `vue-tsc -b` 查看详细错误
2. **依赖缺失**：检查 `node_modules`，必要时删除重装
3. **内存不足**：Node.js 堆内存不足时增加 `--max-old-space-size`

### 连接问题

1. **Gateway 连接失败**：
   - 检查 `.env` 中的 `OPENCLAW_WS_URL`
   - 确认 Gateway 服务已启动
   - 检查 Token 或密码是否正确

2. **WebSocket 断开**：
   - 查看浏览器控制台网络面板
   - 检查后端日志
   - 确认 Gateway 版本兼容性

### 路由与页面

1. **404 页面**：检查路由定义是否在 `src/router/routes.ts` 中
2. **动态加载失败**：检查网络面板，确认 chunk 文件可访问

## 13. 相关文档

- `README.md` - 项目功能说明与使用介绍
- `README.en.md` - 英文版 README
- `docs/TECH_ARCHITECTURE.md` - 详细技术架构文档
- `docs/async-architecture.md` - 前端异步架构规范
- `docs/ASYNC-MIGRATION-GUIDE.md` - 异步架构迁移指南

## 14. 版本历史

- **v0.2.6** - 当前版本，兼容 OpenClaw Gateway 2026.4.5

---

> 本文档随代码演进持续更新。如有疑问，请参考代码实现或联系维护者。
