import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8002';

// Disable caching for this route
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const force_refresh = searchParams.get('force_refresh') || 'false';

    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/smart-triage?force_refresh=${force_refresh}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', errorText);
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Smart triage proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to analyze email', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
