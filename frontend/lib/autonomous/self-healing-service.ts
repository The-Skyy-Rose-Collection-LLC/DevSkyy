/**
 * Self-Healing Service
 * Automatically detects and recovers from failures
 */

import { getWordPressSyncService } from '@/lib/wordpress/sync-service'
import type { CompetitionResponse } from '@/lib/api/types'

interface HealthCheck {
  service: string
  healthy: boolean
  lastCheck: Date
  consecutiveFailures: number
}

interface CircuitBreaker {
  open: boolean
  failures: number
  lastFailure: Date
}

export class SelfHealingService {
  private healthChecks = new Map<string, HealthCheck>()
  private circuitBreakers = new Map<string, CircuitBreaker>()

  private readonly CIRCUIT_BREAKER_THRESHOLD = 5 // Open circuit after 5 failures
  private readonly CIRCUIT_BREAKER_TIMEOUT = 60000 // 1 minute

  /**
   * Execute operation with circuit breaker protection
   */
  async executeWithCircuitBreaker<T>(
    serviceName: string,
    operation: () => Promise<T>,
    fallback?: () => Promise<T>
  ): Promise<T> {
    const breaker = this.getCircuitBreaker(serviceName)

    // Circuit is open - use fallback or throw
    if (breaker.open) {
      const timeSinceFailure = Date.now() - breaker.lastFailure.getTime()

      if (timeSinceFailure < this.CIRCUIT_BREAKER_TIMEOUT) {
        console.warn(`[CircuitBreaker] ${serviceName} circuit OPEN, using fallback`)

        if (fallback) {
          return fallback()
        }

        throw new Error(`Service ${serviceName} unavailable (circuit breaker open)`)
      }

      // Timeout passed - attempt half-open state
      console.log(`[CircuitBreaker] ${serviceName} attempting recovery (half-open)`)
      breaker.open = false
      breaker.failures = 0
    }

    try {
      const result = await operation()

      // Success - reset failures
      breaker.failures = 0
      this.recordHealthCheck(serviceName, true)

      return result
    } catch (error) {
      breaker.failures++
      breaker.lastFailure = new Date()
      this.recordHealthCheck(serviceName, false)

      // Open circuit if threshold exceeded
      if (breaker.failures >= this.CIRCUIT_BREAKER_THRESHOLD) {
        breaker.open = true
        console.error(
          `[CircuitBreaker] ${serviceName} circuit OPENED after ${breaker.failures} failures`
        )
      }

      // Attempt fallback
      if (fallback) {
        console.warn(`[CircuitBreaker] Using fallback for ${serviceName}`)
        return fallback()
      }

      throw error
    }
  }

  /**
   * Auto-retry with exponential backoff and jitter
   */
  async retryWithBackoff<T>(
    operation: () => Promise<T>,
    options: {
      maxRetries?: number
      initialDelay?: number
      maxDelay?: number
      jitter?: boolean
    } = {}
  ): Promise<T> {
    const {
      maxRetries = 5,
      initialDelay = 1000,
      maxDelay = 30000,
      jitter = true
    } = options

    let lastError: Error | undefined

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error as Error

        if (attempt === maxRetries) {
          break
        }

        // Calculate exponential backoff with optional jitter
        let delay = Math.min(initialDelay * Math.pow(2, attempt - 1), maxDelay)

        if (jitter) {
          // Add random jitter (±20%)
          delay = delay * (0.8 + Math.random() * 0.4)
        }

        console.warn(
          `[Retry] Attempt ${attempt}/${maxRetries} failed, retrying in ${Math.round(delay)}ms...`
        )

        await this.sleep(delay)
      }
    }

    throw new Error(
      `Operation failed after ${maxRetries} attempts: ${lastError?.message}`
    )
  }

  /**
   * Self-healing WordPress connection
   */
  async healWordPressConnection(): Promise<boolean> {
    try {
      const syncService = getWordPressSyncService()
      if (!syncService) return false

      const testResult = await syncService.testConnection()

      if (testResult.success) {
        console.log('[SelfHealing] WordPress connection restored')
        return true
      }

      // Attempt reconnection with credential refresh
      console.warn('[SelfHealing] WordPress connection failed, attempting refresh...')

      // TODO: Implement credential refresh logic if applicable

      return false
    } catch (error) {
      console.error('[SelfHealing] WordPress healing failed:', error)
      return false
    }
  }

  /**
   * Fallback LLM provider if winner fails
   */
  async getFallbackWinner(roundTableResult: CompetitionResponse): Promise<{
    provider: string
    response: string
    score: number
  } | null> {
    // Get runner-up (second place)
    const sortedEntries = roundTableResult.entries
      .filter(e => e.provider !== roundTableResult.winner?.provider)
      .sort((a, b) => b.scores.total - a.scores.total)

    if (sortedEntries.length === 0) return null

    const runnerUp = sortedEntries[0]

    console.log(
      `[Fallback] Using runner-up ${runnerUp.provider} (score: ${runnerUp.scores.total})`
    )

    return {
      provider: runnerUp.provider,
      response: runnerUp.response_preview,
      score: runnerUp.scores.total
    }
  }

  private getCircuitBreaker(serviceName: string): CircuitBreaker {
    if (!this.circuitBreakers.has(serviceName)) {
      this.circuitBreakers.set(serviceName, {
        open: false,
        failures: 0,
        lastFailure: new Date()
      })
    }
    return this.circuitBreakers.get(serviceName)!
  }

  private recordHealthCheck(serviceName: string, healthy: boolean): void {
    const existing = this.healthChecks.get(serviceName)

    this.healthChecks.set(serviceName, {
      service: serviceName,
      healthy,
      lastCheck: new Date(),
      consecutiveFailures: healthy ? 0 : (existing?.consecutiveFailures ?? 0) + 1
    })
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * Get health status of all services
   */
  getHealthStatus(): HealthCheck[] {
    return Array.from(this.healthChecks.values())
  }

  /**
   * Get circuit breaker status
   */
  getCircuitBreakerStatus(): Array<{
    service: string
    open: boolean
    failures: number
  }> {
    return Array.from(this.circuitBreakers.entries()).map(([service, breaker]) => ({
      service,
      open: breaker.open,
      failures: breaker.failures
    }))
  }
}

export const selfHealingService = new SelfHealingService()
