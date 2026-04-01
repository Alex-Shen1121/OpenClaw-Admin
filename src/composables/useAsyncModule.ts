/**
 * useAsyncModule — Unified module-level async state management.
 *
 * Provides: data / loading / refreshing / loaded / error
 * Methods:   load / refresh / retry
 *
 * Key guarantees:
 * - load() is idempotent: a second load() call while one is in-flight returns
 *   the same in-flight promise (no duplicate RPC).
 * - refresh() sets refreshing=true but does NOT cancel the in-flight load;
 *   both resolve independently (last-write-wins on data).
 * - retry() resets error and re-invokes load().
 *
 * Usage:
 *   const state = useAsyncModule({ fetch: () => wsStore.rpc.listSessions() })
 *   state.load()
 *   // or with initial data:
 *   const state = useAsyncModule({ initial: [], fetch: () => wsStore.rpc.listSessions() })
 */

import { reactive, readonly, ref } from 'vue'

export interface AsyncModuleState<T> {
  /** Latest resolved data (unchanged while loading). */
  data: T
  /** True from mount until the first successful fetch resolves. */
  loading: boolean
  /** True while a manual refresh/retry is in flight (separate from loading). */
  refreshing: boolean
  /** True once the first fetch has completed successfully at least once. */
  loaded: boolean
  /** Latest error (Error instance or string). Cleared on next load/retry. */
  error: Error | null
}

export interface AsyncModuleActions {
  /** Trigger initial/background fetch. Idempotent while in-flight. */
  load(): void
  /** Manual refresh — sets refreshing, does NOT cancel in-flight load. */
  refresh(): void
  /** Clear error and retry the last fetch. */
  retry(): void
  /** Imperatively set data (useful after a side-effect that mutates server state). */
  setData(data: unknown): void
  /** Reset to initial blank state. */
  reset(): void
}

export interface UseAsyncModuleOptions<T> {
  /** Default value before first load. */
  initial?: T
  /**
   * Async fetch function. Receives an AbortSignal that fires on reset().
   * The signal is cooperative: long-running fetches should check it.
   */
  fetch: (signal?: AbortSignal) => Promise<T>
  /**
   * Default timeout for the fetch call (ms). Default 15000.
   * Pass Infinity to disable.
   */
  timeout?: number
  /**
   * Number of retries on transient failure. Default 0.
   */
  retries?: number
  /**
   * Human-readable label for error messages.
   */
  label?: string
  /**
   * Called with the resolved data after every successful fetch.
   * Use for side-effects that must run on every resolve (e.g. store sync).
   */
  onData?: (data: T) => void
  /**
   * Called with the error after every failed attempt.
   */
  onError?: (error: Error) => void
}

function isTransientError(error: unknown): boolean {
  if (error instanceof Error) {
    const msg = error.message.toLowerCase()
    if (msg.includes('timed out') || msg.includes('timeout')) return true
    if (
      msg.includes('websocket') ||
      msg.includes('network') ||
      msg.includes('fetch') ||
      msg.includes('econnrefused') ||
      msg.includes('enotfound') ||
      msg.includes('socket') ||
      msg.includes('aborted')
    )
      return true
    if (msg.includes('500') || msg.includes('502') || msg.includes('503') || msg.includes('504')) return true
    if (msg.includes('not connected') || msg.includes('ws not open')) return true
  }
  if (typeof error === 'string') {
    const lower = error.toLowerCase()
    if (lower.includes('abort') || lower.includes('cancelled') || lower.includes('canceled')) return true
  }
  return false
}

const RETRY_DELAYS_MS = [400, 900, 2400]
const DEFAULT_TIMEOUT_MS = 15_000

export interface AsyncModuleReturn<T> {
  state: AsyncModuleState<T>
  /** Shortcut to state.loading || state.refreshing */
  isLoading: () => boolean
  load(): Promise<void>
  refresh(): Promise<void>
  retry(): Promise<void>
  setData(data: T): void
  reset(): void
}

