/* Lightweight Supabase REST client used by the static Denta Atelier app. */
(function () {
  const config = window.DENTA_SUPABASE_CONFIG || {};
  const storageKey = 'dentaAtelierSupabaseSession';
  let session = null;
  let stateRowId = null;

  function configured() {
    return /^https:\/\//.test(config.url || '') && Boolean(config.publishableKey);
  }

  function headers(authenticated, extra) {
    const value = { apikey: config.publishableKey, ...extra };
    if (authenticated && session?.access_token) value.Authorization = `Bearer ${session.access_token}`;
    return value;
  }

  async function request(path, options = {}, authenticated = false) {
    const response = await fetch(`${config.url}${path}`, {
      ...options,
      headers: headers(authenticated, options.headers)
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `Supabase a răspuns cu ${response.status}.`);
    }
    return response.status === 204 ? null : response.json();
  }

  async function restoreSession() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || 'null');
      if (!saved?.access_token) return null;
      session = saved;
      const user = await request('/auth/v1/user', {}, true);
      session.user = user;
      return session;
    } catch (_) {
      localStorage.removeItem(storageKey);
      session = null;
      return null;
    }
  }

  function remember(value) {
    session = value;
    if (value?.access_token) localStorage.setItem(storageKey, JSON.stringify(value));
  }

  async function signIn(email, password) {
    const result = await request('/auth/v1/token?grant_type=password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    remember(result);
    return result;
  }

  async function signUp(email, password) {
    const result = await request('/auth/v1/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (result?.access_token) remember(result);
    return result;
  }

  async function signOut() {
    if (session?.access_token) {
      try { await request('/auth/v1/logout', { method: 'POST' }, true); } catch (_) {}
    }
    session = null;
    stateRowId = null;
    localStorage.removeItem(storageKey);
  }

  async function getProfile() {
    if (!session?.user?.id) throw new Error('Nu există utilizator autentificat.');
    const rows = await request(
      `/rest/v1/clinic_users?select=id,email,role,approved&id=eq.${encodeURIComponent(session.user.id)}&limit=1`,
      {}, true
    );
    return rows[0] || null;
  }

  async function listUsers() {
    return request('/rest/v1/clinic_users?select=id,email,role,approved,created_at&order=created_at.asc', {}, true);
  }

  async function approveUser(userId) {
    await request(`/rest/v1/clinic_users?id=eq.${encodeURIComponent(userId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Prefer: 'return=minimal' },
      body: JSON.stringify({ approved: true })
    }, true);
  }

  async function loadState() {
    const rows = await request('/rest/v1/clinic_state?select=id,data&limit=1', {}, true);
    if (!rows.length) return null;
    stateRowId = rows[0].id;
    return rows[0].data;
  }

  async function saveState(data) {
    const payload = JSON.stringify({ data });
    if (stateRowId) {
      await request(`/rest/v1/clinic_state?id=eq.${encodeURIComponent(stateRowId)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Prefer: 'return=minimal' },
        body: payload
      }, true);
      return;
    }
    const rows = await request('/rest/v1/clinic_state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Prefer: 'return=representation' },
      body: payload
    }, true);
    stateRowId = rows[0]?.id || null;
  }

  window.dentaSupabase = {
    configured, restoreSession, signIn, signUp, signOut, getProfile, listUsers, approveUser, loadState, saveState,
    get session() { return session; }
  };
})();
