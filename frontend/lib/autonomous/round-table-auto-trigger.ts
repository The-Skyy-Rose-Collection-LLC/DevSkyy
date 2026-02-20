/**
 * Autonomous Round Table Auto-Trigger System
 * Triggers Round Table competition on ANY task, deploys winner to WordPress
 */

import { api } from '@/lib/api'
import { getWordPressSyncService } from '@/lib/wordpress/sync-service'
import type { CompetitionResponse } from '@/lib/api/types'

interface TaskRequest {
  prompt: string
  task_type: 'content_generation' | 'scene_building' | 'product_update' | 'general'
  metadata?: Record<string, any>
}

interface TaskResult {
  success: boolean
  roundTableResult?: CompetitionResponse
  wordpressPostId?: number
  error?: string
  usedFallback?: boolean
}

export class RoundTableAutoTrigger {
  private maxRetries = 3
  private retryDelay = 2000 // 2 seconds

  /**
   * MAIN PIPELINE: Task → Round Table Competition → Winner Deploy
   */
  async processTask(task: TaskRequest): Promise<TaskResult> {
    console.log('[RoundTable] Auto-trigger for task:', task.prompt.substring(0, 50))

    try {
      // Step 1: Trigger Round Table competition (with retries)
      const roundTableResult = await this.triggerCompetitionWithRetry(task.prompt)

      if (!roundTableResult || !roundTableResult.winner) {
        throw new Error('Round Table competition failed - no winner')
      }

      console.log('[RoundTable] Winner:', roundTableResult.winner.provider)

      // Step 2: Deploy winner to WordPress (with retries)
      const postId = await this.deployWinnerToWordPressWithRetry(roundTableResult)

      console.log('[RoundTable] Winner deployed to WordPress:', postId)

      return {
        success: true,
        roundTableResult,
        wordpressPostId: postId,
      }
    } catch (error) {
      console.error('[RoundTable] Pipeline failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  }

  /**
   * Trigger Round Table competition with exponential backoff retry
   */
  private async triggerCompetitionWithRetry(
    prompt: string,
    attempt = 1
  ): Promise<CompetitionResponse> {
    try {
      const result = await api.roundTable.compete({ prompt })
      return result
    } catch (error) {
      if (attempt >= this.maxRetries) {
        throw new Error(`Round Table failed after ${this.maxRetries} attempts: ${error}`)
      }

      const delay = this.retryDelay * Math.pow(2, attempt - 1) // Exponential backoff
      console.warn(`[RoundTable] Attempt ${attempt} failed, retrying in ${delay}ms...`)
      await this.sleep(delay)

      return this.triggerCompetitionWithRetry(prompt, attempt + 1)
    }
  }

  /**
   * Deploy winner to WordPress with retry logic
   */
  private async deployWinnerToWordPressWithRetry(
    result: CompetitionResponse,
    attempt = 1
  ): Promise<number> {
    try {
      const syncService = getWordPressSyncService()
      if (!syncService) {
        throw new Error('WordPress not configured')
      }

      // CRITICAL: Deploy as PUBLISHED post (not draft)
      const response = await syncService.syncRoundTableResult(result, {
        status: 'publish', // Auto-publish winner
        title: `LLM Round Table Winner: ${result.prompt_preview.substring(0, 60)}`,
      })

      if (!response.success || !response.postId) {
        throw new Error(response.error || 'WordPress deployment failed')
      }

      // Record sync in history
      this.recordSync(result.id, response.postId)
      this.notifySuccess(result.id, response.postId)

      return response.postId
    } catch (error) {
      if (attempt >= this.maxRetries) {
        this.notifyError(result.id, error instanceof Error ? error.message : 'Unknown error')
        throw new Error(`WordPress deployment failed after ${this.maxRetries} attempts: ${error}`)
      }

      const delay = this.retryDelay * Math.pow(2, attempt - 1)
      console.warn(`[WordPress] Attempt ${attempt} failed, retrying in ${delay}ms...`)
      await this.sleep(delay)

      return this.deployWinnerToWordPressWithRetry(result, attempt + 1)
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  private recordSync(resultId: string, postId: number): void {
    if (typeof window === 'undefined') return

    const syncHistory = JSON.parse(localStorage.getItem('wp-sync-history') || '{}')
    syncHistory[resultId] = {
      postId,
      syncedAt: new Date().toISOString(),
      status: 'success'
    }
    localStorage.setItem('wp-sync-history', JSON.stringify(syncHistory))
  }

  private notifySuccess(resultId: string, postId: number): void {
    if (typeof window === 'undefined') return

    window.dispatchEvent(new CustomEvent('wp-sync-success', {
      detail: { resultId, postId }
    }))
  }

  private notifyError(resultId: string, error: string): void {
    if (typeof window === 'undefined') return

    window.dispatchEvent(new CustomEvent('wp-sync-error', {
      detail: { resultId, error }
    }))
  }
}

export const roundTableAutoTrigger = new RoundTableAutoTrigger()
