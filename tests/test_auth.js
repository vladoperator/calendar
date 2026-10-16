// Exercise authentication behavior with a fake DOM and cloud, without real accounts.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const authScript = html.match(/<script>\s*(\/\* Supabase cloud persistence[\s\S]*?)<\/script>/)[1];

function app(overrides = {}) {
  const elements = new Map();
  const calls = [];
  class Element {
    constructor() { this.style = {}; this.dataset = {}; this.value = ''; this.textContent = ''; }
    set innerHTML(value) {
      this.html = value;
      for (const id of ['authGateForm', 'authGateMessage', 'gateEmail', 'gatePassword', 'gateConfirmPassword', 'authSubmit']) elements.delete(id);
      for (const match of value.matchAll(/id="([^"]+)"/g)) elements.set(match[1], new Element());
      this.buttons = [new Element(), elements.get('authSubmit')];
      elements.get('authGateForm').buttons = this.buttons;
    }
    setCustomValidity(message) { this.validationMessage = message; }
    reportValidity() { return !elements.get('gateConfirmPassword')?.validationMessage; }
    querySelectorAll() { return this.buttons || []; }
    querySelector() { return elements.get('authSubmit'); }
  }
  const cloud = {
    configured: () => true,
    restoreSession: async () => null,
    signUp: async () => { calls.push('signup'); return { access_token: 'test-only' }; },
    signIn: async () => { calls.push('signin'); },
    signOut: async () => { calls.push('signout'); },
    getProfile: async () => ({ role: 'staff', approved: false }),
    loadState: async () => { calls.push('load'); return { clinic: {}, patients: [] }; },
    saveState: async () => { calls.push('save'); },
    approveUser: async () => { calls.push('approve'); },
    ...overrides,
  };
  const context = {
    dentaSupabase: cloud,
    q: id => elements.get(id),
    document: {
      querySelector: () => elements.get('app'),
      createElement: () => new Element(),
      head: { appendChild() {} },
      body: { appendChild(element) { elements.set(element.id, element); } },
    },
    localStorage: { setItem() {} },
    console: { error() {} },
    updateDbBadge() {}, closeModal() {}, refreshActiveView() {}, toast() {},
  };
  context.window = context;
  elements.set('app', new Element());
  vm.createContext(context);
  vm.runInContext(authScript, context);
  return { context, cloud, elements, calls };
}

test('registration requires matching passwords and signs out the new account', async () => {
  const { context, elements, calls } = app();
  context.requestClinicAccess();
  elements.get('gateEmail').value = 'new@example.test';
  elements.get('gatePassword').value = 'test-password-only';
  elements.get('gateConfirmPassword').value = 'different';
  await context.submitSupabaseAuth('signup');
  assert.deepEqual(calls, []);
  elements.get('gateConfirmPassword').value = 'test-password-only';
  await context.submitSupabaseAuth('signup');
  assert.deepEqual(calls, ['signup', 'signout']);
  assert.match(elements.get('authGateMessage').textContent, /aprobarea administratorului/);
  assert.equal(elements.get('gateEmail').value, 'new@example.test');
  assert.equal(elements.get('gatePassword').value, '');
});

test('confirmation-required registration explains the next step', async () => {
  const { context, elements } = app({ signUp: async () => ({ user: { id: 'test' } }) });
  context.requestClinicAccess();
  await context.submitSupabaseAuth('signup');
  assert.match(elements.get('authGateMessage').textContent, /confirmarea contului/);
});

test('pending accounts never load clinic data', async () => {
  const { context, elements, calls } = app();
  await context.submitSupabaseAuth('signin');
  assert.deepEqual(calls, ['signin', 'signout']);
  assert.match(elements.get('authGateMessage').textContent, /așteaptă aprobarea/);
  assert.equal(elements.get('authGate').style.display, 'grid');
});

test('approved staff can enter, but cannot approve other accounts', async () => {
  const { context, elements, calls } = app({ getProfile: async () => ({ role: 'staff', approved: true }) });
  await context.submitSupabaseAuth('signin');
  assert.deepEqual(calls, ['signin', 'load']);
  assert.equal(elements.get('authGate').style.display, 'none');
  await context.approveClinicUser('another-user');
  assert.ok(!calls.includes('approve'));
});

test('approved staff cannot seed a missing clinic workspace', async () => {
  const { context, calls, elements } = app({
    getProfile: async () => ({ role: 'staff', approved: true }),
    loadState: async () => null,
  });
  await context.submitSupabaseAuth('signin');
  assert.ok(!calls.includes('save'));
  assert.equal(elements.get('authGate').style.display, 'grid');
  assert.match(elements.get('authGateMessage').textContent, /inițializeze/);
});

test('double submissions produce only one registration request', async () => {
  let finish;
  let count = 0;
  const { context } = app({ signUp: () => { count++; return new Promise(resolve => { finish = resolve; }); } });
  context.requestClinicAccess();
  const first = context.submitSupabaseAuth('signup');
  await context.submitSupabaseAuth('signup');
  assert.equal(count, 1);
  finish({});
  await first;
});

test('auth errors are visible on the login card and allow another attempt', async () => {
  const { context, elements } = app({ signIn: async () => { throw Object.assign(new Error(), { code: 'email_not_confirmed' }); } });
  await context.submitSupabaseAuth('signin');
  assert.match(elements.get('authGateMessage').textContent, /Confirmă adresa/);
  assert.equal(elements.get('authSubmit').disabled, false);
});

test('cloud client preserves Supabase error codes for actionable messages', async () => {
  const context = {
    DENTA_SUPABASE_CONFIG: { url: 'https://example.test', publishableKey: 'public-test' },
    fetch: async () => ({ ok: false, status: 422, text: async () => JSON.stringify({ error_code: 'signup_disabled', msg: 'Disabled' }) }),
  };
  context.window = context;
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'supabase-client.js'), 'utf8'), context);
  await assert.rejects(context.dentaSupabase.signUp('new@example.test', 'test-password-only'), error => error.code === 'signup_disabled');
});
