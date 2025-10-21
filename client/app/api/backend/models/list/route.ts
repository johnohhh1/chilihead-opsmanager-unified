import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8002';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/models/list`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch models:', error);
    return NextResponse.json(
      { error: 'Failed to fetch models' },
      { status: 500 }
    );
  }
}
