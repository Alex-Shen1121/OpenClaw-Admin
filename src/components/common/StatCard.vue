<script setup lang="ts">
import { NCard, NIcon, NSkeleton } from 'naive-ui'

defineProps<{
  title: string
  value: number | string
  icon: unknown
  color?: string
  loading?: boolean
}>()
</script>

<template>
  <NCard :bordered="true" style="border-radius: var(--radius-lg);">
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
      <div>
        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">{{ title }}</div>
        <div style="font-size: 24px; font-weight: 600; line-height: 1.25;">
          <template v-if="loading">
            <NSkeleton text :width="60" :height="28" style="display: inline-block;" />
          </template>
          <template v-else>
            {{ value }}
          </template>
        </div>
      </div>
      <div
        style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;"
        :style="{ backgroundColor: (color || '#18a058') + '15', color: color || '#18a058' }"
      >
        <NIcon :size="22" :component="icon as any" />
      </div>
    </div>
  </NCard>
</template>
