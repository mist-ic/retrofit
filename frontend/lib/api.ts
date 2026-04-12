import { RunResult } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export async function createRun(formData: FormData): Promise<{ run_id: string }> {
  const res = await fetch(`${API_BASE}/api/runs`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Failed to create run: ${res.statusText}`);
  return res.json();
}

export function getStreamUrl(runId: string): string {
  return `${API_BASE}/api/runs/${runId}/stream`;
}

export function getPreviewUrl(runId: string, variant: 'original' | 'variant'): string {
  return `${API_BASE}/api/preview/${runId}/${variant}`;
}

export function getScreenshotUrl(runId: string, variant: 'original' | 'modified'): string {
  return `${API_BASE}/api/screenshots/${runId}/${variant}`;
}

export async function getRunResult(runId: string): Promise<RunResult> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/result`);
  if (!res.ok) throw new Error(`Failed to get result: ${res.statusText}`);
  return res.json();
}
