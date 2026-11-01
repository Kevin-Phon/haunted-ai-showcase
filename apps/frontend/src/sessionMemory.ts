// Browser storage is optional. Backend authority never depends on it.
export function rememberedSession(): string | null {
  try {
    return localStorage.getItem("blackthorn-session");
  } catch {
    return null;
  }
}
export function rememberSession(id: string): void {
  try {
    localStorage.setItem("blackthorn-session", id);
  } catch {
    /* Investigation remains usable when browser storage is unavailable. */
  }
}
