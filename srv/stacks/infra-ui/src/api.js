const API = import.meta.env.VITE_API_BASE_URL;

export async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    ...opts,
    headers: { "Content-Type": "application/json" }
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
