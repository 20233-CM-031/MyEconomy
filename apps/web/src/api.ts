import type { AIExplanation, AIQuestion, FinancialAccount, GuardianCase, ImportBatch, PersonalCase, PersonalCaseDetail, PersonalCaseStatus, PowerReport, Session } from './types';

const API_ROOT = '/api/v1';

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers,
    credentials: 'same-origin',
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = body?.error?.message || body?.detail || message;
    } catch {
      // Keep the HTTP status when the server did not return JSON.
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  demoSession: () => request<Session>('/auth/demo-session', { method: 'POST' }),
  login: (email: string, password: string) =>
    request<Session>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string, displayName: string) =>
    request<Session>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, display_name: displayName }),
    }),
  verifyEmail: (verificationToken: string) => request<{ email_verified: true }>('/auth/verify-email', {
    method: 'POST',
    body: JSON.stringify({ token: verificationToken }),
  }),
  me: (token: string) => request<Session['user']>('/auth/me', {}, token),
  report: (token: string, start: string, end: string, asOf: string) => {
    const params = new URLSearchParams({
      period_start: start,
      period_end: end,
      as_of: asOf,
      currency: 'INR',
      obligation_horizon_days: '30',
    });
    return request<PowerReport>(`/personal/power-report?${params.toString()}`, {}, token);
  },
  guardianCases: (token: string) => request<GuardianCase[]>('/guardian/cases?limit=50', {}, token),
  personalCases: (token: string) => request<PersonalCase[]>('/cases?limit=50', {}, token),
  personalCase: (token: string, caseId: string) => request<PersonalCaseDetail>(`/cases/${caseId}`, {}, token),
  createCaseFromFinding: (
    token: string, findingId: string, periodStart: string, periodEnd: string, asOf: string,
  ) => request<PersonalCase>('/cases/from-finding', {
    method: 'POST',
    headers: { 'Idempotency-Key': `makos-case-open:${crypto.randomUUID()}` },
    body: JSON.stringify({
      finding_id: findingId,
      period_start: periodStart,
      period_end: periodEnd,
      as_of: asOf,
      currency: 'INR',
      obligation_horizon_days: 30,
    }),
  }, token),
  transitionCase: (
    token: string, caseId: string, toStatus: PersonalCaseStatus, expectedVersion: number, note: string,
  ) => request<PersonalCaseDetail>(`/cases/${caseId}/transition`, {
    method: 'POST',
    headers: { 'Idempotency-Key': `makos-case-transition:${crypto.randomUUID()}` },
    body: JSON.stringify({ to_status: toStatus, expected_version: expectedVersion, note }),
  }, token),

  accounts: (token: string) => request<FinancialAccount[]>('/financial/accounts', {}, token),
  createAccount: (token: string, accountName: string, accountType: string) =>
    request<FinancialAccount>('/financial/accounts', {
      method: 'POST',
      body: JSON.stringify({
        account_name: accountName,
        account_type: accountType,
        currency: 'INR',
        institution_label: null,
        masked_reference: null,
        opening_balance: '0.00',
      }),
    }, token),
  importStatement: async (token: string, accountId: string, file: File) => {
    const bytes = await file.arrayBuffer();
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    const hex = Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, '0')).join('');
    const idempotencyKey = `makos-csv:${accountId}:${hex}`;
    const response = await fetch(`${API_ROOT}/financial/accounts/${accountId}/imports/csv`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'text/csv',
        'Authorization': `Bearer ${token}`,
        'Idempotency-Key': idempotencyKey,
        'X-Filename': file.name,
      },
      body: bytes,
      credentials: 'same-origin',
    });
    const result = await response.json();
    if (!response.ok) {
      const firstError = result?.validation_errors?.[0]?.message;
      const message = firstError || result?.error?.message || result?.detail || `Import failed (${response.status})`;
      throw new Error(message);
    }
    return result as ImportBatch;
  },
  createAIConsent: async (token: string) => {
    const terms = await request<Array<{
      purpose: string;
      version: string;
      allowed_categories: string[];
      recipient_type: string;
    }>>('/consents/terms', {}, token);
    const aiTerms = terms.find((item) => item.purpose === 'ai_assistance');
    if (!aiTerms) throw new Error('AI assistance consent is not installed on this API yet.');
    return request('/consents', {
      method: 'POST',
      body: JSON.stringify({
        purpose: 'ai_assistance',
        data_categories: ['financial_summary', 'household_obligations'],
        recipient_type: 'service',
        recipient_id: 'meta-model-api',
        terms_version: aiTerms.version,
        confirmed: true,
      }),
    }, token);
  },
  getConsents: (token: string) => request<Array<{ id: string; purpose: string; recipient_id: string; status: string }>>('/consents', {}, token),
  revokeConsent: (token: string, consentId: string) => request(`/consents/${consentId}/revoke`, { method: 'POST' }, token),
  explain: (
    token: string,
    periodStart: string,
    periodEnd: string,
    asOf: string,
    questionIntent: AIQuestion,
  ) => request<AIExplanation>('/intelligence/personal-explanation', {
    method: 'POST',
    body: JSON.stringify({
      period_start: periodStart,
      period_end: periodEnd,
      as_of: asOf,
      currency: 'INR',
      question_intent: questionIntent,
    }),
  }, token),
  health: () => fetch('/health/ready').then((r) => r.ok),
};
