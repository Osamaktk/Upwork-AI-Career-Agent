export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function apiRequest<T>(
  path: string,
  token: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? {Authorization: `Bearer ${token}`} : {}),
      ...init.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({detail: response.statusText}));
    throw new Error(payload.detail ?? `Request failed with ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