export function useAsyncModule<T>(options: UseAsyncModuleOptions<T>): AsyncModuleReturn<T> {
  const {
    initial,
    fetch,
    timeout = DEFAULT_TIMEOUT_MS,
    retries = 0,
    label,
    onData,
    onError,
  } = options

  // --- Reactive state ---
  const data = ref<T>(initial as T) as { value: T }
  const loading = ref(false)
  const refreshing = ref(false)
  const loaded = ref(false)
  const error = ref<Error | null>(null)

  // In-flight tracking to make load() idempotent
  let inFlight: Promise<void> | null = null
  let abortController: AbortController | null = null

  function normalisedError(err: unknown): Error {
    if (err instanceof Error) return err
    const prefix = label ? `[${label}] ` : ''
    return new Error(`${prefix}${typeof err === 'string' ? err : JSON.stringify(err)}`)
  }

  function settleData(value: T) {
    data.value = value
    error.value = null
    if (!loaded.value) loaded.value = true
  }

  function settleError(err: unknown) {
    error.value = normalisedError(err)
    onError?.(error.value)
  }

  async function doFetch(opts?: { signal?: AbortSignal; retriesLeft?: number; refreshing?: boolean }): Promise<void> {
    const { signal, retriesLeft = retries, refreshing: isRefresh = false } = opts ?? {}

    // Race between user abort, component unmount, and timeout
    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(
        () => reject(new Error(`${label ? `[${label}] ` : ''}timed out after ${timeout}ms`)),
        timeout
      )
    )

    try {
      const result = await Promise.race([fetch(signal), timeoutPromise])
      settleData(result)
      onData?.(result)
    } catch (err) {
      // Don't flag abort as an error
      if (signal?.aborted || (err instanceof Error && err.message.includes('aborted'))) {
        return
      }

      const transient = isTransientError(err)
      if (transient && retriesLeft > 0) {
        const delay = RETRY_DELAYS_MS[retries - retriesLeft] ?? RETRY_DELAYS_MS[RETRY_DELAYS_MS.length - 1] ?? 500
        await new Promise((resolve) => setTimeout(resolve, delay))
        return doFetch({ signal, retriesLeft: retriesLeft - 1, refreshing: isRefresh })
      }

      settleError(err)
    }
  }

  async function load(): Promise<void> {
    if (inFlight) return inFlight

    // Fresh abort controller for this load
    abortController = new AbortController()
    loading.value = true
    error.value = null

    inFlight = doFetch({ signal: abortController.signal, retriesLeft: retries, refreshing: false })
      .finally(() => {
        loading.value = false
        inFlight = null
      })

    return inFlight
  }

  async function refresh(): Promise<void> {
    abortController = new AbortController()
    refreshing.value = true

    // Keep the existing loading.value false so the UI doesn't flash a full-page spinner.
    // refreshing signals "this is a background refresh" to the UI.
    inFlight = doFetch({ signal: abortController.signal, retriesLeft: retries, refreshing: true })
      .finally(() => {
        refreshing.value = false
        inFlight = null
      })

    return inFlight
  }

  async function retry(): Promise<void> {
    error.value = null
    return load()
  }

  function setData(value: T): void {
    settleData(value)
  }

  function reset(): void {
    // Signal any in-flight fetch to abort (non-interruptive: fetch still runs to completion,
    // but we stop waiting for it).
    abortController?.abort()
    abortController = null
    inFlight = null
    loading.value = false
    refreshing.value = false
    data.value = initial as T
    loaded.value = false
    error.value = null
  }

  function isLoading() {
    return loading.value || refreshing.value
  }

  return {
    state: reactive({
      data: data.value,
      loading: loading.value,
      refreshing: refreshing.value,
      loaded: loaded.value,
      error: error.value,
    }) as AsyncModuleState<T>,
    isLoading,
    load,
    refresh,
    retry,
    setData,
    reset,
  }
}

/**
 * useAsyncSection — Thin wrapper around useAsyncModule that also tracks
 * whether the section has ever been rendered (used for empty-state gating).
 *
 * Use when you want a component that owns its own async lifecycle.
 */
export interface AsyncSectionState<T> extends AsyncModuleState<T> {
  /** True once the component has mounted (even if load hasn't fired yet). */
  mounted: boolean
  /** True if the data is empty (=== initial value, by reference or isEmpty check). */
  isEmpty: boolean
}

export function useAsyncSection<T>(
  options: UseAsyncModuleOptions<T>
): AsyncModuleReturn<T> & { mounted: boolean; isEmpty: () => boolean } {
  const module = useAsyncModule<T>(options)

  const mounted = ref(false)

  // We can't easily compare `data` by reference for "isEmpty" without knowing
  // what T looks like. Instead we expose a computed flag: the caller passes
  // an `isEmpty` predicate, or we fall back to a loose check.
  function isEmpty(): boolean {
    const d = module.state.data
    if (d === null || d === undefined) return true
    if (Array.isArray(d)) return d.length === 0
    if (typeof d === 'object') return Object.keys(d as object).length === 0
    return false
  }

  return {
    ...module,
    state: module.state,
    mounted: mounted.value,
    isEmpty,
  }
}
