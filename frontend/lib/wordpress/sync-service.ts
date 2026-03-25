/**
 * WordPress Sync Service
 * Syncs LLM Round Table results to WordPress posts
 */

import { wpProxyFetch } from './proxy-client';

interface RoundTableResult {
  id: string;
  prompt_preview: string;
  created_at: string;
  entries: {
    provider: string;
    rank: number;
    response_preview: string;
    scores: {
      relevance: number;
      quality: number;
      completeness: number;
      efficiency: number;
      brand_alignment: number;
      total: number;
    };
    latency_ms: number;
    cost_usd: number;
  }[];
  winner: {
    provider: string;
    rank: number;
    scores: {
      relevance: number;
      quality: number;
      completeness: number;
      efficiency: number;
      brand_alignment: number;
      total: number;
    };
    latency_ms: number;
    cost_usd: number;
    response_preview: string;
  } | null;
}

interface WordPressPost {
  title: string;
  content: string;
  status: 'draft' | 'publish';
  categories: number[];
  tags: number[];
  meta: Record<string, any>;
}

export class WordPressSyncService {
  /**
   * Sync Round Table result to WordPress as a post
   */
  async syncRoundTableResult(
    result: RoundTableResult,
    options?: {
      status?: 'draft' | 'publish';
      title?: string;
    }
  ): Promise<{ success: boolean; postId?: number; error?: string }> {
    try {
      const post = this.formatRoundTablePost(result);

      // Override status if specified (default: draft)
      if (options?.status) {
        post.status = options.status;
      }

      // Override title if specified
      if (options?.title) {
        post.title = options.title;
      }

      const response = await wpProxyFetch('POST', '/wp/v2/posts', post);

      return {
        success: true,
        postId: response.id,
      };
    } catch (error) {
      console.error('WordPress sync failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Format Round Table result as WordPress post
   */
  private formatRoundTablePost(result: RoundTableResult): WordPressPost {
    const { prompt_preview, entries, winner, created_at } = result;

    // Create rich HTML content
    const content = `
      <div class="round-table-result">
        <div class="prompt-section">
          <h2>Prompt</h2>
          <blockquote>${this.escapeHtml(prompt_preview)}</blockquote>
        </div>

        <div class="winner-section" style="background: linear-gradient(135deg, #B76E79 0%, #8B5A68 100%); padding: 2rem; border-radius: 1rem; color: white; margin: 2rem 0;">
          <h2 style="margin: 0 0 1rem 0;">🏆 Winner: ${winner?.provider || 'N/A'}</h2>
          <p style="font-size: 2rem; font-weight: bold; margin: 0;">Score: ${winner?.scores.total.toFixed(2) || 'N/A'}</p>
        </div>

        <div class="results-section">
          <h2>All Results</h2>
          ${entries
            .sort((a, b) => a.rank - b.rank)
            .map(
              (r, i) => `
            <div class="result-card" style="background: ${i === 0 ? '#f9f5f6' : '#ffffff'}; border: 2px solid ${i === 0 ? '#B76E79' : '#e5e7eb'}; border-radius: 0.75rem; padding: 1.5rem; margin: 1rem 0;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0;">${r.rank}. ${r.provider}</h3>
                <div style="display: flex; gap: 1rem; align-items: center;">
                  <span style="font-size: 1.5rem; font-weight: bold; color: #B76E79;">${r.scores.total.toFixed(2)}</span>
                  <span style="color: #6b7280; font-size: 0.875rem;">${r.latency_ms.toFixed(0)}ms</span>
                </div>
              </div>
              <div style="background: white; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #B76E79;">
                <p style="margin: 0; white-space: pre-wrap;">${this.escapeHtml(r.response_preview)}</p>
              </div>
            </div>
          `
            )
            .join('')}
        </div>

        <div class="metadata" style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 0.875rem;">
          <p>Generated on ${new Date(created_at).toLocaleString()}</p>
          <p>Powered by DevSkyy LLM Round Table</p>
        </div>
      </div>
    `;

    return {
      title: `LLM Round Table: ${prompt_preview.substring(0, 60)}${prompt_preview.length > 60 ? '...' : ''}`,
      content,
      status: 'draft', // Always create as draft for review
      categories: [1], // Default category
      tags: [],
      meta: {
        _skyyrose_llm_round_table: true,
        _skyyrose_winner: winner?.provider || '',
        _skyyrose_winner_score: winner?.scores.total || 0,
        _skyyrose_prompt: prompt_preview,
        _skyyrose_timestamp: created_at,
        _skyyrose_results_count: entries.length,
      },
    };
  }

  /**
   * Get sync status for a result
   */
  async getSyncStatus(resultId: string): Promise<{ synced: boolean; postId?: number; error?: string }> {
    // This would query WordPress to check if the post exists
    // For now, return a placeholder
    return { synced: false };
  }

  /**
   * Escape HTML for safe rendering
   */
  private escapeHtml(text: string): string {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, (c) => map[c]);
  }

  /**
   * Test WordPress connection
   */
  async testConnection(): Promise<{ success: boolean; error?: string }> {
    try {
      await wpProxyFetch('GET', '/wp/v2/posts');
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
}

/**
 * Get WordPress sync service instance.
 * Credentials are handled server-side by /api/wordpress/proxy.
 */
export function getWordPressSyncService(): WordPressSyncService {
  return new WordPressSyncService();
}
