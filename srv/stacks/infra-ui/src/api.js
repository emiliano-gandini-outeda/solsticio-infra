import { CONFIG } from "./config.js";

export async function api(path, opts = {}) {
  // Check if path is already a full URL
  let url;
  if (path.startsWith('http://') || path.startsWith('https://')) {
    url = path;
  } else {
    url = CONFIG.INFRA_API_URL + path;
  }

  opts.headers = {
    ...opts.headers,
    "Authorization": `Bearer ${CONFIG.INFRA_API_TOKEN}`,
    "Content-Type": "application/json"
  };

  if (opts.body && typeof opts.body !== "string") opts.body = JSON.stringify(opts.body);

  const res = await fetch(url, opts);
  const text = await res.text();

  try {
    const data = text ? JSON.parse(text) : {};
    if (!res.ok) throw new Error(JSON.stringify({ status: res.status, data }));
    return data;
  } catch {
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);
    return text;
  }
}
