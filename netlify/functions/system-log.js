export async function handler(event) {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' }
  }

  const token = event.headers['x-system-token'] || event.headers['X-System-Token']
  if (!process.env.SYSTEM_LOG_TOKEN || token !== process.env.SYSTEM_LOG_TOKEN) {
    return { statusCode: 401, body: 'Unauthorized' }
  }

  let payload = null
  try {
    payload = JSON.parse(event.body || '{}')
  } catch {
    return { statusCode: 400, body: 'Invalid JSON' }
  }

  const { action, data } = payload
  if (!action) {
    return { statusCode: 400, body: 'Missing action' }
  }

  // Middleman endpoint for sensitive operations (server-side only).
  // Implement the actual action handlers here (e.g. reset RFID master keys, bulk update prices).
  // Keep credentials / secrets in Netlify Environment Variables.
  return {
    statusCode: 200,
    body: JSON.stringify({
      ok: true,
      received: { action, data: data ?? null },
      ts: Date.now(),
    }),
    headers: { 'Content-Type': 'application/json' },
  }
}

