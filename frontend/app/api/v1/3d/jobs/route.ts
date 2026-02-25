import { NextRequest, NextResponse } from 'next/server';

// In-memory job store (replaced by database in production)
const jobStore: Array<{
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  provider: string;
  input_type: 'text' | 'image';
  input: string;
  output_url?: string;
  error?: string;
  created_at: string;
  completed_at?: string;
}> = [];

export { jobStore };

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const limit = Math.min(Math.max(1, Number(searchParams.get('limit')) || 20), 100);

  return NextResponse.json(jobStore.slice(0, limit));
}
