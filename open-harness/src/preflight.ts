export interface VisionPreflightResult {
  ok: boolean;
  status?: number;
  message: string;
}

export async function checkVisionHealth(
  visionBaseUrl: string,
  timeoutMs = 4000
): Promise<VisionPreflightResult> {
  const url = `${visionBaseUrl.replace(/\/$/, "")}/api/health`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, { signal: controller.signal });
    const bodyText = await response.text();
    const preview = bodyText.slice(0, 180);

    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        message: `Health endpoint responded ${response.status}: ${preview}`,
      };
    }

    return {
      ok: true,
      status: response.status,
      message: preview || "Vision health endpoint reachable",
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      ok: false,
      message: `Vision preflight failed: ${message}`,
    };
  } finally {
    clearTimeout(timer);
  }
}
