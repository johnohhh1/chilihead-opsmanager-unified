import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic'; // Prevent static generation errors

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8002';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get('limit') || '10';

    const response = await fetch(`${BACKEND_URL}/api/operations-chat/sessions?limit=${limit}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', errorText);
      throw new Error('Failed to fetch sessions');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Sessions fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch sessions', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
