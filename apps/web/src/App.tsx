import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from './api';
import { demoCases, demoMonthly, demoObligations, demoPersonalCases, demoReport } from './demo';
import type { AIExplanation, AIQuestion, FinancialAccount, Finding, GuardianCase, PersonalCase, PersonalCaseDetail, PersonalCaseStatus, PowerReport, Session, ViewKey } from './types';

const nav: Array<{ id: ViewKey; label: string; eyebrow?: string }> = [
  { id: 'overview', label: 'Your position' },
  { id: 'casebook', label: 'My actions' },
  { id: 'protection', label: 'Protection' },
  { id: 'opportunity', label: 'Opportunity' },
  { id: 'entitlements', label: 'Entitlements' },
  { id: 'enterprise', label: 'Your enterprise' },
  { id: 'commons', label: 'Commons' },
  { id: 'intelligence', label: 'AI intelligence' },
];

// Exact INR formatting for all monetary values: parse to integer paise, never float.
const toPaise = (value: string | number | bigint | null | undefined): bigint => {
  if (typeof value === 'bigint') return value;
  const raw = String(value ?? '0').trim();
  if (!/^-?\d{1,12}(?:\.\d{1,2})?$/.test(raw)) return 0n;
  const negative = raw.startsWith('-');
  const unsigned = negative ? raw.slice(1) : raw;
  const [rupees, paise = ''] = unsigned.split('.');
  const total = BigInt(rupees) * 100n + BigInt((paise + '00').slice(0, 2));
  return negative ? -total : total;
};
const formatPaise = (amount: bigint) => {
  const negative = amount < 0n;
  const absolute = negative ? -amount : amount;
  const rupees = absolute / 100n;
  const paise = (absolute % 100n).toString().padStart(2, '0');
  return `${negative ? '−' : ''}₹${new Intl.NumberFormat('en-IN').format(rupees)}.${paise}`;
};
const inr = (value: string | number | bigint | null | undefined) => formatPaise(toPaise(value));
// Number conversion is intentionally limited to chart geometry and percentage display.
const visualNumber = (value: string | number | null | undefined) => Number(value ?? 0);
const localToday = () => { const now = new Date(); return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`; };
const dateLabel = (date: string) => new Date(`${date}T12:00:00`).toLocaleDateString('en-IN', {
  day: 'numeric', month: 'short', year: 'numeric',
});
const percent = (a: number, b: number) => (b > 0 ? Math.max(0, Math.min(100, (a / b) * 100)) : 0);

function Mark() {
  return <div className="brand-mark" aria-hidden="true"><span>A</span><i /></div>;
}

function StatusDot({ tone = 'green' }: { tone?: 'green' | 'amber' | 'muted' }) {
  return <span className={`status-dot status-dot--${tone}`} />;
}

function ShellLabel({ children }: { children: string }) {
  return <div className="section-kicker">{children}</div>;
}

function App() {
  const [view, setView] = useState<ViewKey>('overview');
  const [mode, setMode] = useState<'demo' | 'live'>('demo');
  const [session, setSession] = useState<Session | null>(null);
  const [report, setReport] = useState<PowerReport>(demoReport);
  const [cases, setCases] = useState<GuardianCase[]>(demoCases);
  const [personalCases, setPersonalCases] = useState<PersonalCase[]>(demoPersonalCases);
  const [selectedPersonalCase, setSelectedPersonalCase] = useState<PersonalCaseDetail | null>(null);
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [periodStart, setPeriodStart] = useState('2026-10-01');
  const [periodEnd, setPeriodEnd] = useState('2026-10-31');
  const [asOf] = useState(localToday);
  const [loginOpen, setLoginOpen] = useState(false);
  const [apiReady, setApiReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [aiConsent, setAiConsent] = useState(false);
  const [aiConsentId, setAiConsentId] = useState<string | null>(null);
  const [aiOptIn, setAiOptIn] = useState(false);
  const [aiQuestion, setAiQuestion] = useState<AIQuestion>('prioritize_findings');
  const [aiResult, setAiResult] = useState<AIExplanation | null>(null);
  const [enterpriseCost, setEnterpriseCost] = useState('180');
  const [enterpriseTime, setEnterpriseTime] = useState('90');
  const [enterprisePackaging, setEnterprisePackaging] = useState('25');
  const [enterpriseDelivery, setEnterpriseDelivery] = useState('40');
  const [enterprisePrice, setEnterprisePrice] = useState('420');
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    api.health().then(setApiReady).catch(() => setApiReady(false));
  }, []);

  const refreshLive = useCallback(async () => {
    if (!session) return;
    setBusy(true); setError('');
    try {
      const [nextReport, nextCases, nextPersonalCases, consents, nextAccounts] = await Promise.all([
        api.report(session.access_token, periodStart, periodEnd, asOf),
        api.guardianCases(session.access_token).catch(() => [] as GuardianCase[]),
        api.personalCases(session.access_token),
        api.getConsents(session.access_token).catch(() => []),
        api.accounts(session.access_token),
      ]);
      setReport(nextReport);
      setCases(nextCases);
      setPersonalCases(nextPersonalCases);
      setSelectedPersonalCase(null);
      setAccounts(nextAccounts);
      const activeAI = consents.find((grant) => grant.purpose === 'ai_assistance' && grant.recipient_id === 'meta-model-api' && grant.status === 'active');
      setAiConsent(Boolean(activeAI));
      setAiConsentId(activeAI?.id ?? null);
      setNotice('Private data refreshed from your AwnNORA account.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The live account could not be refreshed.');
    } finally {
      setBusy(false);
    }
  }, [session, periodStart, periodEnd, asOf]);

  useEffect(() => {
    if (session && mode === 'live') void refreshLive();
  }, [session, mode, refreshLive]);

  const connectLive = () => {
    setMode('live');
    setLoginOpen(true);
    setError('');
    setNotice('Connect a verified local or sandbox account. Demo data will not be copied into it.');
  };

  const backToDemo = () => {
    setSession(null);
    setMode('demo');
    setReport(demoReport);
    setCases(demoCases);
    setPersonalCases(demoPersonalCases);
    setSelectedPersonalCase(null);
    setAccounts([]);
    setAiResult(null);
    setAiConsent(false);
    setAiConsentId(null);
    setNotice('Synthetic demonstration workspace restored.');
    setError('');
  };

  const onLogin = async (email: string, password: string) => {
    setBusy(true); setError('');
    try {
      const result = await api.login(email, password);
      if (!result.user.email_verified) throw new Error('Verify this account before using Personal Mode.');
      setSession(result);
      setMode('live');
      setPersonalCases([]);
      setSelectedPersonalCase(null);
      setLoginOpen(false);
      setNotice('Connected. Loading your private economic report.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Sign in failed.');
    } finally {
      setBusy(false);
    }
  };


  const createFinancialAccount = async (accountName: string, accountType: string) => {
    if (!session) throw new Error('Connect a verified account first.');
    setBusy(true); setError('');
    try {
      const account = await api.createAccount(session.access_token, accountName, accountType);
      setAccounts((current) => [...current, account]);
      setNotice(`${account.account_name} is ready. Choose a CSV statement to import.`);
      return account;
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : 'Account could not be created.';
      setError(message);
      throw cause;
    } finally {
      setBusy(false);
    }
  };

  const importFinancialStatement = async (accountId: string, file: File) => {
    if (!session) throw new Error('Connect a verified account first.');
    setBusy(true); setError('');
    let committed = false;
    try {
      if (file.size === 0 || file.size > 2 * 1024 * 1024) {
        throw new Error('Choose a non-empty CSV file no larger than 2 MiB.');
      }
      const batch = await api.importStatement(session.access_token, accountId, file);
      committed = true;
      setNotice(`Statement import ${batch.status.toLowerCase()}: ${batch.inserted_count} new rows, ${batch.updated_count} updates, ${batch.duplicate_count} duplicates. Refreshing your report.`);
      try {
        const [nextReport, nextCases, nextPersonalCases, consents, nextAccounts] = await Promise.all([
          api.report(session.access_token, periodStart, periodEnd, asOf),
          api.guardianCases(session.access_token).catch(() => [] as GuardianCase[]),
          api.personalCases(session.access_token),
          api.getConsents(session.access_token).catch(() => []),
          api.accounts(session.access_token),
        ]);
        setReport(nextReport);
        setCases(nextCases);
        setPersonalCases(nextPersonalCases);
        setAccounts(nextAccounts);
        const activeAI = consents.find((grant) => grant.purpose === 'ai_assistance' && grant.recipient_id === 'meta-model-api' && grant.status === 'active');
        setAiConsent(Boolean(activeAI));
        setAiConsentId(activeAI?.id ?? null);
        setNotice(`Statement import ${batch.status.toLowerCase()} and report refreshed: ${batch.inserted_count} new rows, ${batch.updated_count} updates, ${batch.duplicate_count} duplicates.`);
      } catch (refreshCause) {
        const message = refreshCause instanceof Error ? refreshCause.message : 'Unknown refresh error.';
        setError(`Import completed and saved. The report refresh failed: ${message} Use Refresh report to retry; do not re-upload the same file.`);
      }
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : 'Statement import failed.';
      setError(committed ? `Import completed, but a later step failed: ${message}` : message);
      throw cause;
    } finally {
      setBusy(false);
    }
  };

  const grantAIConsent = async () => {
    if (!session) return;
    setBusy(true); setError('');
    try {
      const grant = await api.createAIConsent(session.access_token) as { id: string };
      setAiConsent(true);
      setAiConsentId(grant.id);
      setAiOptIn(false);
      setNotice('AI assistance consent saved for the Meta Model API. You can revoke it in account settings.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Consent could not be saved.');
    } finally {
      setBusy(false);
    }
  };

  const revokeAIConsent = async () => {
    if (!session || !aiConsentId) return;
    setBusy(true); setError('');
    try {
      await api.revokeConsent(session.access_token, aiConsentId);
      setAiConsent(false);
      setAiConsentId(null);
      setAiResult(null);
      setNotice('AI assistance consent revoked. Future Meta explanation requests are blocked.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Consent could not be revoked.');
    } finally {
      setBusy(false);
    }
  };

  const askMeta = async () => {
    if (!session || !aiConsent) return;
    setBusy(true); setError(''); setAiResult(null);
    try {
      const result = await api.explain(session.access_token, periodStart, periodEnd, asOf, aiQuestion);
      setAiResult(result);
      setNotice('Muse Spark returned a structured explanation. The underlying financial calculations remain deterministic.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Meta AI assistance is unavailable.');
    } finally {
      setBusy(false);
    }
  };

  const openCaseFromFinding = async (finding: Finding) => {
    setError('');
    if (mode === 'demo') {
      const now = new Date().toISOString();
      const id = `SYN-CASE-LOCAL-${crypto.randomUUID().slice(0, 8)}`;
      const nextCase: PersonalCaseDetail = {
        id,
        source_engine: 'PERSONAL',
        source_finding_id: finding.finding_id,
        title: finding.title,
        currency: finding.currency || report.currency,
        amount_minor: finding.amount === null ? null : toPaise(finding.amount).toString(),
        source_snapshot: {
          finding_id: finding.finding_id,
          code: finding.code,
          priority: finding.priority,
          title: finding.title,
          explanation: finding.explanation,
          recommended_next_step: finding.recommended_next_step,
          amount: finding.amount,
          currency: finding.currency,
          source_references: [...finding.source_references],
          value_status: finding.value_status,
          report_period: { period_start: periodStart, period_end: periodEnd, as_of: asOf },
          origin: 'SYNTHETIC_DEMO_FIXTURE',
        },
        status: 'OPEN',
        state_version: 1,
        created_at: now,
        updated_at: now,
        events: [{
          id: `${id}-E1`, event_sequence: 1, event_type: 'CASE_OPENED', from_status: null,
          to_status: 'OPEN', note: 'Opened from a synthetic Personal Power finding. No external action was taken.', created_at: now,
        }],
      };
      setPersonalCases((current) => [nextCase, ...current]);
      setSelectedPersonalCase(nextCase);
      setView('casebook');
      setNotice('Synthetic case opened in this browser session. No account record was created.');
      return;
    }
    if (!session) {
      setError('Connect a verified account before opening a persistent case.');
      return;
    }
    setBusy(true);
    try {
      const created = await api.createCaseFromFinding(
        session.access_token, finding.finding_id, periodStart, periodEnd, asOf,
      );
      const detail = await api.personalCase(session.access_token, created.id);
      setPersonalCases((current) => [created, ...current.filter((item) => item.id !== created.id)]);
      setSelectedPersonalCase(detail);
      setView('casebook');
      setNotice(created.replayed ? 'This finding already has a case. Its existing timeline is open.' : 'Case created from the current server-computed finding.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The case could not be opened. Refresh the report and try again.');
    } finally {
      setBusy(false);
    }
  };

  const openPersonalCase = async (caseId: string) => {
    if (mode === 'demo') {
      const item = personalCases.find((candidate) => candidate.id === caseId) as PersonalCaseDetail | undefined;
      if (item) setSelectedPersonalCase(item);
      return;
    }
    if (!session) return;
    setBusy(true);
    setError('');
    try {
      const detail = await api.personalCase(session.access_token, caseId);
      setSelectedPersonalCase(detail);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The case could not be loaded.');
    } finally {
      setBusy(false);
    }
  };

  const transitionSelectedCase = async (toStatus: PersonalCaseStatus) => {
    if (!selectedPersonalCase) return;
    const current = selectedPersonalCase;
    const note = toStatus === 'WAITING_EXTERNAL'
      ? 'User recorded a manually performed external step. AwnNORA did not send a message or contact a provider.'
      : toStatus === 'RESOLVED'
        ? 'User marked this workflow resolved. This is not independent settlement or savings evidence.'
        : `User moved the case to ${toStatus.replaceAll('_', ' ').toLowerCase()} from MAKOS.`;
    if (mode === 'demo') {
      const now = new Date().toISOString();
      const nextVersion = current.state_version + 1;
      const updated: PersonalCaseDetail = {
        ...current,
        status: toStatus,
        state_version: nextVersion,
        updated_at: now,
        events: [...current.events, {
          id: `${current.id}-E${nextVersion}`,
          event_sequence: nextVersion,
          event_type: 'STATUS_CHANGED',
          from_status: current.status,
          to_status: toStatus,
          note,
          created_at: now,
        }],
      };
      setSelectedPersonalCase(updated);
      setPersonalCases((items) => items.map((item) => item.id === updated.id ? updated : item));
      setNotice('Synthetic case state updated locally. Verified value remains unchanged.');
      return;
    }
    if (!session) return;
    setBusy(true);
    setError('');
    try {
      const updated = await api.transitionCase(
        session.access_token, current.id, toStatus, current.state_version, note,
      );
      setSelectedPersonalCase(updated);
      setPersonalCases((items) => items.map((item) => item.id === updated.id ? updated : item));
      setNotice('Case timeline saved. No external action was performed.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The case could not be updated. Reload the case before retrying.');
    } finally {
      setBusy(false);
    }
  };


  const outstanding = useMemo(() => report.findings.filter((item) => item.priority === 'HIGH' || item.priority === 'MEDIUM'), [report]);
  const demoMode = mode === 'demo';
  const syntheticAccountCount = accounts.filter((account) => account.source_type === 'SYNTHETIC_FIXTURE').length;
  const hasSyntheticAccountData = syntheticAccountCount > 0;
  const isSyntheticEnvironment = demoMode || hasSyntheticAccountData;
  const environmentLabel = demoMode ? 'SYNTHETIC DEMO' : syntheticAccountCount === accounts.length && syntheticAccountCount > 0 ? 'SYNTHETIC FIXTURE DATA' : hasSyntheticAccountData ? 'MIXED DATA' : 'PRIVATE ACCOUNT';
  const productName = import.meta.env.VITE_PRODUCT_NAME || 'AwnNORA';

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand-lockup" onClick={() => setView('overview')} aria-label="AwnNORA home">
          <Mark />
          <span><strong>{productName}</strong><small>HUMAN ECONOMIC INTELLIGENCE</small></span>
        </button>

        <div className="sidebar-caption">YOUR SPACE</div>
        <div className="nav-list" role="navigation" aria-label="Main navigation">
          {nav.map((item) => (
            <button key={item.id} className={`nav-item ${view === item.id ? 'is-active' : ''}`} onClick={() => setView(item.id)}>
              <span className={`nav-glyph nav-glyph--${item.id}`} aria-hidden="true" />
              <span>{item.label}</span>
              {item.id === 'protection' && outstanding.length > 0 && <small className="nav-count">{outstanding.length}</small>}
              {item.id === 'casebook' && personalCases.length > 0 && <small className="nav-count">{personalCases.length}</small>}
            </button>
          ))}
        </div>

        <div className="sidebar-rule" />
        <div className="sidebar-caption">SYSTEM</div>
        <button className="nav-item nav-item--quiet" onClick={() => setShowHelp((value) => !value)}>
          <span className="nav-glyph nav-glyph--guide" aria-hidden="true" />
          <span>How AwnNORA works</span>
        </button>
        <button className="nav-item nav-item--quiet" onClick={() => setView('intelligence')}>
          <span className="nav-glyph nav-glyph--settings" aria-hidden="true" />
          <span>Data & permissions</span>
        </button>

        <div className="sidebar-bottom">
          <div className="privacy-note">
            <div className="privacy-note__top"><span className="privacy-symbol" /> PRIVATE BY DEFAULT</div>
            <p>Your records stay in your personal space. Sharing is a separate choice.</p>
            <button onClick={() => setView('commons')}>Understand sharing <span>↗</span></button>
          </div>
          <div className="account-block">
            <div className="avatar">{session?.user.display_name?.slice(0, 1).toUpperCase() || 'A'}</div>
            <div className="account-text"><strong>{session?.user.display_name || 'Personal workspace'}</strong><small>{session?.user.email || 'Not connected'}</small></div>
            <button className="account-menu" aria-label="Account options" onClick={() => (session ? setView('intelligence') : setLoginOpen(true))}>•••</button>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb"><span>PERSONAL MODE</span><i>/</i><strong>{nav.find((item) => item.id === view)?.label || 'Overview'}</strong></div>
          <div className="topbar-right">
            <div className={`environment-pill ${isSyntheticEnvironment ? 'environment-pill--demo' : 'environment-pill--live'}`}>
              <StatusDot tone={isSyntheticEnvironment ? 'amber' : 'green'} />
              {environmentLabel}
            </div>
            <div className="system-state"><StatusDot tone={apiReady ? 'green' : 'muted'} /> API {apiReady ? 'READY' : 'NOT CONNECTED'}</div>
            {session ? <button className="topbar-action" onClick={backToDemo}>Return to demo</button> : <button className="topbar-action" onClick={connectLive}>Connect account</button>}
          </div>
        </header>

        <div className="page-content">
          {notice && <div className="notice-line"><StatusDot />{notice}<button onClick={() => setNotice('')} aria-label="Dismiss notice">×</button></div>}
          {mode === 'live' && hasSyntheticAccountData && <div className="data-origin-note" role="status"><strong>SYNTHETIC FIXTURE RECORDS</strong><span>{syntheticAccountCount === accounts.length ? 'This private account is populated with a fictional test persona. No real bank history or verified financial outcome is represented.' : 'This private account contains both synthetic fixture accounts and other accounts. The synthetic records are excluded from claims of real-world impact.'}</span></div>}
          {error && <div className="error-line"><span>!</span>{error}<button onClick={() => setError('')} aria-label="Dismiss error">×</button></div>}
          {showHelp && <div className="help-strip"><strong>One personal system. Six connected engines.</strong><span>MAKOS organizes your cases and decisions. GENIEA coordinates bounded work. KRN preserves evidence and context. Deterministic services protect calculations and permissions.</span><button onClick={() => setShowHelp(false)}>Close</button></div>}

          {view === 'overview' && <OverviewPage report={report} accounts={accounts} mode={mode} busy={busy} outstanding={outstanding} onReview={() => setView('protection')} onIntelligence={() => setView('intelligence')} onRefresh={refreshLive} onCreateAccount={createFinancialAccount} onOpenCase={openCaseFromFinding} onImportStatement={importFinancialStatement} periodStart={periodStart} periodEnd={periodEnd} setPeriodStart={setPeriodStart} setPeriodEnd={setPeriodEnd} asOf={asOf} />}
          {view === 'casebook' && <CasebookPage cases={personalCases} selectedCase={selectedPersonalCase} mode={mode} busy={busy} onSelect={openPersonalCase} onTransition={transitionSelectedCase} />}
          {view === 'protection' && <ProtectionPage cases={cases} mode={mode} onAI={() => setView('intelligence')} />}
          {view === 'opportunity' && <OpportunityPage mode={mode} />}
          {view === 'entitlements' && <EntitlementsPage mode={mode} />}
          {view === 'enterprise' && <EnterprisePage cost={enterpriseCost} setCost={setEnterpriseCost} time={enterpriseTime} setTime={setEnterpriseTime} packaging={enterprisePackaging} setPackaging={setEnterprisePackaging} delivery={enterpriseDelivery} setDelivery={setEnterpriseDelivery} price={enterprisePrice} setPrice={setEnterprisePrice} mode={mode} />}
          {view === 'commons' && <CommonsPage mode={mode} />}
          {view === 'intelligence' && <IntelligencePage mode={mode} session={session} aiConsent={aiConsent} setAiOptIn={setAiOptIn} aiOptIn={aiOptIn} grantConsent={grantAIConsent} revokeConsent={revokeAIConsent} question={aiQuestion} setQuestion={setAiQuestion} askMeta={askMeta} aiResult={aiResult} busy={busy} />}
        </div>
        <footer className="page-footer"><span>AWNNORA · INTELLIGENCE FOR THE INDIVIDUAL. POWER FOR EVERYONE.</span><span>FINANCIAL TRUTH IS DETERMINISTIC. DECISIONS STAY YOURS.</span></footer>
      </main>

      {loginOpen && <LoginDialog busy={busy} onClose={() => { setLoginOpen(false); if (!session) setMode('demo'); }} onLogin={onLogin} onConnected={(result) => { setSession(result); setMode('live'); setPersonalCases([]); setSelectedPersonalCase(null); setLoginOpen(false); setNotice('Email verified. Your private workspace is connected.'); }} />}
    </div>
  );
}

function OverviewPage({
  report, accounts, mode, busy, outstanding, onReview, onIntelligence, onRefresh,
  onCreateAccount, onOpenCase, onImportStatement, periodStart, periodEnd, setPeriodStart, setPeriodEnd, asOf,
}: {
  report: PowerReport; accounts: FinancialAccount[]; mode: 'demo' | 'live'; busy: boolean; outstanding: Finding[];
  onReview: () => void; onIntelligence: () => void; onRefresh: () => void;
  onCreateAccount: (name: string, type: string) => Promise<FinancialAccount>;
  onOpenCase: (finding: Finding) => void;
  onImportStatement: (accountId: string, file: File) => Promise<void>;
  periodStart: string; periodEnd: string; setPeriodStart: (value: string) => void;
  setPeriodEnd: (value: string) => void; asOf: string;
}) {
  const spendRatio = percent(visualNumber(report.gross_expenses), visualNumber(report.income_total));
  return (
    <>
      <section className="page-intro page-intro--overview">
        <div>
          <ShellLabel>YOUR ECONOMIC PICTURE</ShellLabel>
          <h1>Make your next move<br /><em>with confidence.</em></h1>
          <p>A considered view of what comes in, what goes out, and what deserves your attention next.</p>
        </div>
        <div className="intro-meta">
          <div className="as-of-label">REPORTING PERIOD</div>
          <div className="period-controls">
            <label><span>FROM</span><input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} /></label>
            <label><span>TO</span><input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} /></label>
          </div>
          <div className="period-actions">
            <small>As at {dateLabel(asOf)}</small>
            <button className="text-action" disabled={busy || mode !== 'live'} onClick={onRefresh}>{busy ? 'Refreshing…' : 'Refresh report ↗'}</button>
          </div>
        </div>
      </section>

      <StatementImportPanel accounts={accounts} mode={mode} busy={busy} onCreateAccount={onCreateAccount} onImportStatement={onImportStatement} />

      <section className="metric-band" aria-label="Financial summary">
        <Metric label="CLASSIFIED INFLOW" value={inr(report.income_total)} sub={`${report.account_count} active accounts`} />
        <Metric label="NET OUTFLOW" value={inr(report.net_expenses_after_refunds)} sub={`${inr(report.refunds)} in recorded refunds`} />
        <Metric label="NET CASHFLOW" value={inr(report.net_cashflow)} sub={toPaise(report.net_cashflow) >= 0 ? 'Positive for this period' : 'Outflow exceeded inflow'} tone={toPaise(report.net_cashflow) >= 0 ? 'positive' : 'negative'} />
        <Metric label="ESSENTIALS DUE · 30 DAYS" value={inr(report.upcoming_essential_obligations)} sub={`${report.upcoming_obligation_count} obligations due`} />
      </section>

      <section className="overview-grid">
        <div className="overview-primary">
          <div className="section-heading">
            <div><ShellLabel>THE MONTH IN VIEW</ShellLabel><h2>Where your money moved</h2></div>
            <span className="muted-meta">{report.posted_transaction_count.toLocaleString('en-IN')} posted records · {report.currency}</span>
          </div>
          <div className="cashflow-panel">
            <div className="cashflow-panel__legend"><span><i className="legend-dot legend-dot--income" /> Classified inflow</span><span><i className="legend-dot legend-dot--spend" /> Net outflow</span><span className="chart-unit">INDICATIVE COMPARISON</span></div>
            <CashflowChart report={report} />
            <div className="cashflow-foot"><span>Essential costs <strong>{inr(report.essential_expenses)}</strong></span><span>Discretionary <strong>{inr(report.discretionary_expenses)}</strong></span><span>Outflow / inflow <strong>{spendRatio.toFixed(0)}%</strong></span></div>
          </div>

          <div className="section-heading attention-heading">
            <div><ShellLabel>YOUR ATTENTION</ShellLabel><h2>Worth a closer look</h2></div>
            <button className="text-action" onClick={onReview}>Open protection desk ↗</button>
          </div>
          <div className="finding-list">
            {report.findings.length === 0 && <div className="empty-state">No findings for this period. That is not a guarantee that every charge or opportunity has been checked.</div>}
            {report.findings.slice(0, 4).map((finding) => <div className="finding-action-row" key={finding.finding_id}><FindingRow finding={finding} onClick={onReview} /><button className="finding-open-case" onClick={() => onOpenCase(finding)}>Open case</button></div>)}
          </div>
        </div>

        <aside className="overview-aside">
          <div className="aside-section next-step-panel">
            <ShellLabel>THE NEXT STEP</ShellLabel>
            <div className="next-step-number">01</div>
            <h3>{outstanding[0]?.title || 'Keep your records complete'}</h3>
            <p>{outstanding[0]?.recommended_next_step || 'Add the records you want AwnNORA to review. It will not guess missing income or expenses.'}</p>
            <button className="primary-button primary-button--small" onClick={onReview}>Review the evidence <span>↗</span></button>
            <div className="aside-divider" />
            <div className="next-step-facts"><span>Potential duplicate candidates</span><strong>{report.potential_duplicate_count}</strong></div>
            <div className="next-step-facts"><span>Verified value created</span><strong>{inr(report.verified_value_created)}</strong></div>
            <small className="truth-note">Potential value is not counted until independently verified and settled.</small>
          </div>
          <div className="aside-section commitment-panel">
            <div className="section-heading section-heading--compact"><div><ShellLabel>LOOKING AHEAD</ShellLabel><h3>Coming due</h3></div><span className="mini-count">{report.upcoming_obligation_count}</span></div>
            {mode === 'demo' ? demoObligations.map((item) => <div className="due-row" key={item.name}><span className="due-date">{item.date}</span><span className="due-name">{item.name}</span><strong>{inr(item.amount)}</strong></div>) : <div className="due-empty">Your report includes the upcoming total. Open your financial records to inspect individual obligations.</div>}
            <div className="due-total"><span>Essential total</span><strong>{inr(report.upcoming_essential_obligations)}</strong></div>
          </div>
          <button className="intelligence-link" onClick={onIntelligence}><span className="intelligence-link__index">M</span><span><strong>Ask the intelligence layer</strong><small>Explore findings with Meta model assistance, when you choose to enable it.</small></span><b>↗</b></button>
        </aside>
      </section>

      <section className="engine-line">
        <div className="engine-line__intro"><ShellLabel>ONE CONNECTED SYSTEM</ShellLabel><h2>Built around your economic life</h2></div>
        <div className="engine-item"><strong>Guardian</strong><small>Protection & evidence</small><span className="engine-state engine-state--partial">In progress</span></div>
        <div className="engine-item"><strong>Opportunity</strong><small>Skills into income</small><span className="engine-state">Fixture preview</span></div>
        <div className="engine-item"><strong>Entitlements</strong><small>Benefits & claims</small><span className="engine-state">Fixture preview</span></div>
        <div className="engine-item"><strong>Commons</strong><small>Collective leverage</small><span className="engine-state">Simulation</span></div>
      </section>
    </>
  );
}

function CasebookPage({
  cases, selectedCase, mode, busy, onSelect, onTransition,
}: {
  cases: PersonalCase[];
  selectedCase: PersonalCaseDetail | null;
  mode: 'demo' | 'live';
  busy: boolean;
  onSelect: (caseId: string) => void;
  onTransition: (toStatus: PersonalCaseStatus) => void;
}) {
  const selected = selectedCase;
  const nextStatuses: Record<PersonalCaseStatus, PersonalCaseStatus[]> = {
    OPEN: ['IN_REVIEW', 'CLOSED'],
    IN_REVIEW: ['ACTION_READY', 'WAITING_FOR_USER', 'CLOSED'],
    ACTION_READY: ['IN_REVIEW', 'WAITING_FOR_USER', 'WAITING_EXTERNAL', 'CLOSED'],
    WAITING_FOR_USER: ['IN_REVIEW', 'ACTION_READY', 'CLOSED'],
    WAITING_EXTERNAL: ['IN_REVIEW', 'RESOLVED', 'CLOSED'],
    RESOLVED: ['CLOSED'],
    CLOSED: [],
  };
  const statusLabel: Record<PersonalCaseStatus, string> = {
    OPEN: 'Open', IN_REVIEW: 'In review', ACTION_READY: 'Action ready',
    WAITING_FOR_USER: 'Waiting for you', WAITING_EXTERNAL: 'Awaiting response',
    RESOLVED: 'Marked resolved', CLOSED: 'Closed',
  };
  const snapshot = selected?.source_snapshot;
  return <>
    <section className="page-intro casebook-intro">
      <div><ShellLabel>MAKOS · PERSONAL CASEBOOK</ShellLabel><h1>Your next steps,<br /><em>kept in one place.</em></h1><p>Turn a finding into a trackable piece of work. Every case keeps its source context, current state and change history.</p></div>
      <div className="intro-callout"><span>USER-CONTROLLED WORKFLOW</span><strong>No hidden submissions.</strong><small>Case status records your progress. AwnNORA does not contact providers or move money.</small></div>
    </section>
    <div className="casebook-notice"><strong>Important distinction</strong><span>“Awaiting response” means you are tracking a step you performed yourself. “Marked resolved” is not proof of a refund, award, saving or settled payment. Verified value remains separate.</span></div>
    <div className="casebook-layout">
      <aside className="casebook-list">
        <div className="casebook-list-head"><div><ShellLabel>YOUR CASES</ShellLabel><h2>Work in progress</h2></div><span>{cases.length}</span></div>
        {cases.length === 0 && <div className="casebook-empty">No cases yet. Open one from a finding in Your position.</div>}
        {cases.map((item) => <button key={item.id} className={`casebook-list-item ${selected?.id === item.id ? 'is-selected' : ''}`} onClick={() => onSelect(item.id)}>
          <span className="casebook-item-top"><small>{item.source_engine} · {item.source_finding_id}</small><i className={`case-status case-status--${item.status.toLowerCase()}`}>{statusLabel[item.status]}</i></span>
          <strong>{item.source_snapshot.title || item.title}</strong>
          <span className="casebook-item-date">Updated {dateLabel(item.updated_at.slice(0, 10))}</span>
        </button>)}
      </aside>
      <section className="casebook-detail" aria-live="polite">
        {!selected ? <div className="casebook-empty casebook-empty--detail"><ShellLabel>CASE DETAIL</ShellLabel><h2>Select a case</h2><p>Choose a case to inspect the finding that created it, its current state and its complete event timeline.</p></div> : <>
          <div className="case-detail-top"><div><ShellLabel>{`CASE ${selected.id.slice(0, 12).toUpperCase()}`}</ShellLabel><h2>{snapshot?.title || selected.title}</h2><p>{snapshot?.explanation || 'Source explanation is not available.'}</p></div><i className={`case-status case-status--${selected.status.toLowerCase()}`}>{statusLabel[selected.status]}</i></div>
          <div className="case-facts">
            <div><small>SOURCE FINDING</small><strong>{selected.source_finding_id}</strong></div>
            <div><small>REVIEW PERIOD</small><strong>{snapshot?.report_period.period_start} to {snapshot?.report_period.period_end}</strong></div>
            <div><small>REFERENCE AMOUNT</small><strong>{selected.amount_minor === null ? 'Not specified' : inr(BigInt(selected.amount_minor))}</strong></div>
            <div><small>CASE VERSION</small><strong>{selected.state_version}</strong></div>
          </div>
          <div className="case-next-step"><ShellLabel>SOURCE-RECOMMENDED NEXT STEP</ShellLabel><p>{snapshot?.recommended_next_step || 'Review the underlying source records before acting.'}</p><small>Finding snapshot is frozen at case creation. Refresh the report to inspect newer source data.</small></div>
          <div className="case-transition-area"><div><ShellLabel>UPDATE YOUR WORKFLOW</ShellLabel><p>Choose the next state that reflects what you have actually done.</p></div><div className="case-transition-actions">{nextStatuses[selected.status].map((status) => <button key={status} disabled={busy} className={status === 'CLOSED' ? 'case-transition-secondary' : 'case-transition-primary'} onClick={() => onTransition(status)}>{status === 'WAITING_EXTERNAL' ? 'I sent it manually' : status === 'RESOLVED' ? 'Mark resolved' : statusLabel[status]}</button>)}</div></div>
          <div className="case-timeline-head"><div><ShellLabel>IMMUTABLE HISTORY</ShellLabel><h3>What changed</h3></div><span>{selected.events.length} events</span></div>
          <ol className="case-timeline">{selected.events.map((item) => <li key={item.id}><span className="timeline-marker" /><div><div className="timeline-event-top"><strong>{item.event_type === 'CASE_OPENED' ? 'Case opened' : `${statusLabel[item.to_status]}`}</strong><time>{new Date(item.created_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}</time></div>{item.note && <p>{item.note}</p>}<small>Event {item.event_sequence} · {item.from_status ? `${statusLabel[item.from_status]} → ` : ''}{statusLabel[item.to_status]}</small></div></li>)}</ol>
          <div className="casebook-safety-foot">{mode === 'demo' ? 'SYNTHETIC DEMONSTRATION · Local browser state only. No API records are created.' : 'PRIVATE ACCOUNT · Changes are saved to your authenticated account. External actions are not performed.'}</div>
        </>}
      </section>
    </div>
  </>;
}

function Metric({ label, value, sub, tone = 'normal' }: { label: string; value: string; sub: string; tone?: 'normal' | 'positive' | 'negative' }) {
  return <div className={`metric metric--${tone}`}><span className="metric-label">{label}</span><strong>{value}</strong><small>{sub}</small></div>;
}

function CashflowChart({ report }: { report: PowerReport }) {
  const income = visualNumber(report.income_total);
  const spend = visualNumber(report.net_expenses_after_refunds);
  const data = modeChartData(report);
  const max = Math.max(...data.flatMap((item) => [item.income, item.spend]), 1);
  const h = 146;
  const base = 156;
  const barWidth = 34;
  const gap = 48;
  return (
    <div className="chart-wrap">
      <svg viewBox="0 0 520 184" className="cashflow-chart" role="img" aria-label={`Classified inflow ${inr(income)}, net outflow ${inr(spend)}`}>
        {[28, 68, 108, 148].map((y) => <line key={y} x1="20" x2="506" y1={y} y2={y} className="chart-gridline" />)}
        {data.map((item, index) => {
          const x = 44 + index * (barWidth * 2 + gap);
          const incH = (item.income / max) * h;
          const spendH = (item.spend / max) * h;
          return <g key={item.month}>
            <rect x={x} y={base - incH} width={barWidth} height={incH} rx="5" className="chart-income" />
            <rect x={x + barWidth + 8} y={base - spendH} width={barWidth} height={spendH} rx="5" className="chart-spend" />
            <text x={x + barWidth + 4} y="178" textAnchor="middle" className="chart-label">{item.month}</text>
          </g>;
        })}
      </svg>
      <div className="chart-current"><span>SELECTED PERIOD</span><strong>{inr(report.net_cashflow)}</strong><small>Net cashflow</small></div>
    </div>
  );
}

function modeChartData(report: PowerReport) {
  if (report === demoReport || report.report_version === 'personal-power-v1') return demoMonthly;
  const income = visualNumber(report.income_total);
  const spend = visualNumber(report.net_expenses_after_refunds);
  return [
    { month: 'Inflow', income, spend: 0 },
    { month: 'Outflow', income: 0, spend },
  ];
}

function FindingRow({ finding, onClick }: { finding: Finding; onClick: () => void }) {
  const tone = finding.priority === 'HIGH' ? 'high' : finding.priority === 'MEDIUM' ? 'medium' : 'low';
  return (
    <button className="finding-row" onClick={onClick}>
      <span className={`priority-marker priority-marker--${tone}`} />
      <span className="finding-main"><span className="finding-code">{finding.code.replaceAll('_', ' ')}</span><strong>{finding.title}</strong><small>{finding.explanation}</small></span>
      <span className="finding-amount">{finding.amount ? inr(finding.amount) : 'Review'}</span>
      <span className="finding-arrow">↗</span>
    </button>
  );
}

function StatementImportPanel({ accounts, mode, busy, onCreateAccount, onImportStatement }: {
  accounts: FinancialAccount[]; mode: 'demo' | 'live'; busy: boolean;
  onCreateAccount: (name: string, type: string) => Promise<FinancialAccount>;
  onImportStatement: (accountId: string, file: File) => Promise<void>;
}) {
  const inrAccounts = accounts.filter((account) => account.currency === 'INR' && account.status === 'ACTIVE');
  const [accountId, setAccountId] = useState('');
  const [accountName, setAccountName] = useState('Everyday account');
  const [accountType, setAccountType] = useState('BANK_DEPOSIT');
  const [file, setFile] = useState<File | null>(null);
  const [localBusy, setLocalBusy] = useState(false);
  const [localError, setLocalError] = useState('');
  const selectedAccount = inrAccounts.find((account) => account.id === accountId) || inrAccounts[0];

  const createAccount = async () => {
    setLocalBusy(true); setLocalError('');
    try {
      const account = await onCreateAccount(accountName.trim(), accountType);
      setAccountId(account.id);
    } catch (cause) {
      setLocalError(cause instanceof Error ? cause.message : 'Account could not be created.');
    } finally {
      setLocalBusy(false);
    }
  };

  const importFile = async () => {
    if (!selectedAccount || !file) return;
    setLocalBusy(true); setLocalError('');
    try {
      await onImportStatement(selectedAccount.id, file);
      setFile(null);
    } catch (cause) {
      setLocalError(cause instanceof Error ? cause.message : 'Statement import failed.');
    } finally {
      setLocalBusy(false);
    }
  };

  if (mode === 'demo') {
    return <section className="import-panel import-panel--demo"><div><ShellLabel>START WITH YOUR OWN RECORDS</ShellLabel><h2>Bring a statement into your private workspace.</h2><p>The demo uses linked synthetic data. Connect a local verified account to create a personal account and import a CSV through the real financial data service.</p></div><div className="import-panel__right"><span className="fixture-label">SYNTHETIC DEMO ACTIVE</span><small>No sample records are being sent to a bank or provider.</small></div></section>;
  }

  return <section className="import-panel"><div className="import-panel__copy"><ShellLabel>YOUR FINANCIAL DATA</ShellLabel><h2>Import a statement</h2><p>CSV is parsed and stored through the authenticated data service. Each import is idempotent. Credits without an explicit treatment are excluded from cashflow until classified.</p><div className="import-schema-note"><strong>Accepted columns</strong><code>date, amount, direction, cashflow_treatment, category, description, status</code><small>Required: date, amount and direction. A missing treatment defaults to IGNORE. Only import statements you are authorized to use.</small></div></div><div className="import-panel__form">
    {inrAccounts.length === 0 ? <div className="account-create-row"><label><span>ACCOUNT NAME</span><input value={accountName} onChange={(event) => setAccountName(event.target.value)} maxLength={100} /></label><label><span>ACCOUNT TYPE</span><select value={accountType} onChange={(event) => setAccountType(event.target.value)}><option value="BANK_DEPOSIT">Bank deposit</option><option value="CREDIT_CARD">Credit card</option><option value="UPI_WALLET">UPI wallet</option><option value="CASH">Cash</option><option value="OTHER">Other</option></select></label><button className="secondary-button" disabled={busy || localBusy || !accountName.trim()} onClick={createAccount}>{localBusy ? 'Creating…' : 'Create INR account'}</button></div> : <label className="account-select"><span>IMPORT INTO</span><select value={selectedAccount?.id || ''} onChange={(event) => setAccountId(event.target.value)}>{inrAccounts.map((account) => <option key={account.id} value={account.id}>{account.account_name} · {account.account_type.replaceAll('_', ' ')}</option>)}</select></label>}
    <label className="file-select"><span>CSV STATEMENT</span><input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0] || null)} /><small>{file ? `${file.name} · ${(file.size / 1024).toFixed(1)} KB` : 'UTF-8 CSV · up to 2 MB · 10,000 rows'}</small></label>
    <button className="primary-button" disabled={!selectedAccount || !file || busy || localBusy} onClick={importFile}>{localBusy || busy ? 'Importing…' : 'Import statement'} <span>↗</span></button>
    <small className="import-boundary">Required columns: date, amount, direction. Add cashflow_treatment to classify credits and expenses; otherwise rows default to IGNORE. No bank connection is created.</small>
    {localError && <span className="import-error">{localError}</span>}
  </div></section>;
}

function ProtectionPage({ cases, mode, onAI }: { cases: GuardianCase[]; mode: 'demo' | 'live'; onAI: () => void }) {
  return (
    <>
      <section className="page-intro"><div><ShellLabel>GUARDIAN · ECONOMIC DEFENCE</ShellLabel><h1>Protection starts<br /><em>with the evidence.</em></h1><p>Review billing signals, documents and commitments before deciding what to do next.</p></div><div className="intro-callout"><span>HUMAN CONTROL</span><strong>No complaint is sent automatically.</strong><small>Every external step remains under your approval.</small></div></section>
      <div className="protection-status"><div><StatusDot tone="amber" /><span>DOCUMENT TRUST PIPELINE</span><strong>Quarantine & malware scanning are not yet active.</strong></div><p>Uploaded evidence remains <code>STORED_UNSCANNED</code>. This workspace does not run OCR or model extraction until a real scanner and parser sandbox are connected.</p></div>
      <div className="section-heading"><div><ShellLabel>YOUR CASES</ShellLabel><h2>Evidence under review</h2></div><span className="muted-meta">{cases.length} {mode === 'demo' ? 'synthetic cases' : 'private cases'}</span></div>
      <div className="case-list">{cases.length === 0 ? <div className="empty-state">No Guardian cases are attached to this account yet. Import a statement or add an invoice after the document-safety pipeline is enabled.</div> : cases.map((item) => <article className="case-row" key={item.id}><div className="case-date">{dateLabel(item.issue_date)}</div><div className="case-main"><span className="finding-code">{item.case_type.replaceAll('_', ' ')}</span><h3>{item.invoice_id || item.provider_key}</h3><p>{item.findings[0]?.message || 'No findings recorded.'}</p><small>{item.disclaimer}</small></div><div className="case-status"><span className={`case-disposition case-disposition--${item.disposition.toLowerCase()}`}>{item.disposition.replaceAll('_', ' ')}</span><small>{item.status.replaceAll('_', ' ')}</small></div></article>)}</div>
      <div className="bottom-note"><span>01 / 03</span><div><strong>Document intelligence will be evidence-led.</strong><p>Muse models can propose extracted fields. SHA-256, source spans, deterministic arithmetic and human verification must decide whether a field can be trusted.</p></div><button className="text-action" onClick={onAI}>View Meta AI pipeline ↗</button></div>
    </>
  );
}

function OpportunityPage({ mode }: { mode: 'demo' | 'live' }) {
  return <>
    <section className="page-intro"><div><ShellLabel>OPPORTUNITY ENGINE</ShellLabel><h1>Turn what you know<br /><em>into what you earn.</em></h1><p>Connect skills, experience, available time and tools to real demand. Rank the work by net income, not headline pay.</p></div><div className="intro-callout"><span>PERSONAL FIRST</span><strong>No Commons membership required.</strong><small>One person can discover an opportunity on their own.</small></div></section>
    <div className="capability-banner"><span>CAPABILITY GRAPH</span><strong>Skills → proof → available time → verified demand → net value</strong><small>{mode === 'demo' ? 'Synthetic persona profile · demonstration only' : 'This account does not yet have a persisted opportunity profile.'}</small></div>
    <div className="opportunity-layout"><div><ShellLabel>DEMO MATCHES</ShellLabel><h2>Possible ways to create income</h2><article className="opportunity-item"><div className="opportunity-tag">REMOTE · FLEXIBLE HOURS</div><h3>Weekend mathematics tutoring</h3><p>Two 90-minute sessions per week match the available evening hours in the synthetic profile.</p><div className="opportunity-data"><span>Gross fee <strong>₹2,400 / month</strong></span><span>Travel & materials <strong>₹0</strong></span><span>Net before tax <strong>₹2,400</strong></span></div><span className="fixture-label">SIMULATED DEMAND · NOT A LIVE CLIENT REQUEST</span></article><article className="opportunity-item"><div className="opportunity-tag">LOCAL · PROJECT</div><h3>Product photography for a small seller</h3><p>The portfolio evidence is incomplete. AwnNORA asks for samples before recommending a proposal.</p><div className="opportunity-data"><span>Potential fee <strong>₹1,800</strong></span><span>Direct costs <strong>₹450</strong></span><span>Net before tax <strong>₹1,350</strong></span></div><span className="fixture-label">SIMULATED BRIEF · NEEDS PORTFOLIO PROOF</span></article></div><aside className="rules-panel"><ShellLabel>MATCHING RULES</ShellLabel><h3>Good work must fit your life.</h3><ul><li>Skill evidence is visible, not assumed.</li><li>Time, travel, materials and platform fees are deducted.</li><li>Unsafe terms and incompatible schedules are rejected.</li><li>Your profile is never sent to an employer without your approval.</li></ul><div className="rules-foot">CURRENT STATUS <strong>Designed + synthetic fixtures</strong></div></aside></div>
  </>;
}

function EntitlementsPage({ mode }: { mode: 'demo' | 'live' }) {
  return <>
    <section className="page-intro"><div><ShellLabel>ENTITLEMENT ENGINE</ShellLabel><h1>Find what you may<br /><em>already be entitled to.</em></h1><p>Scholarships, reimbursements, subsidies and claims should be grounded in current authoritative rules.</p></div><div className="intro-callout"><span>NO FALSE AWARDS</span><strong>A possible match is not an approval.</strong><small>Official confirmation remains with the responsible institution.</small></div></section>
    <div className="source-warning"><strong>Source freshness is a hard gate.</strong><span>Every scheme must carry its issuing authority, jurisdiction, source version, last checked date and evidence for each rule. Stale or incomplete sources cause the engine to abstain.</span></div>
    <div className="entitlement-table"><div className="table-head"><span>PROGRAMME / ROUTE</span><span>WHAT IS KNOWN</span><span>STATUS</span></div><div className="entitlement-row"><div><strong>Education fee assistance</strong><small>DEMO STATE SCHEME · synthetic</small></div><div>Potential fit; income proof and enrollment evidence missing.</div><span className="status-word status-word--amber">Evidence needed</span></div><div className="entitlement-row"><div><strong>Employer reimbursement</strong><small>DEMO EMPLOYER BENEFIT · synthetic</small></div><div>Deadline in the fixture is approaching; receipt and manager approval are required.</div><span className="status-word status-word--amber">Prepare checklist</span></div><div className="entitlement-row"><div><strong>Insurance claim pathway</strong><small>DEMO POLICY · synthetic</small></div><div>Incident evidence and policy coverage must be reviewed.</div><span className="status-word">Not assessed</span></div></div>
    <p className="muted-disclaimer">{mode === 'demo' ? 'All programme names and eligibility facts in this screen are synthetic illustrations, not current official offers.' : 'No authoritative benefits source is currently connected to this account.'}</p>
  </>;
}

function EnterprisePage({ cost, setCost, time, setTime, packaging, setPackaging, delivery, setDelivery, price, setPrice, mode }: {
  cost: string; setCost: (v: string) => void; time: string; setTime: (v: string) => void; packaging: string; setPackaging: (v: string) => void;
  delivery: string; setDelivery: (v: string) => void; price: string; setPrice: (v: string) => void; mode: 'demo' | 'live';
}) {
  const fullCost = toPaise(cost) + toPaise(time) + toPaise(packaging) + toPaise(delivery);
  const contribution = toPaise(price) - fullCost;
  const margin = toPaise(price) > 0n ? Number((contribution * 10000n) / toPaise(price)) / 100 : 0;
  return <>
    <section className="page-intro"><div><ShellLabel>ONE-PERSON ENTERPRISE</ShellLabel><h1>Your work deserves<br /><em>a real back office.</em></h1><p>Understand the full cost of making and delivering something before you commit to a price.</p></div><div className="intro-callout"><span>UNIT ECONOMICS</span><strong>Price above full cost.</strong><small>Materials are only one part of what your work costs.</small></div></section>
    <div className="enterprise-layout"><section className="calculator-panel"><ShellLabel>PRODUCT / SERVICE COST BUILDER</ShellLabel><h2>Build a fair price</h2><p className="panel-intro">Example: a small made-to-order product. Change the figures to test the economics.</p><div className="cost-inputs"><MoneyInput label="Materials & ingredients" value={cost} onChange={setCost} /><MoneyInput label="Your labour value" value={time} onChange={setTime} /><MoneyInput label="Packaging" value={packaging} onChange={setPackaging} /><MoneyInput label="Delivery & platform" value={delivery} onChange={setDelivery} /><MoneyInput label="Customer price" value={price} onChange={setPrice} /></div><div className="fixture-label">{mode === 'demo' ? 'LOCAL SYNTHETIC EXAMPLE · NOT A LIVE ORDER' : 'LOCAL CALCULATION · NOT A POSTED BUSINESS RECORD'}</div></section><aside className="economics-result"><ShellLabel>PRICE CHECK</ShellLabel><div className="economics-total"><span>Full cost per unit</span><strong>{inr(fullCost)}</strong></div><div className="economics-total economics-total--strong"><span>Contribution after listed costs</span><strong className={contribution >= 0n ? 'good-text' : 'bad-text'}>{inr(contribution)}</strong></div><div className="margin-track"><span style={{ width: `${Math.max(0, Math.min(100, margin))}%` }} /></div><div className="margin-label"><span>Contribution margin</span><strong>{Number.isFinite(margin) ? `${margin.toFixed(1)}%` : 'n/a'}</strong></div><div className={`price-verdict ${contribution > 0n ? 'price-verdict--good' : 'price-verdict--bad'}`}>{contribution > 0n ? 'This price is above the listed costs.' : 'This price does not cover the listed costs.'}</div><small>Tax, wastage, returns, equipment depreciation and overhead are not yet included.</small></aside></div>
  </>;
}

function MoneyInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="money-input"><span>{label}</span><div><i>₹</i><input type="text" inputMode="decimal" pattern="[0-9]{1,12}([.][0-9]{1,2})?" value={value} onChange={(e) => onChange(e.target.value)} aria-label={label} /></div></label>;
}

function CommonsPage({ mode }: { mode: 'demo' | 'live' }) {
  const [joined, setJoined] = useState(false);
  return <>
    <section className="page-intro"><div><ShellLabel>COMMONS · COLLECTIVE ECONOMIC INTELLIGENCE</ShellLabel><h1>Private people.<br /><em>Collective leverage.</em></h1><p>When people choose to combine a narrow need, they can create bargaining power without exposing the records behind it.</p></div><div className="intro-callout"><span>OPTIONAL BY DESIGN</span><strong>Personal Mode works alone.</strong><small>Commons is an additional, revocable choice.</small></div></section>
    <div className="commons-layout"><section className="commons-campaign"><div className="campaign-label">SYNTHETIC CAMPAIGN · EDUCATION SUPPLIES</div><h2>Shared demand can improve the terms.</h2><p>Five fictional households contribute only a broad service category, quantity band and location cluster. No account statements, names or exact incomes are shared.</p><div className="quorum-block"><div className="quorum-top"><span>DEMO QUORUM</span><strong>5 / 5</strong></div><div className="quorum-track"><span /></div><small>Example quorum reached in a simulated dataset. This is not a live supplier quote or confirmed discount.</small></div><div className="campaign-economics"><span>Candidate net benefit <strong>₹340</strong></span><span>Direct discount goes to users <strong>100%</strong></span><span>External settlement <strong>Not performed</strong></span></div><button className={`primary-button ${joined ? 'primary-button--confirmed' : ''}`} onClick={() => setJoined((v) => !v)}>{joined ? 'Demo preference recorded locally' : 'Preview a consented contribution'} <span>↗</span></button><small className="local-only">{joined ? 'This control only changes the local demonstration state. No consent record was created.' : 'This is a local interaction only, not a persistent Commons opt-in.'}</small></section><aside className="commons-principles"><ShellLabel>THE PRIVACY CONTRACT</ShellLabel><h3>What stays private</h3><ul><li>Bank statements and raw transaction records</li><li>Names, contact details and identity documents</li><li>Household-specific financial difficulty</li><li>Personal evidence and private knowledge graph edges</li></ul><div className="aside-divider" /><h3>What may be shared</h3><ul><li>Purpose-approved demand categories</li><li>Broad locality and quantity bands</li><li>Only with active consent at event time</li></ul><div className="commons-alert">A minimum cohort is not a mathematical privacy guarantee. Differencing, rare groups and repeated queries must also be controlled.</div></aside></div>
    <p className="muted-disclaimer">{mode === 'demo' ? 'Everything on this page is simulated. No supplier, sponsor, household or payment system was contacted.' : 'Commons participation is not yet connected to a persistent exchange service in this API.'}</p>
  </>;
}

function IntelligencePage({ mode, session, aiConsent, setAiOptIn, aiOptIn, grantConsent, revokeConsent, question, setQuestion, askMeta, aiResult, busy }: {
  mode: 'demo' | 'live'; session: Session | null; aiConsent: boolean; setAiOptIn: (v: boolean) => void; aiOptIn: boolean;
  grantConsent: () => void; revokeConsent: () => void; question: AIQuestion; setQuestion: (v: AIQuestion) => void; askMeta: () => void; aiResult: AIExplanation | null; busy: boolean;
}) {
  return <>
    <section className="page-intro"><div><ShellLabel>THE INTELLIGENCE LAYER</ShellLabel><h1>AI that understands.<br /><em>Systems that verify.</em></h1><p>Meta models interpret complex information and propose structured next steps. AwnNORA's deterministic kernel protects money, permissions and outcomes.</p></div><div className="intro-callout"><span>MODEL POLICY</span><strong>Standard mode only for personal context.</strong><small>Contributor mode is not permitted for personal or confidential data.</small></div></section>
    <div className="model-grid">
      <ModelRow name="Muse Spark 1.3" role="Reasoning, task decomposition and structured explanations" status="Server-key gated" detail="The Standard-mode explanation endpoint is implemented. A server-side MODEL_API_KEY and the user's separate consent are required for a real call." />
      <ModelRow name="Muse Wonder 1.0" role="Long-running mission planning and multi-agent delegation" status="GENIEA target" detail="Reserve for complex durable missions after mission checkpoints, tool permissions and reconciliation are implemented." />
      <ModelRow name="Muse Glimmer" role="Local multimodal reasoning for private or edge deployments" status="Open-weight target" detail="A self-hosted 30B model. Hardware and latency must be benchmarked before enabling it." />
      <ModelRow name="Muse Voice Transcribe" role="Voice-first intake and user clarification" status="Integration target" detail="Streaming transcription with speaker turns. It transcribes; it does not generate speech." />
      <ModelRow name="SAM 3.1" role="Visual regions for physical resource and product workflows" status="Integration target" detail="Returns segmentation boxes and masks for images and video; it is not an OCR replacement." />
    </div>
    <div className="ai-workspace">
      <div className="ai-workspace__intro"><ShellLabel>PERSONAL REPORT ASSISTANCE</ShellLabel><h2>Ask for an explanation, not a decision.</h2><p>Muse Spark can explain findings already produced by AwnNORA. The model cannot change your records, calculate a settlement, approve a claim or execute an action.</p></div>
      {mode === 'demo' ? <div className="ai-gate"><span className="gate-number">01</span><div><strong>Connect a local demo account to try the Meta API.</strong><p>The standalone synthetic interface does not send its example data to Meta and does not pretend a model was called.</p></div></div> : !session ? <div className="ai-gate"><span className="gate-number">02</span><div><strong>Sign in to a verified account.</strong><p>AI assistance is only available through the authenticated backend.</p></div></div> : !aiConsent ? <div className="consent-gate"><div><span className="gate-number">03</span><div><strong>Optional consent: share minimized financial aggregates and obligation totals with Meta Model API.</strong><p>The service sends aggregate financial totals, essential-obligation totals and genericized finding labels only. It does not send transaction rows, names, account IDs, payee labels, contact information or uploaded documents. The Meta Model API processes the request in Standard mode. This is separate from the consent to use AwnNORA itself.</p></div></div><label className="consent-check"><input type="checkbox" checked={aiOptIn} onChange={(e) => setAiOptIn(e.target.checked)} /><span>I agree to this optional, purpose-specific AI processing.</span></label><button className="primary-button" disabled={!aiOptIn || busy} onClick={grantConsent}>{busy ? 'Saving…' : 'Grant optional AI consent'} <span>↗</span></button></div> : <div className="ai-form"><div className="consent-active"><StatusDot /><span>AI ASSISTANCE CONSENT ACTIVE</span><small>Aggregate summary only · Standard mode</small><button className="text-action consent-revoke" disabled={busy} onClick={revokeConsent}>Revoke consent</button></div><label className="question-label" htmlFor="ai-question">Choose what the model should explain</label><select id="ai-question" value={question} onChange={(e) => setQuestion(e.target.value as AIQuestion)}><option value="prioritize_findings">Prioritize findings and evidence checks</option><option value="explain_cashflow">Explain this period's cashflow</option><option value="review_obligations">Review upcoming obligations</option><option value="understand_data_gaps">Explain missing or incomplete data</option></select><div className="ai-form-footer"><small>Model: Muse Spark 1.3 · Standard mode · No tools or external mutations enabled</small><button className="primary-button" disabled={!question.trim() || busy} onClick={askMeta}>{busy ? 'Thinking…' : 'Ask Muse Spark'} <span>↗</span></button></div>{aiResult && <div className="ai-result"><div className="ai-result__header"><strong>Structured explanation</strong><span>{aiResult.model} · {aiResult.mode}</span></div><p>{aiResult.summary}</p>{aiResult.actions.map((action) => <div className="ai-action" key={action.finding_id}><span>{action.finding_id}</span><strong>{action.why_it_matters}</strong><p>{action.next_step}</p><small>Uncertainty: {action.uncertainty}</small></div>)}<div className="model-disclaimer">{aiResult.limitations.join(' ')} {aiResult.external_actions_taken ? 'External actions were taken.' : 'No external action was taken.'}</div></div>}</div>}
    </div>
    <div className="intelligence-boundary"><strong>Decision boundary</strong><span>Model proposes language and prioritization.</span><b>→</b><span>Application checks allowed finding IDs and consent.</span><b>→</b><span>Deterministic code owns calculations and all external state changes.</span></div>
  </>;
}

function ModelRow({ name, role, status, detail }: { name: string; role: string; status: string; detail: string }) {
  return <div className="model-row"><div className="model-monogram">{name.split(' ').map((part) => part[0]).slice(0, 2).join('')}</div><div className="model-copy"><strong>{name}</strong><span>{role}</span><small>{detail}</small></div><span className="model-status">{status}</span></div>;
}

function LoginDialog({ busy, onClose, onLogin, onConnected }: {
  busy: boolean;
  onClose: () => void;
  onLogin: (email: string, password: string) => void;
  onConnected: (session: Session) => void;
}) {
  const [step, setStep] = useState<'signin' | 'register' | 'verify'>('signin');
  const [email, setEmail] = useState('awnnora-demo-01@example.invalid');
  const [displayName, setDisplayName] = useState('AwnNORA Demo User');
  const [password, setPassword] = useState('');
  const [verificationToken, setVerificationToken] = useState('');
  const [pendingSession, setPendingSession] = useState<Session | null>(null);
  const [localBusy, setLocalBusy] = useState(false);
  const [localError, setLocalError] = useState('');
  const [localNotice, setLocalNotice] = useState('');

  const register = async () => {
    setLocalBusy(true); setLocalError(''); setLocalNotice('');
    try {
      const result = await api.register(email.trim(), password, displayName.trim());
      setPendingSession(result);
      setStep('verify');
      setLocalNotice('Account created. Enter the one-time email verification token sent by your configured email adapter.');
    } catch (cause) {
      setLocalError(cause instanceof Error ? cause.message : 'Account registration failed.');
    } finally {
      setLocalBusy(false);
    }
  };

  const verify = async () => {
    if (!pendingSession) return;
    setLocalBusy(true); setLocalError('');
    try {
      await api.verifyEmail(verificationToken.trim());
      const verifiedUser = await api.me(pendingSession.access_token);
      onConnected({ ...pendingSession, user: verifiedUser });
    } catch (cause) {
      setLocalError(cause instanceof Error ? cause.message : 'Email verification failed.');
    } finally {
      setLocalBusy(false);
    }
  };

  return <div className="dialog-backdrop" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
    <section className="login-dialog" role="dialog" aria-modal="true" aria-labelledby="login-title">
      <button className="dialog-close" onClick={onClose} aria-label="Close">×</button>
      <Mark />
      <ShellLabel>{step === 'verify' ? 'EMAIL CONTROL' : 'PRIVATE ACCOUNT CONNECTION'}</ShellLabel>
      <h2 id="login-title">{step === 'verify' ? <>Verify your<br /><em>email address.</em></> : <>Your personal<br /><em>economic space.</em></>}</h2>
      <p>{step === 'verify' ? 'Enter the one-time verification token delivered to the address you registered.' : 'Your account is private by default. Credentials are sent only to your configured AwnNORA API.'}</p>
      {localNotice && <div className="dialog-notice">{localNotice}</div>}
      {localError && <div className="dialog-error" role="alert">{localError}</div>}

      {step === 'verify' ? <form onSubmit={(e) => { e.preventDefault(); void verify(); }}>
        <label>Verification token<input type="text" required minLength={32} maxLength={128} value={verificationToken} onChange={(e) => setVerificationToken(e.target.value)} autoComplete="one-time-code" /></label>
        <button className="primary-button primary-button--full" disabled={localBusy}>{localBusy ? 'Verifying…' : 'Verify and continue'} <span>↗</span></button>
        <button type="button" className="text-action dialog-back" onClick={() => setStep('signin')}>Back to sign in</button>
      </form> : <>
        <div className="dialog-tabs"><button type="button" className={step === 'signin' ? 'is-active' : ''} onClick={() => { setStep('signin'); setLocalError(''); }}>Sign in</button><button type="button" className={step === 'register' ? 'is-active' : ''} onClick={() => { setStep('register'); setLocalError(''); }}>Create account</button></div>
        <form onSubmit={(e) => { e.preventDefault(); if (step === 'signin') onLogin(email.trim(), password); else void register(); }}>
          {step === 'register' && <label>Your name<input type="text" required minLength={1} maxLength={80} value={displayName} onChange={(e) => setDisplayName(e.target.value)} autoComplete="name" /></label>}
          <label>Email<input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" /></label>
          <label>Password<input type="password" required minLength={12} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={step === 'signin' ? 'current-password' : 'new-password'} /></label>
          <button className="primary-button primary-button--full" disabled={busy || localBusy}>{busy || localBusy ? 'Connecting…' : step === 'signin' ? 'Sign in' : 'Create private account'} <span>↗</span></button>
        </form>
        <div className="login-footnote">For the synthetic first-user demo, use a dedicated `@example.invalid` email and follow `docs/transfer/FIRST_USER_RUNBOOK.md` to seed its fictional financial persona. With the development email adapter, the verification token appears in the API console.</div>
      </>}
    </section>
  </div>;
}

export default App;

// AWNNORA_ITERATION_06_CASEBOOK: integrated Personal Casebook view, case actions and API-backed transitions.
