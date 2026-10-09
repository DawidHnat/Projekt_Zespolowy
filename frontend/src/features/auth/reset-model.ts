export function resetTokenFromHash(hash: string): string | null {
  if (!hash.startsWith("#reset-password?")) return null;
  return (
    new URLSearchParams(hash.slice(hash.indexOf("?") + 1)).get("token") || ""
  );
}
export function validResetToken(token: string) {
  return /^[A-Za-z0-9_-]{20,100}$/.test(token);
}
