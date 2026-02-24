/**
 * Pipeline Status Dashboard - API Route
 *
 * GET /api/pipeline-status
 *   Returns the aggregated status of ALL content-automation pipelines.
 *
 * Query params:
 *   ?dry_run=true  - Returns simulated all-green data for UI testing.
 *   ?pipeline=name - Filter to a single pipeline (case-insensitive).
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  getAllPipelineStatuses,
  getAllPipelineStatusesDryRun,
  getPipelineStatus,
} from '@/lib/pipeline-config';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = request.nextUrl;
    const dryRun = searchParams.get('dry_run') === 'true';
    const pipelineFilter = searchParams.get('pipeline');

    if (dryRun) {
      return NextResponse.json(getAllPipelineStatusesDryRun());
    }

    if (pipelineFilter) {
      const status = getPipelineStatus(pipelineFilter);
      if (!status) {
        return NextResponse.json(
          {
            success: false,
            error: `Unknown pipeline: ${pipelineFilter}`,
            timestamp: new Date().toISOString(),
          },
          { status: 404 },
        );
      }
      return NextResponse.json({
        success: true,
        dry_run: false,
        timestamp: new Date().toISOString(),
        pipeline: status,
      });
    }

    return NextResponse.json(getAllPipelineStatuses());
  } catch {
    return NextResponse.json(
      {
        success: false,
        error: 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    );
  }
}
