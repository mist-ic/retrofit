/**
 * Client-side interface to the RetroFit Backend API.
 */

export async function startPipelineRun(landingPageUrl: string, adImageFile?: File | null): Promise<string> {
  const formData = new FormData();
  formData.append("landing_page_url", landingPageUrl);

  if (adImageFile) {
    formData.append("ad_image", adImageFile);
  }

  // Uses the Next.js rewrite rule in next.config.ts to proxy to http://localhost:8080/api/runs
  const response = await fetch("/api/runs", {
    method: "POST",
    body: formData,
    // Do not set Content-Type header manually when sending FormData
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Failed to initiate run: ${response.status} ${errText}`);
  }

  const data = await response.json();
  return data.run_id;
}
