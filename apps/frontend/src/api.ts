import type {
  Action,
  ActionResponse,
  CreateRequest,
  SessionResponse,
} from "./generated/contract";
export interface Transport {
  create(
    mode: CreateRequest["mode"],
    requestId: string,
  ): Promise<SessionResponse>;
  get(sessionId: string): Promise<SessionResponse>;
  action(
    sessionId: string,
    revision: number,
    action: Action,
    requestId: string,
  ): Promise<ActionResponse>;
  restart(
    sessionId: string,
    revision: number,
    requestId: string,
  ): Promise<SessionResponse>;
}
export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public revision: number | null = null,
    public retryable = false,
  ) {
    super(message);
  }
}
export class ApiClient implements Transport {
  constructor(private fetcher: typeof fetch = (...args) => fetch(...args)) {}
  private async request<T>(path: string, body?: unknown): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await this.fetcher("/api/v1/" + path, {
        method: body === undefined ? "GET" : "POST",
        headers: { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });
      const result = await response.json();
      if (!response.ok)
        throw new ApiError(
          result.error?.code ?? "HTTP_ERROR",
          result.error?.message ??
            "The investigation service could not complete this request.",
          result.error?.current_revision ?? null,
          result.error?.retryable ?? false,
        );
      if (result.state?.contract_version !== "1.0.0")
        throw new ApiError(
          "CONTRACT_MISMATCH",
          "The server uses an unsupported contract. Refresh after the service is updated.",
        );
      return result as T;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (body === undefined)
        throw new ApiError(
          "NETWORK_UNAVAILABLE",
          "Could not retrieve the investigation state. Retry retrieval when the service is available.",
          null,
          true,
        );
      throw new ApiError(
        "NETWORK_UNCERTAIN",
        "The response could not be read. The request may have been accepted. Retry the same request or retrieve the latest state.",
        null,
        true,
      );
    } finally {
      clearTimeout(timeout);
    }
  }
  create(mode: CreateRequest["mode"], requestId: string) {
    return this.request<SessionResponse>("sessions", {
      request_id: requestId,
      content_id: "blackthorn_manor",
      mode,
    });
  }
  get(id: string) {
    return this.request<SessionResponse>("sessions/" + encodeURIComponent(id));
  }
  action(id: string, revision: number, action: Action, requestId: string) {
    return this.request<ActionResponse>(
      "sessions/" + encodeURIComponent(id) + "/actions",
      { request_id: requestId, expected_revision: revision, action },
    );
  }
  restart(id: string, revision: number, requestId: string) {
    return this.request<SessionResponse>(
      "sessions/" + encodeURIComponent(id) + "/restart",
      { request_id: requestId, expected_revision: revision },
    );
  }
}
