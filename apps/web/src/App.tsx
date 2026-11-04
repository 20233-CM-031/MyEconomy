import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from './api';
import {
  appleKeynoteScenes,
  countryConfigs,
  demoAdSenseStream,
  demoCases,
  demoCommonsCampaigns,
  demoConnectedRails,
  demoEntitlements,
  demoInitialAIMessages,
  demoLiveEvents,
  demoMonthly,
  demoObligations,
  demoOpportunities,
  demoPersonalCases,
  demoReport,
} from './demo';
import type {
  AdSenseMonetizationStream,
  AIAssistantMessage,
  AIExplanation,
  AIQuestion,
  CommonsCampaign,
  ConnectedRail,
  CountryCode,
  CountryConfig,
  FinancialAccount,
  Finding,
  GuardianCase,
  LiveEconomicEvent,
  LiveEntitlement,
  LiveOpportunity,
  PersonalCase,
  PersonalCaseDetail,
  PersonalCaseStatus,
  PowerReport,
  RailType,
  Session,
  ViewKey,
} from './types';

const nav: Array<{ id: ViewKey; label: string; eyebrow?: string }> = [
  { id: 'intro', label: 'Vision & About', eyebrow: 'THE PRODUCT' },
  { id: 'tour', label: 'Automated Demo', eyebrow: 'END-TO-END' },
  { id: 'auth', label: 'Login & Security', eyebrow: 'REAL ACCESS' },
  { id: 'assistant', label: 'AI Navigator', eyebrow: 'AUTONOMOUS' },
  { id: 'accounts', label: 'Accounts & Rails', eyebrow: 'MULTI-CONNECT' },
  { id: 'overview', label: 'Your position' },
  { id: 'casebook', label: 'Action Casebook' },
  { id: 'protection', label: 'Guardian Shield' },
  { id: 'opportunity', label: 'Opportunity Hub' },
  { id: 'entitlements', label: 'Entitlements & Grants' },
  { id: 'enterprise', label: 'Solo Enterprise' },
  { id: 'commons', label: 'Collective Commons' },
  { id: 'intelligence', label: 'AI Intelligence' },
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
const visualNumber = (value: string | number | null | undefined) => Number(value ?? 0);
const localToday = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
};
const dateLabel = (date: string) =>
  new Date(`${date}T12:00:00`).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
const percent = (a: number, b: number) => (b > 0 ? Math.max(0, Math.min(100, (a / b) * 100)) : 0);

function Mark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span>A</span>
      <i />
    </div>
  );
}

function StatusDot({ tone = 'green' }: { tone?: 'green' | 'amber' | 'rose' | 'cyan' | 'muted' }) {
  return <span className={`status-dot status-dot--${tone}`} />;
}

function ShellLabel({ children }: { children: React.ReactNode }) {
  return <div className="section-kicker">{children}</div>;
}

function App() {
  const [selectedCountry, setSelectedCountry] = useState<CountryCode>('IN');
  const [countrySelectorModalOpen, setCountrySelectorModalOpen] = useState(false);
  const activeCountry = countryConfigs[selectedCountry] || countryConfigs.IN;
  const [view, setView] = useState<ViewKey>('intro');
  const [mode, setMode] = useState<'demo' | 'live'>('demo');
  const [session, setSession] = useState<Session | null>(null);
  const [report, setReport] = useState<PowerReport>(demoReport);
  const [cases, setCases] = useState<GuardianCase[]>(demoCases);
  const [personalCases, setPersonalCases] = useState<PersonalCase[]>(demoPersonalCases);
  const [selectedPersonalCase, setSelectedPersonalCase] = useState<PersonalCaseDetail | null>(null);
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [rails, setRails] = useState<ConnectedRail[]>(demoConnectedRails);
  const [adsenseStream] = useState<AdSenseMonetizationStream>(demoAdSenseStream);
  const [liveEvents, setLiveEvents] = useState<LiveEconomicEvent[]>(demoLiveEvents);
  const [aiMessages, setAiMessages] = useState<AIAssistantMessage[]>(demoInitialAIMessages);
  const [opportunities, setOpportunities] = useState<LiveOpportunity[]>(demoOpportunities);
  const [entitlements, setEntitlements] = useState<LiveEntitlement[]>(demoEntitlements);
  const [commonsCampaigns, setCommonsCampaigns] = useState<CommonsCampaign[]>(demoCommonsCampaigns);
  const [connectRailModalOpen, setConnectRailModalOpen] = useState(false);

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
    setBusy(true);
    setError('');
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
      const activeAI = consents.find(
        (grant) => grant.purpose === 'ai_assistance' && grant.recipient_id === 'meta-model-api' && grant.status === 'active'
      );
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
    setView('auth');
    setError('');
    setNotice('Connect a verified local account or create a realistic private economic space.');
  };

  const backToDemo = () => {
    setSession(null);
    setMode('demo');
    setReport(demoReport);
    setCases(demoCases);
    setPersonalCases(demoPersonalCases);
    setSelectedPersonalCase(null);
    setAccounts([]);
    setRails(demoConnectedRails);
    setLiveEvents(demoLiveEvents);
    setAiMessages(demoInitialAIMessages);
    setOpportunities(demoOpportunities);
    setEntitlements(demoEntitlements);
    setCommonsCampaigns(demoCommonsCampaigns);
    setAiResult(null);
    setAiConsent(false);
    setAiConsentId(null);
    setNotice('Synthetic demonstration workspace restored.');
    setError('');
  };

  const onLogin = async (email: string, password: string) => {
    setBusy(true);
    setError('');
    try {
      const result = await api.login(email, password);
      if (!result.user.email_verified) throw new Error('Verify this account before using Personal Mode.');
      setSession(result);
      setMode('live');
      setPersonalCases([]);
      setSelectedPersonalCase(null);
      setLoginOpen(false);
      setView('assistant');
      setNotice('Connected. Loading your private economic workspace.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Sign in failed.');
    } finally {
      setBusy(false);
    }
  };

  const launchDemoSession = async () => {
    setBusy(true);
    setError('');
    try {
      const result = await api.demoSession();
      setSession(result);
      setMode('live');
      setPersonalCases([]);
      setSelectedPersonalCase(null);
      setLoginOpen(false);
      setView('assistant');
      setNotice('Instant Verified Demo Account activated! Welcome to AwnNORA.');
    } catch {
      // Fallback to offline demo mode
      backToDemo();
      setView('assistant');
      setNotice('Instant Synthetic Demonstration Workspace activated.');
    } finally {
      setBusy(false);
    }
  };

  const createFinancialAccount = async (accountName: string, accountType: string) => {
    if (!session) throw new Error('Connect a verified account first.');
    setBusy(true);
    setError('');
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
    setBusy(true);
    setError('');
    let committed = false;
    try {
      if (file.size === 0 || file.size > 2 * 1024 * 1024) {
        throw new Error('Choose a non-empty CSV file no larger than 2 MiB.');
      }
      const batch = await api.importStatement(session.access_token, accountId, file);
      committed = true;
      setNotice(
        `Statement import ${batch.status.toLowerCase()}: ${batch.inserted_count} new rows, ${batch.updated_count} updates, ${batch.duplicate_count} duplicates. Refreshing your report.`
      );
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
        const activeAI = consents.find(
          (grant) => grant.purpose === 'ai_assistance' && grant.recipient_id === 'meta-model-api' && grant.status === 'active'
        );
        setAiConsent(Boolean(activeAI));
        setAiConsentId(activeAI?.id ?? null);
        setNotice(
          `Statement import ${batch.status.toLowerCase()} and report refreshed: ${batch.inserted_count} new rows, ${batch.updated_count} updates, ${batch.duplicate_count} duplicates.`
        );
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
    setBusy(true);
    setError('');
    try {
      const grant = (await api.createAIConsent(session.access_token)) as { id: string };
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
    setBusy(true);
    setError('');
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
    setBusy(true);
    setError('');
    setAiResult(null);
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
        events: [
          {
            id: `${id}-E1`,
            event_sequence: 1,
            event_type: 'CASE_OPENED',
            from_status: null,
            to_status: 'OPEN',
            note: 'Opened from a synthetic Personal Power finding. Forensic SHA-256 evidence preserved.',
            created_at: now,
          },
        ],
      };
      setPersonalCases((current) => [nextCase, ...current]);
      setSelectedPersonalCase(nextCase);
      setView('casebook');
      setNotice('Dispute case opened in this browser session. Evidence timeline initialized.');
      return;
    }
    if (!session) {
      setError('Connect a verified account before opening a persistent case.');
      return;
    }
    setBusy(true);
    try {
      const created = await api.createCaseFromFinding(
        session.access_token,
        finding.finding_id,
        periodStart,
        periodEnd,
        asOf
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
    const note =
      toStatus === 'WAITING_EXTERNAL'
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
        events: [
          ...current.events,
          {
            id: `${current.id}-E${nextVersion}`,
            event_sequence: nextVersion,
            event_type: 'STATUS_CHANGED',
            from_status: current.status,
            to_status: toStatus,
            note,
            created_at: now,
          },
        ],
      };
      setSelectedPersonalCase(updated);
      setPersonalCases((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setNotice('Synthetic case state updated locally. Verified value remains unchanged.');
      return;
    }
    if (!session) return;
    setBusy(true);
    setError('');
    try {
      const updated = await api.transitionCase(
        session.access_token,
        current.id,
        toStatus,
        current.state_version,
        note
      );
      setSelectedPersonalCase(updated);
      setPersonalCases((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setNotice('Case timeline saved. No external action was performed.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The case could not be updated. Reload the case before retrying.');
    } finally {
      setBusy(false);
    }
  };

  // Autonomous AI Command Execution Engine
  const handleAISend = (userText: string) => {
    if (!userText.trim()) return;
    const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg: AIAssistantMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      timestamp: nowTime,
      text: userText,
    };

    setAiMessages((prev) => [...prev, userMsg]);
    const lower = userText.toLowerCase();

    setTimeout(() => {
      let reply: AIAssistantMessage;

      if (lower.includes('audit') || lower.includes('duplicate') || lower.includes('netflix') || lower.includes('leak') || lower.includes('spend')) {
        reply = {
          id: `agt-${Date.now()}`,
          sender: 'agent',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `🔍 **Autonomous Audit Complete**: I analyzed transactions across your 9 connected rails (PhonePe, GPay, Paytm, Amazon Pay, HDFC, SBI, Stripe, Axis Bank Card, and Google AdSense).\n\n⚠️ **Flagged Alert**: Detected duplicate subscription debit **₹649** on your Axis Bank Platinum Card for Netflix in the same 48-hour window. I have compiled the statement timestamps, card reference hashes, and evidence snapshot.`,
          actionCard: {
            title: 'Evidence Ready: Duplicate Charge ₹649',
            description: 'Dispute case package prepared. Click to open and preserve this case in your Casebook.',
            actionType: 'OPEN_CASE',
            targetView: 'casebook',
            buttonLabel: '⚡ Open Dispute Case (DUP-001)',
          },
        };
      } else if (lower.includes('adsense') || lower.includes('monetiz') || lower.includes('creator') || lower.includes('youtube') || lower.includes('ad revenue')) {
        reply = {
          id: `agt-${Date.now()}`,
          sender: 'agent',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `📊 **Google AdSense Creator Stream Active**:\nYour verified AdSense publisher stream (**pub-89241029412491**) delivered **₹16,400.00** this month across 340,000 impressions at an average ₹48.24 eCPM.\n\n⚡ **Bill-Offsetting In Effect**: 100% of your upcoming electricity (₹3,200) and high-speed fiber broadband (₹650) bills are completely neutralized by ad revenue before touching your bank balance.`,
          actionCard: {
            title: 'View AdSense & Creator Offset Studio',
            description: 'Inspect live publisher metrics, eCPM trends, and automated utility bill offset rules.',
            actionType: 'NAVIGATE',
            targetView: 'enterprise',
            buttonLabel: '📈 Open AdSense Studio',
          },
        };
      } else if (lower.includes('connect') || lower.includes('bank') || lower.includes('rail') || lower.includes('upi') || lower.includes('account') || lower.includes('card') || lower.includes('stripe') || lower.includes('phonepe') || lower.includes('gpay')) {
        reply = {
          id: `agt-${Date.now()}`,
          sender: 'agent',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `💳 **Multi-Rail Connection Manager**:\nYou currently have **9 connected payment & yield rails** active in your workspace. You can link any additional Indian UPI app (PhonePe, Google Pay, Paytm, Amazon Pay, BHIM), Indian Core Banks via Account Aggregator, Debit/Credit Cards via CoFT, or Global Merchant rails (Stripe, PayPal, AdSense).\n\nEvery connected rail receives real-time Guardian monitoring against rogue debits.`,
          actionCard: {
            title: 'Connect New Financial Rail',
            description: 'Add UPI VPA, Bank Account, ATM Card or Global Payment Rail with instant consent boundaries.',
            actionType: 'CONNECT_RAIL',
            targetView: 'accounts',
            buttonLabel: '➕ Launch Rail Connector',
          },
        };
      } else if (lower.includes('opportunity') || lower.includes('job') || lower.includes('earn') || lower.includes('income') || lower.includes('work') || lower.includes('skill')) {
        reply = {
          id: `agt-${Date.now()}`,
          sender: 'agent',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `💼 **Living Opportunity Discovery**:\nI polled verified registries including **Skill India Digital**, **ONDC Open Network**, and the **Local Jaipur Exchange**.\n\n✨ **Top Matches for Your Profile**:\n1. **Weekend STEM Mathematics Specialist** (Skill India Digital) · **98% Match** · ₹28,000 / month\n2. **Handcrafted Heritage Textile Micro-Storefront** (ONDC Open Network) · **94% Match** · 44% Net Margin\n3. **Neighborhood Electric Delivery Fleet Dispatcher** · **87% Match** · ₹18,200 / month`,
          actionCard: {
            title: 'Explore High-Yield Opportunities',
            description: 'Browse verified gigs and micro-enterprises with net-margin ranking and escrow security.',
            actionType: 'NAVIGATE',
            targetView: 'opportunity',
            buttonLabel: '🚀 Inspect Opportunities Hub',
          },
        };
      } else if (lower.includes('subsid') || lower.includes('grant') || lower.includes('entitlement') || lower.includes('scheme') || lower.includes('surya') || lower.includes('svanidhi')) {
        reply = {
          id: `agt-${Date.now()}`,
          sender: 'agent',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `🏛️ **Entitlements & Benefit Eligibility Verified**:\nBased on your verified economic indicators, I have confirmed your eligibility for:\n\n• **PM Surya Ghar: Muft Bijli Yojana**: ₹78,000 direct subsidy for rooftop solar.\n• **PM-SVANidhi Micro-Business Credit**: ₹20,000 credit @ 7% interest subsidy.\n• **Ayushman Bharat PM-JAY**: ₹5,00,000 active annual family healthcare cover.`,
          actionCard: {
            title: 'Claim Direct Entitlements',
            description: 'Generate your official application packs and digital identity claim certificates.',
            actionType: 'NAVIGATE',
            targetView: 'entitlements',
            buttonLabel: '📜 View Verified Entitlements',
          },
        };
      } else if (lower.includes('enterprise') || lower.includes('price') || lower.includes('margin') || lower.includes('cost') || lower.includes('business')) {
        reply = {
          id: `agt-${Date.now()}`,
          sender: 'agent',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `📈 **Solo Enterprise Unit Economics**:\nI have loaded your pricing model for handcrafted products. At materials of ₹180, labour of ₹90, packaging of ₹25, and delivery of ₹40 (Total unit cost: **₹335**), selling at ₹420 yields a **20.2% contribution margin** (₹85 profit per unit).\n\nAdditionally, factoring in AdSense creator revenue allows subsidizing operational delivery costs.`,
          actionCard: {
            title: 'Optimize Enterprise Margins',
            description: 'Simulate price points, raw material bulk discounts, and break-even sales volume.',
            actionType: 'NAVIGATE',
            targetView: 'enterprise',
            buttonLabel: '📊 Open Solo Enterprise Studio',
          },
        };
      } else if (lower.includes('commons') || lower.includes('solar') || lower.includes('collective') || lower.includes('pool') || lower.includes('discount')) {
        reply = {
          id: `agt-${Date.now()}`,
          sender: 'agent',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `🤝 **Active Collective Commons Alert**:\nThe **Jaipur North Residential Solar Equipment Bulk Order** currently has **9 out of 10 households joined**! Just 1 more participant reaches quorum to unlock a guaranteed **22% bulk purchase discount** (~₹4,200 savings per household).\n\nZero raw banking records are shared—only aggregated demand is pooled.`,
          actionCard: {
            title: 'Join Solar Bulk Order Quorum',
            description: 'Participate in the cohort to reach 10/10 quorum and secure 22% supplier discount.',
            actionType: 'NAVIGATE',
            targetView: 'commons',
            buttonLabel: '⚡ Review Solar Commons Pool',
          },
        };
      } else {
        reply = {
          id: `agt-${Date.now()}`,
          sender: 'agent',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `I understand: "${userText}". As your **AwnNORA Autonomous Economic Agent**, I can actively operate across your workspace:\n\n• **Audit Leaks**: Scan UPI, cards, and bank statements for duplicate debits.\n• **Multi-Account Hub**: Connect PhonePe, Google Pay, Paytm, HDFC, SBI, Stripe, AdSense, and Cards.\n• **Income Opportunities**: Match skills with high-yield gigs on Skill India & ONDC.\n• **Public Subsidies**: Claim PM Surya Ghar (₹78k) or PM-SVANidhi grants.\n• **AdSense Monetization**: Offset utility bills using digital ad streams.\n• **Collective Leverage**: Join neighborhood bulk purchasing quorums for 20-40% savings.`,
          actionCard: {
            title: 'Explore System Capabilities',
            description: 'Choose any workspace module to see live synthetic workflows in action.',
            actionType: 'NAVIGATE',
            targetView: 'accounts',
            buttonLabel: '💳 Manage Payment Rails',
          },
        };
      }

      setAiMessages((prev) => [...prev, reply]);
    }, 400);
  };

  const handleActionCardClick = (card: NonNullable<AIAssistantMessage['actionCard']>) => {
    if (card.actionType === 'OPEN_CASE') {
      const findingCandidate = report.findings.find((f) => f.code === 'POSSIBLE_DUPLICATE_CHARGE') || report.findings[0];
      if (findingCandidate) {
        void openCaseFromFinding(findingCandidate);
      } else {
        setView('casebook');
      }
    } else if (card.actionType === 'CONNECT_RAIL') {
      setView('accounts');
      setConnectRailModalOpen(true);
    } else if (card.actionType === 'NAVIGATE' && card.targetView) {
      setView(card.targetView);
    } else if (card.targetView) {
      setView(card.targetView);
    }
  };

  const handleAddRail = (newRail: ConnectedRail) => {
    setRails((prev) => [newRail, ...prev]);
    setConnectRailModalOpen(false);
    setNotice(`Successfully connected ${newRail.name} (${newRail.masked_identifier}). Autonomous Guardian shield active.`);

    const newEvt: LiveEconomicEvent = {
      id: `evt-${Date.now()}`,
      timestamp: 'Just now',
      engine: 'RAILS',
      title: `${newRail.name} linked successfully`,
      description: `Autonomous validation completed for ${newRail.provider} (${newRail.masked_identifier}). Live balance ${newRail.balance_formatted} indexed.`,
      amount: newRail.balance_formatted,
      tone: 'positive',
      action_label: 'View Rails',
      action_view: 'accounts',
    };
    setLiveEvents((prev) => [newEvt, ...prev]);
  };

  const handleJoinCommons = (campaignId: string) => {
    setCommonsCampaigns((prev) =>
      prev.map((c) => {
        if (c.id === campaignId) {
          const nextJoined = c.participants_joined + 1;
          const reached = nextJoined >= c.target_quorum;
          return {
            ...c,
            participants_joined: nextJoined,
            status: reached ? 'QUORUM_REACHED' : c.status,
          };
        }
        return c;
      })
    );
    setNotice('You joined the collective pool! Quorum reached and supplier discount secured.');
  };

  const outstanding = useMemo(
    () => report.findings.filter((item) => item.priority === 'HIGH' || item.priority === 'MEDIUM'),
    [report]
  );
  const demoMode = mode === 'demo';
  const syntheticAccountCount = accounts.filter((account) => account.source_type === 'SYNTHETIC_FIXTURE').length;
  const hasSyntheticAccountData = syntheticAccountCount > 0;
  const isSyntheticEnvironment = demoMode || hasSyntheticAccountData;
  const environmentLabel = demoMode
    ? 'SYNTHETIC REAL-TIME DEMO'
    : syntheticAccountCount === accounts.length && syntheticAccountCount > 0
      ? 'SYNTHETIC FIXTURE DATA'
      : hasSyntheticAccountData
        ? 'MIXED DATA'
        : 'PRIVATE ACCOUNT';
  const productName = import.meta.env.VITE_PRODUCT_NAME || 'AwnNORA';

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand-lockup" onClick={() => setView('intro')} aria-label="AwnNORA home">
          <Mark />
          <span>
            <strong>{productName}</strong>
            <small>HUMAN ECONOMIC INTELLIGENCE</small>
          </span>
        </button>

        <div className="sidebar-agent-pill">
          <span className="agent-indicator-pulse" />
          <div>
            <strong>GENIEA AGENT</strong>
            <small>Autonomous & Active</small>
          </div>
        </div>

        <div className="sidebar-caption">DISCOVERY & DEMO</div>
        <div className="nav-list" role="navigation" aria-label="Intro and Demo navigation">
          {nav.slice(0, 3).map((item) => (
            <button
              key={item.id}
              className={`nav-item ${view === item.id ? 'is-active' : ''}`}
              onClick={() => setView(item.id)}
            >
              <span className={`nav-glyph nav-glyph--${item.id}`} aria-hidden="true" />
              <div className="nav-label-group">
                <span>{item.label}</span>
                {item.eyebrow && <small className="nav-eyebrow">{item.eyebrow}</small>}
              </div>
            </button>
          ))}
        </div>

        <div className="sidebar-caption">YOUR WORKSPACE</div>
        <div className="nav-list" role="navigation" aria-label="Workspace navigation">
          {nav.slice(3).map((item) => (
            <button
              key={item.id}
              className={`nav-item ${view === item.id ? 'is-active' : ''}`}
              onClick={() => setView(item.id)}
            >
              <span className={`nav-glyph nav-glyph--${item.id}`} aria-hidden="true" />
              <div className="nav-label-group">
                <span>{item.label}</span>
                {item.eyebrow && <small className="nav-eyebrow">{item.eyebrow}</small>}
              </div>
              {item.id === 'accounts' && <small className="nav-count nav-count--cyan">{rails.length}</small>}
              {item.id === 'protection' && outstanding.length > 0 && <small className="nav-count">{outstanding.length}</small>}
              {item.id === 'casebook' && personalCases.length > 0 && <small className="nav-count">{personalCases.length}</small>}
              {item.id === 'commons' && <small className="nav-count nav-count--emerald">9/10</small>}
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
            <div className="privacy-note__top">
              <span className="privacy-symbol" /> PRIVATE BY DEFAULT
            </div>
            <p>Financial truth is deterministic. Zero unsolicited data leaks to external third parties.</p>
            <button onClick={() => setView('commons')}>
              Understand collective commons <span>↗</span>
            </button>
          </div>
          <div className="account-block">
            <div className="avatar">{session?.user.display_name?.slice(0, 1).toUpperCase() || 'A'}</div>
            <div className="account-text">
              <strong>{session?.user.display_name || 'Autonomous Workspace'}</strong>
              <small>{session?.user.email || 'Synthetic Live Mode'}</small>
            </div>
            <button
              className="account-menu"
              aria-label="Account options"
              onClick={() => (session ? setView('intelligence') : setView('auth'))}
            >
              •••
            </button>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <span>AWNNORA SYSTEM</span>
            <i>/</i>
            <strong>{nav.find((item) => item.id === view)?.label || 'System'}</strong>
          </div>
          <div className="topbar-right">
            <button
              className="country-pill-btn"
              onClick={() => setCountrySelectorModalOpen(true)}
              title="Change sovereign regional economic engine"
            >
              <span style={{ fontSize: 16 }}>{activeCountry.flag}</span>
              <span>{activeCountry.name} ({activeCountry.currencySymbol})</span>
              <span style={{ fontSize: 10, opacity: 0.6 }}>▼</span>
            </button>
            <button className="topbar-quick-btn" onClick={() => setView('tour')}>
              <span>▶ Keynote Demo</span>
            </button>
            <div className={`environment-pill ${isSyntheticEnvironment ? 'environment-pill--demo' : 'environment-pill--live'}`}>
              <StatusDot tone={isSyntheticEnvironment ? 'cyan' : 'green'} />
              {environmentLabel}
            </div>
            <div className="system-state">
              <StatusDot tone={apiReady ? 'green' : 'amber'} /> API {apiReady ? 'CONNECTED' : 'STANDALONE READY'}
            </div>
            {session ? (
              <button className="topbar-action" onClick={backToDemo}>
                Return to demo
              </button>
            ) : (
              <button className="topbar-action" onClick={connectLive}>
                Login & Security
              </button>
            )}
          </div>
        </header>

        {/* Real-time Economic Activity Ticker Banner */}
        <LiveEconomicStreamTicker events={liveEvents} onAction={(v) => setView(v)} />

        <div className="page-content">
          {notice && (
            <div className="notice-line">
              <StatusDot tone="green" />
              {notice}
              <button onClick={() => setNotice('')} aria-label="Dismiss notice">
                ×
              </button>
            </div>
          )}
          {mode === 'live' && hasSyntheticAccountData && (
            <div className="data-origin-note" role="status">
              <strong>SYNTHETIC FIXTURE RECORDS</strong>
              <span>
                {syntheticAccountCount === accounts.length
                  ? 'This private account is populated with a fictional test persona. No real bank history or verified financial outcome is represented.'
                  : 'This private account contains both synthetic fixture accounts and other accounts. The synthetic records are excluded from claims of real-world impact.'}
              </span>
            </div>
          )}
          {error && (
            <div className="error-line">
              <span>!</span>
              {error}
              <button onClick={() => setError('')} aria-label="Dismiss error">
                ×
              </button>
            </div>
          )}
          {showHelp && (
            <div className="help-strip">
              <strong>One personal system. Six connected engines.</strong>
              <span>
                MAKOS organizes your cases and decisions. GENIEA coordinates bounded autonomous work. KRN preserves immutable evidence. Deterministic services protect calculations and permissions.
              </span>
              <button onClick={() => setShowHelp(false)}>Close</button>
            </div>
          )}

          {/* VIEW ROUTING */}
          {view === 'intro' && (
            <IntroLandingPage
              activeCountry={activeCountry}
              onSelectCountry={() => setCountrySelectorModalOpen(true)}
              onStartTour={() => setView('tour')}
              onLaunchDemo={launchDemoSession}
              onGoAuth={() => setView('auth')}
              onGoAssistant={() => setView('assistant')}
            />
          )}

          {view === 'tour' && (
            <AppleKeynoteProductLaunchDemo
              activeCountry={activeCountry}
              onSelectCountry={() => setCountrySelectorModalOpen(true)}
              onJumpToFeature={(targetView) => setView(targetView)}
              onFinishTour={() => setView('assistant')}
              onGoAuth={() => setView('auth')}
            />
          )}

          {view === 'auth' && (
            <LoginSecurityPage
              busy={busy}
              session={session}
              onLogin={onLogin}
              onLaunchDemo={launchDemoSession}
              onConnected={(result) => {
                setSession(result);
                setMode('live');
                setPersonalCases([]);
                setSelectedPersonalCase(null);
                setView('assistant');
                setNotice('Account verified! Welcome to your private economic workspace.');
              }}
              onLogout={() => {
                backToDemo();
                setNotice('Signed out. Restored synthetic sandbox.');
              }}
            />
          )}

          {view === 'assistant' && (
            <AssistantPage
              messages={aiMessages}
              onSend={handleAISend}
              onActionCard={handleActionCardClick}
              railsCount={rails.length}
              openFindingsCount={outstanding.length}
              onNavigate={(v) => setView(v)}
            />
          )}

          {view === 'accounts' && (
            <AccountsPage
              rails={rails}
              adsenseStream={adsenseStream}
              onOpenConnectModal={() => setConnectRailModalOpen(true)}
              onReviewLeak={() => {
                const candidate = report.findings.find((f) => f.code === 'POSSIBLE_DUPLICATE_CHARGE') || report.findings[0];
                if (candidate) void openCaseFromFinding(candidate);
                else setView('casebook');
              }}
            />
          )}

          {view === 'overview' && (
            <OverviewPage
              report={report}
              accounts={accounts}
              mode={mode}
              busy={busy}
              outstanding={outstanding}
              onReview={() => setView('protection')}
              onIntelligence={() => setView('intelligence')}
              onRefresh={refreshLive}
              onCreateAccount={createFinancialAccount}
              onOpenCase={openCaseFromFinding}
              onImportStatement={importFinancialStatement}
              periodStart={periodStart}
              periodEnd={periodEnd}
              setPeriodStart={setPeriodStart}
              setPeriodEnd={setPeriodEnd}
              asOf={asOf}
              onOpenAssistant={() => setView('assistant')}
            />
          )}

          {view === 'casebook' && (
            <CasebookPage
              cases={personalCases}
              selectedCase={selectedPersonalCase}
              mode={mode}
              busy={busy}
              onSelect={openPersonalCase}
              onTransition={transitionSelectedCase}
            />
          )}

          {view === 'protection' && <ProtectionPage cases={cases} mode={mode} onAI={() => setView('intelligence')} />}

          {view === 'opportunity' && (
            <OpportunityPage
              opportunities={opportunities}
              mode={mode}
              onApply={(opp) => {
                setNotice(`Application dispatched via Agent for "${opp.title}" at ${opp.source}. Escrow agreement locked.`);
              }}
            />
          )}

          {view === 'entitlements' && (
            <EntitlementsPage
              entitlements={entitlements}
              mode={mode}
              onClaim={(ent) => {
                setNotice(`Claim certificate prepared for ${ent.title} (${ent.scheme_code}). Submitted to ${ent.ministry}.`);
              }}
            />
          )}

          {view === 'enterprise' && (
            <EnterprisePage
              cost={enterpriseCost}
              setCost={setEnterpriseCost}
              time={enterpriseTime}
              setTime={setEnterpriseTime}
              packaging={enterprisePackaging}
              setPackaging={setEnterprisePackaging}
              delivery={enterpriseDelivery}
              setDelivery={setEnterpriseDelivery}
              price={enterprisePrice}
              setPrice={setEnterprisePrice}
              mode={mode}
              adsenseStream={adsenseStream}
            />
          )}

          {view === 'commons' && (
            <CommonsPage
              campaigns={commonsCampaigns}
              mode={mode}
              onJoin={handleJoinCommons}
            />
          )}

          {view === 'intelligence' && (
            <IntelligencePage
              mode={mode}
              session={session}
              aiConsent={aiConsent}
              setAiOptIn={setAiOptIn}
              aiOptIn={aiOptIn}
              grantConsent={grantAIConsent}
              revokeConsent={revokeAIConsent}
              question={aiQuestion}
              setQuestion={setAiQuestion}
              askMeta={askMeta}
              aiResult={aiResult}
              busy={busy}
            />
          )}
        </div>

        <footer className="page-footer">
          <span>AWNNORA · AUTONOMOUS ECONOMIC EMPOWERMENT PLATFORM</span>
          <span>CODE-ENFORCED ACCURACY · DETERMINISTIC CALCULATIONS · HUMAN CONSENT GATES</span>
        </footer>
      </main>

      {connectRailModalOpen && (
        <ConnectRailModal
          activeCountry={activeCountry}
          onClose={() => setConnectRailModalOpen(false)}
          onAddRail={handleAddRail}
        />
      )}

      {countrySelectorModalOpen && (
        <CountrySelectorModal
          selectedCountry={selectedCountry}
          onSelect={(code) => {
            setSelectedCountry(code);
            setCountrySelectorModalOpen(false);
            const cfg = countryConfigs[code];
            setNotice(`Jurisdiction updated to ${cfg.name} (${cfg.currencySymbol} ${cfg.currencyCode}). Banking rails and subsidy registries re-aligned.`);
          }}
          onClose={() => setCountrySelectorModalOpen(false)}
        />
      )}

      {loginOpen && (
        <LoginDialog
          busy={busy}
          onClose={() => {
            setLoginOpen(false);
            if (!session) setMode('demo');
          }}
          onLogin={onLogin}
          onConnected={(result) => {
            setSession(result);
            setMode('live');
            setPersonalCases([]);
            setSelectedPersonalCase(null);
            setLoginOpen(false);
            setView('assistant');
            setNotice('Email verified. Your private workspace is connected.');
          }}
        />
      )}
    </div>
  );
}

// ==========================================
// 1. INTRO & ABOUT PRODUCT LANDING PAGE
// ==========================================
function IntroLandingPage({
  activeCountry,
  onSelectCountry,
  onStartTour,
  onLaunchDemo,
  onGoAuth,
  onGoAssistant,
}: {
  activeCountry: CountryConfig;
  onSelectCountry: () => void;
  onStartTour: () => void;
  onLaunchDemo: () => void;
  onGoAuth: () => void;
  onGoAssistant: () => void;
}) {
  return (
    <div className="intro-page">
      {/* Hero Section */}
      <section className="intro-hero">
        <div className="intro-hero-content">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <div className="intro-badge">
              <span className="intro-badge-dot" />
              <span>AWNNORA SYSTEM ARCHITECTURE · v0.4.0</span>
            </div>
            <button className="country-pill-btn" onClick={onSelectCountry} title="Switch Country Engine">
              <span style={{ fontSize: 16 }}>{activeCountry.flag}</span>
              <strong>{activeCountry.name} ({activeCountry.currencySymbol} {activeCountry.currencyCode})</strong>
              <span style={{ fontSize: 11, color: '#4f46e5', fontWeight: 700 }}>Switch Jurisdiction ▾</span>
            </button>
          </div>
          <h1>
            Economic Agency for the Individual.<br />
            <em>Autonomous Defense &amp; Collective Power.</em>
          </h1>
          <p className="intro-lead">
            The world’s institutions possess sophisticated systems to price, extract, and compound wealth. The individual has a checking account and a prayer. <strong>AwnNORA</strong> bridges this asymmetry: an autonomous economic representative that balances your daily cashflows, halts subscription leakages, transforms skills into high-margin contracts, claims government entitlements, and pools collective buying power—all while keeping your private records strictly yours.
          </p>

          <div className="intro-cta-row">
            <button className="primary-button primary-button--glow" onClick={onStartTour}>
              <span>▶ Play Automated End-to-End Tour</span>
            </button>
            <button className="secondary-button" onClick={onLaunchDemo}>
              <span>⚡ Launch Instant Test Demo Account</span>
            </button>
            <button className="text-action" onClick={onGoAuth}>
              <span>🔐 Security &amp; Banking Connection Proof ↗</span>
            </button>
          </div>
        </div>

        <div className="intro-hero-visual">
          <div className="vision-card">
            <div className="vision-card-header">
              <span className="vision-pill">SYSTEM BALANCE</span>
              <strong className="text-cyan">+₹46,140 Net Cashflow</strong>
            </div>
            <div className="vision-pulse-metrics">
              <div className="pulse-item">
                <small>GUARDIAN SHIELD</small>
                <strong className="text-rose">₹649 Flagged</strong>
                <span>Duplicate Netflix isolated</span>
              </div>
              <div className="pulse-item">
                <small>OPPORTUNITY</small>
                <strong className="text-emerald">₹28,000 / mo</strong>
                <span>Skill India STEM Specialist</span>
              </div>
              <div className="pulse-item">
                <small>COMMONS QUORUM</small>
                <strong className="text-purple">9/10 Joined</strong>
                <span>Jaipur Solar 22% bulk discount</span>
              </div>
              <div className="pulse-item">
                <small>ADSENSE YIELD</small>
                <strong className="text-emerald">₹16,400 / mo</strong>
                <span>Fixed utility bills covered 100%</span>
              </div>
            </div>
            <div className="vision-card-footer">
              <button className="vision-enter-btn" onClick={onGoAssistant}>
                Enter AI Pilot Workspace ↗
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Pillars of Product Vision */}
      <section className="intro-pillars-section">
        <div className="section-heading">
          <div>
            <ShellLabel>THE 4 PILLARS OF ECONOMIC DEFENSE</ShellLabel>
            <h2>How AwnNORA Realistically Balances Your Life</h2>
          </div>
          <span className="muted-meta">Deterministic code + Forensic evidence + Collective leverage</span>
        </div>

        <div className="pillars-grid">
          <div className="pillar-card pillar-card--cyan">
            <div className="pillar-icon">⚖️</div>
            <h3>Deterministic Cashflow Balancing</h3>
            <p>
              Consolidates Indian UPI apps (PhonePe, GPay, Paytm, Amazon Pay), Core Bank deposits (HDFC, SBI), credit cards, and digital monetization streams into a mathematically verified ledger using integer paise arithmetic. Never estimates or hallucinates balances.
            </p>
            <span className="pillar-tag">RBI AA &amp; NPCI Compatible</span>
          </div>

          <div className="pillar-card pillar-card--rose">
            <div className="pillar-icon">🛡️</div>
            <h3>Forensic Guardian Defense</h3>
            <p>
              Isolates silent fee creep, duplicate debits, and ghost subscriptions. Extracts verifiable statement proofs with SHA-256 cryptographic hashing and provisions trackable dispute cases in your MAKOS Casebook without moving money unprompted.
            </p>
            <span className="pillar-tag">Cryptographic Proof Chains</span>
          </div>

          <div className="pillar-card pillar-card--emerald">
            <div className="pillar-icon">💼</div>
            <h3>Opportunities &amp; Real Connections</h3>
            <p>
              Connects directly with verified registries—Skill India Digital and ONDC Open Network. Converts verified capabilities and available hours into high-margin contracts, linking people with local clusters and peer cohorts under guaranteed escrow security.
            </p>
            <span className="pillar-tag">ONDC Beckn Protocol</span>
          </div>

          <div className="pillar-card pillar-card--purple">
            <div className="pillar-icon">🤝</div>
            <h3>Anonymous Collective Commons</h3>
            <p>
              Alone, individuals have zero pricing power against monopolies. In the Commons, households unite aggregated category demand to reach bulk quorums (e.g. 10/10 solar order for 22% off), without ever leaking private bank statements or identities.
            </p>
            <span className="pillar-tag">Differential Privacy Guaranteed</span>
          </div>
        </div>
      </section>

      {/* Financial Support via AdSense & Creator Yield Section */}
      <section className="adsense-vision-section">
        <div className="adsense-vision-content">
          <ShellLabel>FINANCIAL SUPPORT THROUGH MONETIZATION</ShellLabel>
          <h2>How Google AdSense &amp; Creator Yield Insulate Your Life</h2>
          <p>
            AwnNORA uniquely bridges creator economy streams and living balance sheets. By connecting verified Google AdSense publisher accounts (<code>pub-xxxxxxxx</code>), digital ad impressions are classified as zero-tax, high-margin cashflow that automatically offsets essential utility obligations.
          </p>
          <div className="adsense-benefits-grid">
            <div className="adsense-benefit-item">
              <strong>Automated Bill Offsetting</strong>
              <p>AdSense ad payouts directly neutralize upcoming power, high-speed fiber broadband, and cloud hosting bills before touching your bank balance.</p>
            </div>
            <div className="adsense-benefit-item">
              <strong>Community Ad Pooling</strong>
              <p>Neighborhood commons hubs pool micro-sponsorship and digital storefront AdSense yield to fund shared solar battery maintenance and mesh networks.</p>
            </div>
            <div className="adsense-benefit-item">
              <strong>Solo Enterprise Subsidies</strong>
              <p>Artisans and small businesses selling on ONDC offset shipping and packaging costs using digital ad yield to maintain &gt;40% net contribution margins.</p>
            </div>
          </div>
        </div>
        <div className="adsense-vision-card">
          <span className="publisher-tag">VERIFIED PUBLISHER STREAM</span>
          <strong>pub-89241029412491</strong>
          <div className="adsense-stats-row">
            <div>
              <small>MONTHLY YIELD</small>
              <strong className="text-emerald">₹16,400.00</strong>
            </div>
            <div>
              <small>TRAFFIC</small>
              <strong>340k views</strong>
            </div>
            <div>
              <small>EFF. eCPM</small>
              <strong className="text-cyan">₹48.24</strong>
            </div>
          </div>
          <div className="offset-status-box">
            <span className="offset-badge">100% COVERED</span>
            <p>Electricity (₹3,200) + High-Speed Fiber Mesh (₹650) covered by ad revenue.</p>
          </div>
        </div>
      </section>

      {/* Realistic Banking Protocols Architecture */}
      <section className="banking-protocols-section">
        <div className="section-heading">
          <div>
            <ShellLabel>REALISTIC CONNECTION ARCHITECTURE</ShellLabel>
            <h2>How AwnNORA Actually Connects to Real-World Infrastructure</h2>
          </div>
          <span className="muted-meta">Strict adherence to Indian &amp; Global regulatory specifications</span>
        </div>

        <div className="protocol-cards-grid">
          <div className="protocol-card">
            <span className="protocol-number">01</span>
            <strong>India Account Aggregator (AA)</strong>
            <p>Regulated by the Reserve Bank of India (RBI). Connects bank deposit accounts via certified FIPs/FIUs (Sahamati framework) with electronic, time-bound, revocable consent artifacts.</p>
            <small>Supported: HDFC, SBI, ICICI, Axis, PNB</small>
          </div>

          <div className="protocol-card">
            <span className="protocol-number">02</span>
            <strong>NPCI UPI AutoPay &amp; VPA Rails</strong>
            <p>Direct integration with National Payments Corporation of India (NPCI) handle verification protocol. Manages automated recurring mandates across PhonePe, Google Pay, Paytm, and Amazon Pay.</p>
            <small>Supported: @ybl, @okaxis, @okhdfcbank, @paytm</small>
          </div>

          <div className="protocol-card">
            <span className="protocol-number">03</span>
            <strong>RBI Card-on-File Tokenization (CoFT)</strong>
            <p>Zero plain-text 16-digit card numbers or CVVs are ever stored. Replaced with device and merchant network tokens issued by Visa, Mastercard, and RuPay.</p>
            <small>Supported: Platinum Credit, Debit, ATM Cards</small>
          </div>

          <div className="protocol-card">
            <span className="protocol-number">04</span>
            <strong>ONDC &amp; Government Beckn Gateways</strong>
            <p>Decentralized protocol linking users to Open Network for Digital Commerce buyers, Skill India Digital courses, and PM Surya Ghar direct cash transfer gateways.</p>
            <small>Supported: ONDC, Skill India, PM-JAY, PM-SVANidhi</small>
          </div>
        </div>
      </section>

      {/* Final Call to Action */}
      <section className="intro-cta-banner">
        <div>
          <h2>Ready to experience your autonomous economic pilot?</h2>
          <p>Explore the end-to-end interactive demo or launch an immediate test workspace in one click.</p>
        </div>
        <div className="cta-banner-buttons">
          <button className="primary-button primary-button--glow" onClick={onStartTour}>
            <span>Start Interactive Tour ↗</span>
          </button>
          <button className="secondary-button" onClick={onLaunchDemo}>
            <span>Instant Demo Session</span>
          </button>
        </div>
      </section>
    </div>
  );
}

// ==========================================
// 2. AUTOMATED DEMO WALKTHROUGH PLAYER
// ==========================================
function AppleKeynoteProductLaunchDemo({
  activeCountry,
  onSelectCountry,
  onJumpToFeature,
  onFinishTour,
  onGoAuth,
}: {
  activeCountry: CountryConfig;
  onSelectCountry: () => void;
  onJumpToFeature: (view: ViewKey) => void;
  onFinishTour: () => void;
  onGoAuth: () => void;
}) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [speed, setSpeed] = useState<1 | 1.5 | 2>(1);
  const [progress, setProgress] = useState(0);
  const [typedChars, setTypedChars] = useState('');
  const [isClicking, setIsClicking] = useState(false);

  const activeScene = appleKeynoteScenes[currentIdx] || appleKeynoteScenes[0];

  useEffect(() => {
    if (!isPlaying) return;
    const intervalMs = 100;
    const sceneDuration = (7000) / speed;

    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + (intervalMs / sceneDuration) * 100;
        if (next >= 100) {
          setCurrentIdx((c) => (c + 1) % appleKeynoteScenes.length);
          setTypedChars('');
          setIsClicking(false);
          return 0;
        }

        // Simulate operator typing or clicking
        if (activeScene.cursorTarget.action === 'type' && activeScene.cursorTarget.typingInput) {
          const fullText = activeScene.cursorTarget.typingInput;
          const typingProgress = Math.max(0, Math.min(1, (next - 20) / 50));
          const charCount = Math.floor(typingProgress * fullText.length);
          setTypedChars(fullText.slice(0, charCount));
        } else if (activeScene.cursorTarget.action === 'click') {
          if (next >= 40 && next <= 60) {
            setIsClicking(true);
          } else {
            setIsClicking(false);
          }
        }

        return next;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isPlaying, speed, activeScene, currentIdx]);

  const selectScene = (idx: number) => {
    setCurrentIdx(idx);
    setProgress(0);
    setTypedChars('');
    setIsClicking(false);
  };

  const handleNext = () => {
    setCurrentIdx((prev) => (prev + 1) % appleKeynoteScenes.length);
    setProgress(0);
    setTypedChars('');
    setIsClicking(false);
  };

  const handlePrev = () => {
    setCurrentIdx((prev) => (prev - 1 + appleKeynoteScenes.length) % appleKeynoteScenes.length);
    setProgress(0);
    setTypedChars('');
    setIsClicking(false);
  };

  return (
    <div className="keynote-theater">
      {/* Top Playback Controller Deck */}
      <div className="keynote-controls-strip">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div className="keynote-live-pill">
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
            <span>APPLE KEYNOTE PRODUCT LAUNCH SHOWCASE · IN MOTION</span>
          </div>
          <button className="country-pill-btn" onClick={onSelectCountry} title="Switch Country/Jurisdiction">
            <span style={{ fontSize: 16 }}>{activeCountry.flag}</span>
            <span>{activeCountry.name} ({activeCountry.currencySymbol})</span>
            <span style={{ fontSize: 10, color: '#4f46e5' }}>Change ▾</span>
          </button>
        </div>

        <div className="keynote-playback-buttons">
          <button
            className="keynote-btn"
            onClick={() => setIsPlaying((p) => !p)}
            aria-label={isPlaying ? 'Pause Demo' : 'Play Demo'}
          >
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>
          <button className="keynote-btn" onClick={handlePrev} aria-label="Previous Act">
            ← Prev
          </button>
          <button className="keynote-btn" onClick={handleNext} aria-label="Next Act">
            Next →
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginLeft: 8 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: '#64748b' }}>Speed:</span>
            {([1, 1.5, 2] as const).map((s) => (
              <button
                key={s}
                className={`keynote-btn ${speed === s ? 'keynote-btn--primary' : ''}`}
                style={{ padding: '4px 8px', fontSize: 11 }}
                onClick={() => setSpeed(s)}
              >
                {s}x
              </button>
            ))}
          </div>
          <button className="keynote-btn keynote-btn--primary" onClick={onFinishTour} style={{ marginLeft: 12 }}>
            Take Control (Try Workspace) ↗
          </button>
        </div>
      </div>

      {/* Chapter Ribbon / Scrubber */}
      <nav className="keynote-chapter-ribbon" aria-label="Keynote Acts">
        {appleKeynoteScenes.map((sc, idx) => (
          <button
            key={sc.id}
            className={`keynote-chapter-chip ${idx === currentIdx ? 'is-active' : ''}`}
            onClick={() => selectScene(idx)}
          >
            <span className="keynote-chapter-chip-num">ACT 0{sc.chapterNumber}</span>
            <span className="keynote-chapter-chip-title">{sc.actTitle.split('·')[1]?.trim() || sc.actTitle}</span>
            {idx === currentIdx && isPlaying && (
              <div className="keynote-chapter-progress" style={{ width: `${progress}%` }} />
            )}
          </button>
        ))}
      </nav>

      {/* Apple Keynote Presenter Narrative Card */}
      <div className="keynote-presenter-card">
        <div className="keynote-presenter-header">
          <div className="keynote-speaker-info">
            <div className="keynote-speaker-avatar">
              {activeScene.presenterName.slice(0, 1)}
            </div>
            <div className="keynote-speaker-meta">
              <span className="keynote-speaker-name">{activeScene.presenterName}</span>
              <span className="keynote-speaker-role">{activeScene.presenterRole}</span>
            </div>
          </div>
          <span className={`keynote-badge keynote-badge--${activeScene.badgeTone}`}>
            {activeScene.badgeText}
          </span>
        </div>

        <div className="keynote-act-title">{activeScene.actTitle}</div>
        <h2 className="keynote-headline">{activeScene.headline}</h2>
        <p className="keynote-subheadline">{activeScene.subheadline}</p>

        <div className="keynote-speech-bubble">
          {activeScene.presenterNarration}
        </div>

        {/* Specification Points & Live Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20, marginTop: 16 }}>
          <div>
            <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: 1, textTransform: 'uppercase', color: '#64748b', display: 'block', marginBottom: 8 }}>
              ENGINE SPECIFICATIONS &amp; COLD TRUTH:
            </span>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: '#334155', lineHeight: 1.6 }}>
              {activeScene.highlights.map((h, i) => (
                <li key={i}>{h}</li>
              ))}
            </ul>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            {activeScene.metrics.map((m, i) => (
              <div
                key={i}
                style={{
                  background: '#ffffff',
                  border: '1px solid rgba(99, 102, 241, 0.2)',
                  borderRadius: 12,
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                  boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)',
                }}
              >
                <small style={{ fontSize: 10, fontWeight: 800, textTransform: 'uppercase', color: '#64748b' }}>{m.label}</small>
                <strong style={{ fontSize: 14, color: m.tone === 'positive' ? '#059669' : m.tone === 'warning' ? '#d97706' : '#4f46e5' }}>{m.value}</strong>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 20, flexWrap: 'wrap' }}>
          <button className="primary-button" onClick={() => onJumpToFeature(activeScene.targetView)}>
            <span>{activeScene.actionCta} in Live Workspace ↗</span>
          </button>
          <button className="text-action" onClick={onGoAuth}>
            <span>1-Click Test Demo Account ↗</span>
          </button>
        </div>
      </div>

      {/* Keynote Device Screen Stage with Animated Virtual Operator Cursor */}
      <div className="keynote-device-frame">
        {/* macOS Chrome Header */}
        <div className="keynote-device-topbar">
          <div className="keynote-window-dots">
            <span className="keynote-dot keynote-dot--close" />
            <span className="keynote-dot keynote-dot--min" />
            <span className="keynote-dot keynote-dot--zoom" />
          </div>
          <div className="keynote-address-bar">
            <span style={{ color: '#10b981' }}>🔒</span>
            <span>https://my-economy.network/app/{activeScene.targetView}?region={activeCountry.code}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: '#64748b' }}>Operator: Autonomous Copilot</span>
          </div>
        </div>

        {/* Animated Virtual Operator Cursor */}
        <div
          className="keynote-operator-cursor"
          style={{
            top: `${activeScene.cursorTarget.y}%`,
            left: `${activeScene.cursorTarget.x}%`,
          }}
        >
          {isClicking && <div className="keynote-click-ripple" />}
          <svg className="keynote-cursor-pointer" viewBox="0 0 24 24" fill="none">
            <path
              d="M3 3L10.07 19.97L12.58 12.58L19.97 10.07L3 3Z"
              fill="#4f46e5"
              stroke="#ffffff"
              strokeWidth="2"
              strokeLinejoin="round"
            />
          </svg>
          <div className="keynote-cursor-label">
            {activeScene.operatorActionDescription}
          </div>
        </div>

        {/* Viewport Content based on activeScene */}
        <div style={{ padding: 28, background: '#f8fafc', flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
          {activeScene.id === 'keynote-act-1-country' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: '#4f46e5', textTransform: 'uppercase' }}>
                  SOVEREIGN ECONOMIC ENGINE DISPATCH · 5 ACTIVE NATIONS
                </span>
                <span className="status-word status-word--green">PRECISION VERIFIED</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
                {(Object.keys(countryConfigs) as CountryCode[]).map((cCode) => {
                  const c = countryConfigs[cCode];
                  const isCur = cCode === activeCountry.code;
                  return (
                    <div
                      key={cCode}
                      style={{
                        padding: '14px 16px',
                        background: '#ffffff',
                        border: isCur ? '2px solid #4f46e5' : '1px solid var(--line)',
                        borderRadius: 12,
                        boxShadow: isCur ? '0 8px 24px rgba(79, 70, 229, 0.12)' : 'none',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                        <span style={{ fontSize: 24 }}>{c.flag}</span>
                        <strong style={{ fontSize: 12, color: isCur ? '#4f46e5' : '#64748b' }}>{c.currencySymbol} {c.currencyCode}</strong>
                      </div>
                      <strong style={{ fontSize: 14, color: '#0f172a', display: 'block' }}>{c.name}</strong>
                      <small style={{ fontSize: 11, color: '#64748b' }}>{c.bankingStandard.split('+')[0]}</small>
                    </div>
                  );
                })}
              </div>
              <div style={{ padding: 16, background: '#ffffff', borderRadius: 12, border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                <strong style={{ color: '#059669' }}>Zero Float Drift Guarantee:</strong> All balances calculated in integer minor units (paise / cents / pence) to prevent IEEE-754 loss.
              </div>
            </div>
          )}

          {activeScene.id === 'keynote-act-2-multirail' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: '#0284c7', textTransform: 'uppercase' }}>
                  REBIT-AA &amp; OPEN FINANCE LINKED RAILS
                </span>
                <span className="status-word status-word--green">CONSENT SIGNED</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
                {activeCountry.sampleAccounts.map((acc, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '14px 16px',
                      background: '#ffffff',
                      borderRadius: 12,
                      border: '1px solid var(--line)',
                      boxShadow: '0 4px 14px rgba(15, 23, 42, 0.04)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 4,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: 11, fontWeight: 800, color: acc.color }}>{acc.provider}</span>
                      <small style={{ color: '#64748b' }}>{acc.masked}</small>
                    </div>
                    <strong style={{ fontSize: 18, color: '#0f172a' }}>{acc.balanceFormatted}</strong>
                    <span style={{ fontSize: 11, color: '#64748b' }}>{acc.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeScene.id === 'keynote-act-3-ai-copilot' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: '#7c3aed', textTransform: 'uppercase' }}>
                  AUTONOMOUS AI FINANCIAL REPRESENTATIVE
                </span>
                <span className="status-word status-word--green">ACTIVE DISPATCH</span>
              </div>
              <div style={{ background: '#ffffff', border: '1px solid rgba(124, 58, 237, 0.25)', borderRadius: 12, padding: 18, boxShadow: '0 4px 16px rgba(15, 23, 42, 0.04)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#7c3aed', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 12 }}>
                    AI
                  </div>
                  <strong>AwnNORA Copilot (Muse-Spark-1.3)</strong>
                </div>
                <p style={{ margin: '0 0 12px', fontSize: 14, color: '#334155', lineHeight: 1.5 }}>
                  Forensic scan completed across 86 transactions in the selected period. <strong>1 duplicate charge detected:</strong> ₹649 debit on Axis Platinum card repeated 48 hours apart.
                </p>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '8px 14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, color: '#dc2626', fontSize: 12, fontWeight: 700 }}>
                  <span>Dispute Package Prepared · SHA-256 Checksum Locked</span>
                </div>
              </div>
              <div style={{ background: '#ffffff', border: '1px solid var(--line)', borderRadius: 10, padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ color: '#4f46e5', fontWeight: 700 }}>💬 Operator:</span>
                <span style={{ fontSize: 13, color: '#0f172a', fontFamily: 'monospace' }}>
                  {typedChars || 'Audit my statements for duplicate debits and fee anomalies'}<span className="blinking-cursor">|</span>
                </span>
              </div>
            </div>
          )}

          {activeScene.id === 'keynote-act-4-guardian-dispute' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: '#e11d48', textTransform: 'uppercase' }}>
                  GUARDIAN INTERCEPT &amp; ACTION CASEBOOK
                </span>
                <span className="status-word status-word--green">EVIDENCE FROZEN</span>
              </div>
              <div style={{ background: '#ffffff', border: '1px solid rgba(225, 29, 72, 0.3)', borderRadius: 12, padding: 20, boxShadow: '0 6px 20px rgba(225, 29, 72, 0.08)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <strong style={{ fontSize: 16, color: '#0f172a' }}>CASE #DUP-001: Streaming Subscription Rebilling</strong>
                  <span style={{ padding: '3px 10px', borderRadius: 999, background: '#fef2f2', color: '#e11d48', fontWeight: 800, fontSize: 11 }}>
                    ACTION READY
                  </span>
                </div>
                <p style={{ margin: '0 0 12px', fontSize: 13, color: '#475569' }}>
                  Two identical {activeCountry.currencySymbol}649 charges posted 48 hours apart in the same cycle. Cryptographic evidence package created.
                </p>
                <div style={{ padding: '8px 12px', background: '#f1f5f9', borderRadius: 6, fontSize: 11, fontFamily: 'monospace', color: '#334155' }}>
                  EVIDENCE SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                </div>
              </div>
            </div>
          )}

          {activeScene.id === 'keynote-act-5-opportunity' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: '#059669', textTransform: 'uppercase' }}>
                  REAL-TIME OPPORTUNITY RADAR
                </span>
                <span className="status-word status-word--green">ESCROW VERIFIED</span>
              </div>
              <div style={{ background: '#ffffff', border: '1px solid rgba(5, 150, 105, 0.3)', borderRadius: 12, padding: 20, boxShadow: '0 6px 20px rgba(5, 150, 105, 0.08)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 11, fontWeight: 800, color: '#059669', textTransform: 'uppercase' }}>
                    {activeCountry.featuredOpportunity.source}
                  </span>
                  <span style={{ padding: '2px 8px', borderRadius: 6, background: '#ecfdf5', color: '#059669', fontWeight: 800, fontSize: 11 }}>
                    98% PROFILE MATCH
                  </span>
                </div>
                <strong style={{ fontSize: 18, color: '#0f172a', display: 'block', marginBottom: 6 }}>
                  {activeCountry.featuredOpportunity.title}
                </strong>
                <div style={{ display: 'flex', gap: 20, fontSize: 14 }}>
                  <span>Rate: <strong>{activeCountry.featuredOpportunity.rate}</strong></span>
                  <span>Estimated: <strong style={{ color: '#059669' }}>{activeCountry.featuredOpportunity.estimatedMonthly}</strong></span>
                </div>
              </div>
            </div>
          )}

          {activeScene.id === 'keynote-act-6-entitlements' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: '#d97706', textTransform: 'uppercase' }}>
                  SOVEREIGN GOVERNMENT ENTITLEMENTS ENGINE
                </span>
                <span className="status-word status-word--green">PRE-ASSESSED</span>
              </div>
              <div style={{ background: '#ffffff', border: '1px solid rgba(217, 119, 6, 0.3)', borderRadius: 12, padding: 20, boxShadow: '0 6px 20px rgba(217, 119, 6, 0.08)' }}>
                <small style={{ fontSize: 11, fontWeight: 800, color: '#d97706', textTransform: 'uppercase' }}>
                  {activeCountry.featuredSubsidy.ministry}
                </small>
                <strong style={{ fontSize: 18, color: '#0f172a', display: 'block', margin: '4px 0' }}>
                  {activeCountry.featuredSubsidy.title}
                </strong>
                <strong style={{ fontSize: 16, color: '#059669', display: 'block', marginBottom: 8 }}>
                  {activeCountry.featuredSubsidy.valueAnnual}
                </strong>
                <p style={{ margin: 0, fontSize: 13, color: '#475569' }}>
                  {activeCountry.featuredSubsidy.description}
                </p>
              </div>
            </div>
          )}

          {activeScene.id === 'keynote-act-7-commons' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: '#4f46e5', textTransform: 'uppercase' }}>
                  COLLECTIVE COMMONS &amp; BULK QUORUM
                </span>
                <span className="status-word status-word--green">QUORUM UNLOCKED</span>
              </div>
              <div style={{ background: '#ffffff', border: '1px solid rgba(79, 70, 229, 0.3)', borderRadius: 12, padding: 20, boxShadow: '0 6px 20px rgba(79, 70, 229, 0.08)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <strong>{activeCountry.commonsLocality}</strong>
                  <strong style={{ color: '#059669' }}>10 / 10 Joined (100%)</strong>
                </div>
                <div style={{ height: 8, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden', marginBottom: 12 }}>
                  <div style={{ height: '100%', width: '100%', background: '#4f46e5' }} />
                </div>
                <strong style={{ color: '#059669' }}>{activeCountry.commonsSavings}</strong>
              </div>
            </div>
          )}

          {activeScene.id === 'keynote-act-8-adsense-monetization' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: '#059669', textTransform: 'uppercase' }}>
                  GOOGLE ADSENSE MONETIZATION &amp; AUTOMATED BILL OFFSET
                </span>
                <span className="status-word status-word--green">100% OFFSET</span>
              </div>
              <div style={{ background: '#ffffff', border: '1px solid rgba(5, 150, 105, 0.3)', borderRadius: 12, padding: 20, boxShadow: '0 6px 20px rgba(5, 150, 105, 0.08)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <strong style={{ fontSize: 16 }}>Google AdSense Stream (pub-89241029412491)</strong>
                  <span style={{ fontSize: 14, fontWeight: 800, color: '#059669' }}>{activeCountry.adSenseYield}</span>
                </div>
                <div style={{ padding: '12px 14px', background: '#ecfdf5', borderRadius: 8, border: '1px solid #a7f3d0', color: '#065f46', fontSize: 13 }}>
                  <strong>{activeCountry.utilityOffset}</strong> — Zero cash deducted from your checking account!
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


// ==========================================
// 3. LOGIN & SECURITY HUB PAGE
// ==========================================
// ==========================================
// COUNTRY & REGIONAL JURISDICTION SELECTOR MODAL
// ==========================================
function CountrySelectorModal({
  selectedCountry,
  onSelect,
  onClose,
}: {
  selectedCountry: CountryCode;
  onSelect: (code: CountryCode) => void;
  onClose: () => void;
}) {
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="login-dialog" style={{ maxWidth: 880 }} role="dialog" aria-modal="true">
        <button className="dialog-close" onClick={onClose} aria-label="Close">×</button>
        <ShellLabel>SOVEREIGN REGIONAL ECONOMIC ENGINE</ShellLabel>
        <h2>Select Your Country &amp; Economic Jurisdiction</h2>
        <p style={{ margin: '0 0 16px', color: '#475569' }}>
          AwnNORA dynamically re-aligns currency arithmetic, instant payment rails, government subsidy databases, and opportunity registries to your sovereign nation.
        </p>

        <div className="country-grid-modal">
          {(Object.keys(countryConfigs) as CountryCode[]).map((cCode) => {
            const c = countryConfigs[cCode];
            const isSelected = cCode === selectedCountry;
            return (
              <button
                key={cCode}
                className={`country-card-option ${isSelected ? 'is-selected' : ''}`}
                onClick={() => onSelect(cCode)}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 28 }}>{c.flag}</span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 800,
                      padding: '3px 8px',
                      borderRadius: 6,
                      background: isSelected ? '#4f46e5' : '#f1f5f9',
                      color: isSelected ? '#ffffff' : '#475569',
                    }}
                  >
                    {isSelected ? 'ACTIVE ENGINE' : `${c.currencySymbol} ${c.currencyCode}`}
                  </span>
                </div>
                <strong style={{ fontSize: 16, color: '#0f172a' }}>{c.name}</strong>
                <small style={{ fontSize: 11, color: '#4f46e5', fontWeight: 700 }}>{c.bankingStandard}</small>
                <span style={{ fontSize: 11, color: '#64748b', lineHeight: 1.4 }}>{c.railsDescriptor}</span>
                <div style={{ marginTop: 6, padding: '8px 10px', background: '#f8fafc', borderRadius: 8, fontSize: 11, border: '1px solid var(--line)' }}>
                  <strong style={{ color: '#0f172a' }}>Featured Subsidy:</strong> {c.featuredSubsidy.title} ({c.featuredSubsidy.valueAnnual})
                </div>
              </button>
            );
          })}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
          <button className="secondary-button" onClick={onClose}>
            Done
          </button>
        </div>
      </section>
    </div>
  );
}

function LoginSecurityPage({
  busy,
  session,
  onLogin,
  onLaunchDemo,
  onConnected,
  onLogout,
}: {
  busy: boolean;
  session: Session | null;
  onLogin: (email: string, password: string) => void;
  onLaunchDemo: () => void;
  onConnected: (result: Session) => void;
  onLogout: () => void;
}) {
  const [tab, setTab] = useState<'signin' | 'register' | 'verify'>('signin');
  const [email, setEmail] = useState('demo@example.com');
  const [displayName, setDisplayName] = useState('AwnNORA Demo Explorer');
  const [password, setPassword] = useState('Password12345!');
  const [verificationToken, setVerificationToken] = useState('');
  const [pendingSession, setPendingSession] = useState<Session | null>(null);
  const [localBusy, setLocalBusy] = useState(false);
  const [localError, setLocalError] = useState('');
  const [localNotice, setLocalNotice] = useState('');

  const register = async () => {
    setLocalBusy(true);
    setLocalError('');
    setLocalNotice('');
    try {
      const result = await api.register(email.trim(), password, displayName.trim());
      setPendingSession(result);
      setTab('verify');
      setLocalNotice('Account created. Enter the one-time email verification token sent by your configured email adapter.');
    } catch (cause) {
      setLocalError(cause instanceof Error ? cause.message : 'Account registration failed.');
    } finally {
      setLocalBusy(false);
    }
  };

  const verify = async () => {
    if (!pendingSession) return;
    setLocalBusy(true);
    setLocalError('');
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

  return (
    <div className="login-security-page">
      <section className="page-intro">
        <div>
          <ShellLabel>SECURITY &amp; ACCESS GATEWAY</ShellLabel>
          <h1>
            Your private economic space,<br />
            <em>cryptographically fortified.</em>
          </h1>
          <p>
            Choose between instant synthetic demo access for exploratory testing or establish a realistic, Argon2id-encrypted personal workspace.
          </p>
        </div>
      </section>

      <div className="login-security-layout">
        {/* Left Side: Auth Card */}
        <section className="auth-card">
          <div className="demo-instant-box">
            <span className="demo-badge">QUICK TEST ACCESS</span>
            <h3>Explore Without Setup</h3>
            <p>Launch a fully populated, pre-seeded synthetic test workspace with 9 connected payment rails, active dispute cases, and verified ONDC contracts.</p>
            <button className="primary-button primary-button--glow primary-button--full" disabled={busy} onClick={onLaunchDemo}>
              <span>⚡ Enter Instant Test Demo Workspace</span>
            </button>
          </div>

          <div className="auth-divider">
            <span>OR ESTABLISH A REALISTIC ACCOUNT</span>
          </div>

          {session ? (
            <div className="authenticated-status-box">
              <div className="auth-user-header">
                <StatusDot tone="green" />
                <strong>Signed in as {session.user.display_name}</strong>
              </div>
              <small>{session.user.email} · Verified Session Active</small>
              <div className="auth-status-actions">
                <button className="primary-button" onClick={() => onConnected(session)}>
                  Go to AI Pilot Workspace ↗
                </button>
                <button className="secondary-button" onClick={onLogout}>
                  Sign Out
                </button>
              </div>
            </div>
          ) : (
            <div className="credentials-form-box">
              {localNotice && <div className="dialog-notice">{localNotice}</div>}
              {localError && <div className="dialog-error">{localError}</div>}

              {tab === 'verify' ? (
                <form onSubmit={(e) => { e.preventDefault(); void verify(); }} className="auth-form">
                  <ShellLabel>EMAIL CHALLENGE</ShellLabel>
                  <label>
                    <span>VERIFICATION TOKEN</span>
                    <input
                      type="text"
                      required
                      value={verificationToken}
                      onChange={(e) => setVerificationToken(e.target.value)}
                      placeholder="Paste 32+ character verification token..."
                    />
                  </label>
                  <button className="primary-button primary-button--full" disabled={localBusy}>
                    {localBusy ? 'Verifying…' : 'Verify &amp; Enter Workspace'} <span>↗</span>
                  </button>
                  <button type="button" className="text-action" onClick={() => setTab('signin')}>
                    Back to Sign In
                  </button>
                </form>
              ) : (
                <>
                  <div className="dialog-tabs">
                    <button
                      type="button"
                      className={tab === 'signin' ? 'is-active' : ''}
                      onClick={() => { setTab('signin'); setLocalError(''); }}
                    >
                      Sign In
                    </button>
                    <button
                      type="button"
                      className={tab === 'register' ? 'is-active' : ''}
                      onClick={() => { setTab('register'); setLocalError(''); }}
                    >
                      Create Realistic Account
                    </button>
                  </div>

                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      if (tab === 'signin') onLogin(email.trim(), password);
                      else void register();
                    }}
                    className="auth-form"
                  >
                    {tab === 'register' && (
                      <label>
                        <span>YOUR NAME</span>
                        <input
                          type="text"
                          required
                          value={displayName}
                          onChange={(e) => setDisplayName(e.target.value)}
                        />
                      </label>
                    )}
                    <label>
                      <span>EMAIL ADDRESS</span>
                      <input
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                      />
                    </label>
                    <label>
                      <span>PASSWORD (MIN 12 CHARACTERS)</span>
                      <input
                        type="password"
                        required
                        minLength={12}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                      />
                    </label>
                    <button className="primary-button primary-button--full" disabled={busy || localBusy}>
                      {busy || localBusy ? 'Connecting…' : tab === 'signin' ? 'Sign In to Workspace' : 'Create Private Account'} <span>↗</span>
                    </button>
                  </form>
                </>
              )}
            </div>
          )}
        </section>

        {/* Right Side: Security & Realistic Banking Architecture */}
        <section className="security-architecture-panel">
          <div className="section-heading">
            <div>
              <ShellLabel>TRUST &amp; CRYPTOGRAPHIC PROOFS</ShellLabel>
              <h2>Security Architecture &amp; Real Banking Rails</h2>
            </div>
          </div>

          <div className="security-specs-list">
            <div className="security-spec-card">
              <span className="spec-icon">🏦</span>
              <div>
                <strong>RBI Account Aggregator (AA) Integration</strong>
                <p>Real bank accounts are connected via certified Financial Information Providers (FIPs). Consent is electronic, signed, time-bound, and revocable. AwnNORA never touches banking passwords or OTPs.</p>
              </div>
            </div>

            <div className="security-spec-card">
              <span className="spec-icon">💳</span>
              <div>
                <strong>Card-on-File Tokenization (CoFT)</strong>
                <p>Card numbers are tokenized directly with Visa, Mastercard, and RuPay networks under RBI guidelines. Transaction surveillance tracks posted debits without storing PAN data.</p>
              </div>
            </div>

            <div className="security-spec-card">
              <span className="spec-icon">🔐</span>
              <div>
                <strong>Argon2id &amp; Ephemeral Sessions</strong>
                <p>Passphrases are salted and stretched using Argon2id with memory-hard parameters. Sessions use cryptographically random 256-bit opaque tokens with a strict 12-hour expiration.</p>
              </div>
            </div>

            <div className="security-spec-card">
              <span className="spec-icon">📜</span>
              <div>
                <strong>SHA-256 Immutable Evidence Ledger</strong>
                <p>Every Guardian finding and Casebook state transition is hashed. Evidence snapshots are frozen at case creation so merchants and banks cannot dispute statement timestamps.</p>
              </div>
            </div>

            <div className="security-spec-card">
              <span className="spec-icon">🤝</span>
              <div>
                <strong>Zero-Knowledge Differential Privacy</strong>
                <p>Commons collective campaigns aggregate demand clusters using differential privacy. No individual account names, transaction rows, or balances are shared with suppliers or cohort peers.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

// ==========================================
// 4. LIVE ECONOMIC STREAM TICKER
// ==========================================
function LiveEconomicStreamTicker({
  events,
  onAction,
}: {
  events: LiveEconomicEvent[];
  onAction: (view: ViewKey) => void;
}) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (events.length <= 1) return;
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % events.length);
    }, 6000);
    return () => clearInterval(timer);
  }, [events]);

  const current = events[index] || events[0];
  if (!current) return null;

  return (
    <div className="stream-ticker-bar" role="marquee" aria-live="polite">
      <div className="stream-ticker-badge">
        <span className="ticker-live-dot" />
        <span>LIVE ECO-STREAM</span>
      </div>
      <div className="stream-ticker-content">
        <span className={`engine-tag engine-tag--${current.engine.toLowerCase()}`}>{current.engine}</span>
        <strong>{current.title}</strong>
        <span className="ticker-desc">{current.description}</span>
        {current.amount && <span className="ticker-amt">{current.amount}</span>}
      </div>
      <div className="stream-ticker-actions">
        {current.action_label && current.action_view && (
          <button
            className="ticker-action-btn"
            onClick={() => onAction(current.action_view!)}
          >
            {current.action_label} ↗
          </button>
        )}
        <div className="ticker-nav-dots">
          {events.slice(0, 5).map((e, idx) => (
            <button
              key={e.id}
              className={`ticker-dot ${idx === index ? 'is-active' : ''}`}
              onClick={() => setIndex(idx)}
              aria-label={`Go to event ${idx + 1}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ==========================================
// 5. AI ASSISTANT / AUTONOMOUS REPRESENTATIVE
// ==========================================
function AssistantPage({
  messages,
  onSend,
  onActionCard,
  railsCount,
  openFindingsCount,
  onNavigate,
}: {
  messages: AIAssistantMessage[];
  onSend: (text: string) => void;
  onActionCard: (card: NonNullable<AIAssistantMessage['actionCard']>) => void;
  railsCount: number;
  openFindingsCount: number;
  onNavigate: (view: ViewKey) => void;
}) {
  const [input, setInput] = useState('');

  const quickPrompts = [
    { label: '⚡ Audit accounts for leaks & duplicate charges', text: 'Audit my accounts for duplicate charges and rogue debits.' },
    { label: '📊 View Google AdSense utility bill offset', text: 'How is Google AdSense ad revenue offsetting my monthly living expenses?' },
    { label: '💳 Link PhonePe / GPay / Bank / Card', text: 'Help me connect my UPI and bank accounts to the system.' },
    { label: '💼 Find highest paying Skill India / ONDC gigs', text: 'Find the best matched income opportunities on Skill India and ONDC.' },
    { label: '🏛️ Claim PM-Surya & SVANidhi government grants', text: 'Check my eligibility for government subsidies and direct benefit transfers.' },
    { label: '🤝 Join Solar Bulk Order collective pool', text: 'Show me active collective commons campaigns and join the solar pool.' },
    { label: '📈 Optimize Solo Enterprise profit margins', text: 'Simulate my product pricing and calculate contribution margin.' },
  ];

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSend(input.trim());
    setInput('');
  };

  return (
    <div className="assistant-workspace">
      {/* Hero Header */}
      <section className="assistant-hero">
        <div className="assistant-hero__badge">
          <div className="hero-avatar">
            <span>A</span>
            <span className="halo-ring" />
          </div>
          <div>
            <div className="hero-title-row">
              <h1>AwnNORA Autonomous Agent</h1>
              <span className="agent-status-tag">ACTIVE · LEVEL 4 ECONOMIC PILOT</span>
            </div>
            <p>
              Your personal economic representative. I guard your accounts, locate income, pool collective bargaining power, and execute tasks directly on your behalf.
            </p>
          </div>
        </div>

        {/* Live System Telemetry Bar */}
        <div className="assistant-telemetry-grid">
          <div className="telemetry-card">
            <span className="telemetry-label">CONNECTED RAILS</span>
            <strong className="telemetry-value text-cyan">{railsCount} Rails Active</strong>
            <small>PhonePe · GPay · HDFC · SBI · Stripe · AdSense</small>
          </div>
          <div className="telemetry-card">
            <span className="telemetry-label">GUARDIAN WATCH</span>
            <strong className="telemetry-value text-rose">{openFindingsCount} Leaks Flagged</strong>
            <small>Netflix ₹649 duplicate debit isolated</small>
          </div>
          <div className="telemetry-card">
            <span className="telemetry-label">COMMONS LEVERAGE</span>
            <strong className="telemetry-value text-emerald">9/10 Quorum</strong>
            <small>Jaipur Solar Pool (22% Cohort Saving)</small>
          </div>
          <div className="telemetry-card">
            <span className="telemetry-label">MODEL ARCHITECTURE</span>
            <strong className="telemetry-value text-purple">Meta Muse Spark 1.3</strong>
            <small>Standard Mode · Deterministic Kernel</small>
          </div>
        </div>
      </section>

      {/* Main Conversation Stream */}
      <div className="chat-container">
        <div className="chat-messages-scroll">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat-message chat-message--${msg.sender}`}>
              <div className="message-header">
                <span className="sender-name">{msg.sender === 'agent' ? 'AwnNORA Autonomous Pilot' : 'You'}</span>
                <span className="message-time">{msg.timestamp}</span>
              </div>
              <div className="message-body">
                <p style={{ whiteSpace: 'pre-line' }}>{msg.text}</p>
                {msg.actionCard && (
                  <div className="chat-action-card">
                    <div className="action-card-header">
                      <span className="action-card-icon">⚡</span>
                      <strong>{msg.actionCard.title}</strong>
                    </div>
                    <p>{msg.actionCard.description}</p>
                    <button
                      className="action-card-btn"
                      onClick={() => onActionCard(msg.actionCard!)}
                    >
                      {msg.actionCard.buttonLabel}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Quick Suggestion Chips */}
        <div className="quick-prompts-bar">
          <span className="quick-prompt-label">EXECUTE ON SYSTEM:</span>
          <div className="quick-chips-wrapper">
            {quickPrompts.map((chip) => (
              <button
                key={chip.label}
                className="quick-chip"
                onClick={() => onSend(chip.text)}
              >
                {chip.label}
              </button>
            ))}
          </div>
        </div>

        {/* Chat Input Dock */}
        <form className="chat-input-form" onSubmit={handleFormSubmit}>
          <input
            type="text"
            className="chat-input-field"
            placeholder="Command your agent: e.g. 'Audit my accounts', 'Show AdSense offset', 'Find ONDC projects'..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" className="chat-send-btn" disabled={!input.trim()}>
            <span>Execute</span>
            <i>↗</i>
          </button>
        </form>
      </div>

      {/* Feature Jump Matrix */}
      <section className="agent-jump-matrix">
        <div className="section-heading">
          <div>
            <ShellLabel>SYSTEM CAPABILITY TILES</ShellLabel>
            <h2>Instant Module Navigation</h2>
          </div>
          <span className="muted-meta">Code-enforced deterministic safety</span>
        </div>
        <div className="jump-tiles-grid">
          <button className="jump-tile jump-tile--cyan" onClick={() => onNavigate('accounts')}>
            <span className="jump-icon">💳</span>
            <strong>Connected Rails &amp; Banks</strong>
            <p>Manage UPI, Debit/ATM cards, Stripe, AdSense and HDFC/SBI bank accounts.</p>
            <span className="jump-cta">Manage Rails ↗</span>
          </button>
          <button className="jump-tile jump-tile--emerald" onClick={() => onNavigate('opportunity')}>
            <span className="jump-icon">💼</span>
            <strong>Opportunity Engine</strong>
            <p>Verified projects from Skill India Digital and ONDC Open Network.</p>
            <span className="jump-cta">Inspect Matches ↗</span>
          </button>
          <button className="jump-tile jump-tile--amber" onClick={() => onNavigate('entitlements')}>
            <span className="jump-icon">🏛️</span>
            <strong>Entitlements &amp; Grants</strong>
            <p>PM Surya Ghar Rooftop Solar, PM-SVANidhi, and Ayushman Bharat claim packs.</p>
            <span className="jump-cta">Claim Subsidies ↗</span>
          </button>
          <button className="jump-tile jump-tile--purple" onClick={() => onNavigate('commons')}>
            <span className="jump-icon">🤝</span>
            <strong>Collective Commons</strong>
            <p>Bargaining power in numbers: 9/10 solar pool near quorum for 22% discounts.</p>
            <span className="jump-cta">Join Commons ↗</span>
          </button>
        </div>
      </section>
    </div>
  );
}

// ==========================================
// 6. ACCOUNTS & MULTI-RAIL HUB
// ==========================================
function AccountsPage({
  rails,
  adsenseStream,
  onOpenConnectModal,
  onReviewLeak,
}: {
  rails: ConnectedRail[];
  adsenseStream: AdSenseMonetizationStream;
  onOpenConnectModal: () => void;
  onReviewLeak: () => void;
}) {
  const upiRails = rails.filter((r) => r.type === 'upi' || (r.type === 'wallet' && !r.name.includes('AdSense')));
  const bankRails = rails.filter((r) => r.type === 'bank');
  const cardRails = rails.filter((r) => r.type === 'card');
  const globalRails = rails.filter((r) => r.type === 'global');
  const adsenseRails = rails.filter((r) => r.name.includes('AdSense'));

  return (
    <div className="accounts-page">
      <section className="page-intro accounts-intro">
        <div>
          <ShellLabel>MULTI-RAIL PAYMENT, BANKING &amp; YIELD HUB</ShellLabel>
          <h1>
            All your economic rails,<br />
            <em>unified &amp; protected.</em>
          </h1>
          <p>
            Connect any Indian UPI rail, bank account, ATM/debit/credit card, global merchant rail, or digital AdSense publisher stream. Autonomous Guardian continuously watches every rail against fraudulent debits and stealth subscriptions.
          </p>
        </div>
        <div className="intro-actions">
          <button className="primary-button primary-button--glow" onClick={onOpenConnectModal}>
            <span>➕ Link New Payment Rail</span>
          </button>
        </div>
      </section>

      {/* Aggregate Balance Highlights */}
      <section className="metric-band accounts-metrics" aria-label="Accounts overview">
        <Metric
          label="TOTAL LIQUID BALANCE"
          value="₹2,50,320.00"
          sub={`${rails.length} linked rails in active sync`}
          tone="positive"
        />
        <Metric
          label="INSTANT UPI VPAS"
          value={`${upiRails.length} Active`}
          sub="PhonePe · Google Pay · Paytm · Amazon"
          tone="normal"
        />
        <Metric
          label="CORE BANK DEPOSITS"
          value={`${bankRails.length} Connected`}
          sub="HDFC Salary · SBI Emergency Savings"
          tone="normal"
        />
        <Metric
          label="ADSENSE YIELD BUFFER"
          value="₹16,400.00 / mo"
          sub="Offsetting 100% of power & fiber bills"
          tone="positive"
        />
      </section>

      {/* Alert banner if an account has attention required */}
      <div className="rail-attention-banner">
        <div className="rail-attention-content">
          <span className="alert-badge">ACTION NEEDED</span>
          <div>
            <strong>Axis Bank Platinum Credit Card: Duplicate Charge Flagged</strong>
            <p>Two identical ₹649 debits for Netflix posted within 48 hours. Evidence captured and dispute case ready.</p>
          </div>
        </div>
        <button className="primary-button primary-button--small" onClick={onReviewLeak}>
          Review &amp; Freeze Case ↗
        </button>
      </div>

      {/* Special Section: Google AdSense & Creator Monetization Streams */}
      <div className="rail-group-section adsense-section-wrap">
        <div className="section-heading">
          <div>
            <ShellLabel>DIGITAL ASSET MONETIZATION</ShellLabel>
            <h2>Google AdSense &amp; Creator Yield Streams</h2>
          </div>
          <span className="verified-chip">✓ Verified Publisher ID Linked</span>
        </div>

        <div className="adsense-featured-card">
          <div className="adsense-card-header">
            <div className="adsense-logo-monogram">G</div>
            <div>
              <strong>{adsenseStream.channel_name}</strong>
              <small>Publisher ID: {adsenseStream.publisher_id} · Status: Active Yield</small>
            </div>
            <span className="adsense-status-tag">EFT Payouts Enabled</span>
          </div>

          <div className="adsense-metrics-row">
            <div>
              <span className="adsense-metric-label">MONTHLY IMPRESSIONS</span>
              <strong>{adsenseStream.monthly_impressions}</strong>
            </div>
            <div>
              <span className="adsense-metric-label">AVERAGE eCPM</span>
              <strong>{adsenseStream.average_ecpm}</strong>
            </div>
            <div>
              <span className="adsense-metric-label">NET MONTHLY AD YIELD</span>
              <strong className="text-emerald">{adsenseStream.net_monthly_yield}</strong>
            </div>
            <div>
              <span className="adsense-metric-label">LAST SETTLEMENT</span>
              <strong>{adsenseStream.last_payout_date}</strong>
            </div>
          </div>

          <div className="adsense-offset-box">
            <strong>⚡ Automated Living Expense Offset Rule:</strong>
            <p>{adsenseStream.offset_target_obligation}. Ad revenue automatically neutralizes these costs before they impact your salary deposit.</p>
          </div>
        </div>

        <div className="rail-cards-grid" style={{ marginTop: '12px' }}>
          {adsenseRails.map((rail) => (
            <RailCard key={rail.id} rail={rail} />
          ))}
        </div>
      </div>

      {/* Section 1: UPI & Wallets */}
      <div className="rail-group-section">
        <div className="section-heading">
          <div>
            <ShellLabel>INSTANT PAYMENT RAILS</ShellLabel>
            <h2>UPI Apps &amp; Wallets</h2>
          </div>
          <button className="text-action" onClick={onOpenConnectModal}>+ Link another UPI VPA</button>
        </div>
        <div className="rail-cards-grid">
          {upiRails.map((rail) => (
            <RailCard key={rail.id} rail={rail} />
          ))}
        </div>
      </div>

      {/* Section 2: Core Banking & Savings */}
      <div className="rail-group-section">
        <div className="section-heading">
          <div>
            <ShellLabel>DEPOSIT ACCOUNTS</ShellLabel>
            <h2>Core Banking &amp; Emergency Savings</h2>
          </div>
          <button className="text-action" onClick={onOpenConnectModal}>+ Link Bank Account</button>
        </div>
        <div className="rail-cards-grid">
          {bankRails.map((rail) => (
            <RailCard key={rail.id} rail={rail} />
          ))}
        </div>
      </div>

      {/* Section 3: Cards & Credit Lines */}
      <div className="rail-group-section">
        <div className="section-heading">
          <div>
            <ShellLabel>CARD RAILS</ShellLabel>
            <h2>Credit, Debit &amp; ATM Cards</h2>
          </div>
          <button className="text-action" onClick={onOpenConnectModal}>+ Add Card</button>
        </div>
        <div className="rail-cards-grid">
          {cardRails.map((rail) => (
            <RailCard key={rail.id} rail={rail} onAttentionClick={onReviewLeak} />
          ))}
        </div>
      </div>

      {/* Section 4: Global Merchant & Escrow */}
      <div className="rail-group-section">
        <div className="section-heading">
          <div>
            <ShellLabel>CROSS-BORDER &amp; MERCHANT</ShellLabel>
            <h2>Global Payout Rails</h2>
          </div>
          <button className="text-action" onClick={onOpenConnectModal}>+ Link Stripe / PayPal</button>
        </div>
        <div className="rail-cards-grid">
          {globalRails.map((rail) => (
            <RailCard key={rail.id} rail={rail} />
          ))}
        </div>
      </div>
    </div>
  );
}

function RailCard({ rail, onAttentionClick }: { rail: ConnectedRail; onAttentionClick?: () => void }) {
  return (
    <div
      className={`rail-card ${rail.status === 'ATTENTION_REQUIRED' ? 'rail-card--attention' : ''}`}
      style={{ borderTop: `4px solid ${rail.color}` }}
    >
      <div className="rail-card-top">
        <div className="rail-badge" style={{ background: rail.accent_gradient }}>
          {rail.icon_label}
        </div>
        <div className="rail-meta">
          <strong>{rail.name}</strong>
          <small>{rail.masked_identifier}</small>
        </div>
        {rail.is_default && <span className="default-pill">DEFAULT</span>}
        {rail.status === 'ATTENTION_REQUIRED' && (
          <span className="attention-pill" onClick={onAttentionClick}>
            ALERT !
          </span>
        )}
      </div>

      <div className="rail-balance-block">
        <span className="rail-balance-label">AVAILABLE BALANCE</span>
        <strong className="rail-balance-value">{rail.balance_formatted}</strong>
      </div>

      <div className="rail-card-foot">
        <span className="rail-activity-text">{rail.last_activity}</span>
        <span className="rail-status-dot-wrap">
          <StatusDot tone={rail.status === 'ACTIVE' ? 'green' : 'rose'} />
          <small>{rail.status === 'ACTIVE' ? 'Live & Protected' : 'Audit Required'}</small>
        </span>
      </div>
    </div>
  );
}

// Modal for Connecting New Payment Rails
function ConnectRailModal({
  activeCountry,
  onClose,
  onAddRail,
}: {
  activeCountry: CountryConfig;
  onClose: () => void;
  onAddRail: (rail: ConnectedRail) => void;
}) {
  const [type, setType] = useState<RailType>('upi');
  const [provider, setProvider] = useState('PhonePe');
  const [identifier, setIdentifier] = useState('user@ybl');
  const [initialBalance, setInitialBalance] = useState('5000');
  const [syncing, setSyncing] = useState(false);

  const providerDefaults: Record<RailType, string[]> = {
    upi: activeCountry.code === 'IN'
      ? ['PhonePe', 'Google Pay', 'Paytm', 'Amazon Pay', 'BHIM UPI']
      : activeCountry.code === 'US'
        ? ['Apple Cash', 'Venmo Instant', 'Zelle RTP', 'Cash App']
        : ['Faster Payments', 'Monzo Instant', 'Revolut Pay', 'SEPA Instant'],
    bank: activeCountry.sampleAccounts.map((a) => a.provider).slice(0, 5),
    card: activeCountry.code === 'IN'
      ? ['Axis Bank Credit Card', 'HDFC Regalia Debit', 'SBI Global ATM Card', 'RuPay Platinum']
      : ['Visa Infinite', 'Mastercard World Elite', 'American Express Platinum'],
    wallet: ['Google AdSense Stream', 'PayPal Wallet', 'Amazon Pay Balance'],
    global: ['Stripe USD Merchant', 'PayPal International', 'Wise Multi-Currency'],
  };

  const handleTypeChange = (newType: RailType) => {
    setType(newType);
    const defaultProv = providerDefaults[newType][0];
    setProvider(defaultProv);
    if (newType === 'upi') setIdentifier('user@okaxis');
    else if (newType === 'bank') setIdentifier('A/C •••• 9921');
    else if (newType === 'card') setIdentifier('Card •••• 4410');
    else if (newType === 'wallet') setIdentifier('pub-89241029412491');
    else setIdentifier('acct_stripe_live_usd');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSyncing(true);

    setTimeout(() => {
      const colors: Record<string, { color: string; gradient: string }> = {
        PhonePe: { color: '#6739B7', gradient: 'linear-gradient(135deg, #6739B7, #8E24AA)' },
        'Google Pay': { color: '#1A73E8', gradient: 'linear-gradient(135deg, #1A73E8, #4285F4)' },
        Paytm: { color: '#00BAF2', gradient: 'linear-gradient(135deg, #002970, #00BAF2)' },
        'Amazon Pay': { color: '#FF9900', gradient: 'linear-gradient(135deg, #232F3E, #FF9900)' },
        'HDFC Bank': { color: '#004B8D', gradient: 'linear-gradient(135deg, #004B8D, #002B49)' },
        'State Bank of India': { color: '#280071', gradient: 'linear-gradient(135deg, #280071, #0087CF)' },
        'Axis Bank Credit Card': { color: '#97144D', gradient: 'linear-gradient(135deg, #97144D, #670830)' },
        'Stripe USD Merchant': { color: '#635BFF', gradient: 'linear-gradient(135deg, #635BFF, #0A2540)' },
        'Google AdSense Stream': { color: '#34A853', gradient: 'linear-gradient(135deg, #0F9D58, #4285F4)' },
      };

      const branding = colors[provider] || {
        color: '#10B981',
        gradient: 'linear-gradient(135deg, #10B981, #047857)',
      };

      const minor = (BigInt(initialBalance || '0') * 100n).toString();
      const newRail: ConnectedRail = {
        id: `rail-${Date.now()}`,
        name: `${provider} Rail`,
        type,
        provider,
        masked_identifier: identifier,
        balance_minor: minor,
        balance_formatted: `${activeCountry.currencySymbol}${Number(initialBalance || 0).toLocaleString(activeCountry.locale)}.00`,
        currency: activeCountry.currencyCode,
        status: 'ACTIVE',
        color: branding.color,
        accent_gradient: branding.gradient,
        icon_label: provider.slice(0, 4).toUpperCase(),
        last_activity: 'Just now · Live handshake verified',
      };

      onAddRail(newRail);
      setSyncing(false);
    }, 600);
  };

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="login-dialog rail-modal" role="dialog" aria-modal="true">
        <button className="dialog-close" onClick={onClose} aria-label="Close">×</button>
        <ShellLabel>MULTI-RAIL CONNECTOR</ShellLabel>
        <h2>Connect New Payment Rail</h2>
        <p>Integrate your UPI app, bank account, card, or merchant gateway. End-to-end encrypted; records stay in your private workspace.</p>

        <div className="rail-type-selector">
          <button type="button" className={`rail-type-btn ${type === 'upi' ? 'is-active' : ''}`} onClick={() => handleTypeChange('upi')}>UPI Apps</button>
          <button type="button" className={`rail-type-btn ${type === 'bank' ? 'is-active' : ''}`} onClick={() => handleTypeChange('bank')}>Banks</button>
          <button type="button" className={`rail-type-btn ${type === 'card' ? 'is-active' : ''}`} onClick={() => handleTypeChange('card')}>Cards / ATM</button>
          <button type="button" className={`rail-type-btn ${type === 'wallet' ? 'is-active' : ''}`} onClick={() => handleTypeChange('wallet')}>AdSense / Wallets</button>
          <button type="button" className={`rail-type-btn ${type === 'global' ? 'is-active' : ''}`} onClick={() => handleTypeChange('global')}>Stripe / PayPal</button>
        </div>

        <form onSubmit={handleSubmit} className="rail-modal-form">
          <label>
            <span>SELECT PROVIDER</span>
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              {providerDefaults[type].map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </label>

          <label>
            <span>{type === 'upi' ? 'UPI VPA HANDLE' : type === 'bank' ? 'ACCOUNT NUMBER' : type === 'card' ? 'CARD NUMBER' : type === 'wallet' ? 'PUBLISHER ID' : 'ACCOUNT ID'}</span>
            <input
              type="text"
              required
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="e.g. mobile@upi, A/C 99824, pub-8924102..."
            />
          </label>

          <label>
            <span>INITIAL SEED BALANCE (₹)</span>
            <input
              type="number"
              min="0"
              value={initialBalance}
              onChange={(e) => setInitialBalance(e.target.value)}
            />
          </label>

          <div className="modal-trust-note">
            <span>🔒 Bank-grade Tokenization</span>
            <small>AwnNORA never stores raw credentials or MPINs. Handshakes are verified against live sandbox rails.</small>
          </div>

          <button className="primary-button primary-button--full" disabled={syncing}>
            {syncing ? 'Verifying with Banking Network…' : 'Link Rail &amp; Activate Guardian'} <span>↗</span>
          </button>
        </form>
      </section>
    </div>
  );
}

// ==========================================
// 7. OVERVIEW PAGE (POSITION & POWER)
// ==========================================
function OverviewPage({
  report,
  accounts,
  mode,
  busy,
  outstanding,
  onReview,
  onIntelligence,
  onRefresh,
  onCreateAccount,
  onOpenCase,
  onImportStatement,
  periodStart,
  periodEnd,
  setPeriodStart,
  setPeriodEnd,
  asOf,
  onOpenAssistant,
}: {
  report: PowerReport;
  accounts: FinancialAccount[];
  mode: 'demo' | 'live';
  busy: boolean;
  outstanding: Finding[];
  onReview: () => void;
  onIntelligence: () => void;
  onRefresh: () => void;
  onCreateAccount: (name: string, type: string) => Promise<FinancialAccount>;
  onOpenCase: (finding: Finding) => void;
  onImportStatement: (accountId: string, file: File) => Promise<void>;
  periodStart: string;
  periodEnd: string;
  setPeriodStart: (value: string) => void;
  setPeriodEnd: (value: string) => void;
  asOf: string;
  onOpenAssistant: () => void;
}) {
  const spendRatio = percent(visualNumber(report.gross_expenses), visualNumber(report.income_total));

  return (
    <>
      <section className="page-intro page-intro--overview">
        <div>
          <ShellLabel>YOUR ECONOMIC POSITION</ShellLabel>
          <h1>
            Command your finances<br />
            <em>with total clarity.</em>
          </h1>
          <p>
            Deterministic arithmetic across all linked accounts. Code-enforced transparency with an autonomous AI Representative ready to act.
          </p>
        </div>
        <div className="intro-meta">
          <div className="as-of-label">REPORTING PERIOD</div>
          <div className="period-controls">
            <label>
              <span>FROM</span>
              <input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} />
            </label>
            <label>
              <span>TO</span>
              <input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} />
            </label>
          </div>
          <div className="period-actions">
            <small>As at {dateLabel(asOf)}</small>
            <button className="text-action" disabled={busy || mode !== 'live'} onClick={onRefresh}>
              {busy ? 'Refreshing…' : 'Refresh report ↗'}
            </button>
          </div>
        </div>
      </section>

      <StatementImportPanel
        accounts={accounts}
        mode={mode}
        busy={busy}
        onCreateAccount={onCreateAccount}
        onImportStatement={onImportStatement}
      />

      <section className="metric-band" aria-label="Financial summary">
        <Metric
          label="CLASSIFIED INFLOW"
          value={inr(report.income_total)}
          sub={`${report.account_count} active accounts`}
          tone="positive"
        />
        <Metric
          label="NET OUTFLOW"
          value={inr(report.net_expenses_after_refunds)}
          sub={`${inr(report.refunds)} in recorded refunds`}
          tone="normal"
        />
        <Metric
          label="NET CASHFLOW"
          value={inr(report.net_cashflow)}
          sub={toPaise(report.net_cashflow) >= 0 ? 'Surplus cashflow maintained' : 'Outflow exceeded inflow'}
          tone={toPaise(report.net_cashflow) >= 0 ? 'positive' : 'negative'}
        />
        <Metric
          label="ESSENTIALS DUE · 30 DAYS"
          value={inr(report.upcoming_essential_obligations)}
          sub={`${report.upcoming_obligation_count} obligations due`}
          tone="normal"
        />
      </section>

      <section className="overview-grid">
        <div className="overview-primary">
          <div className="section-heading">
            <div>
              <ShellLabel>THE MONTH IN VIEW</ShellLabel>
              <h2>Where your money moved</h2>
            </div>
            <span className="muted-meta">
              {report.posted_transaction_count.toLocaleString('en-IN')} posted records · {report.currency}
            </span>
          </div>
          <div className="cashflow-panel">
            <div className="cashflow-panel__legend">
              <span>
                <i className="legend-dot legend-dot--income" /> Classified inflow
              </span>
              <span>
                <i className="legend-dot legend-dot--spend" /> Net outflow
              </span>
              <span className="chart-unit">INDICATIVE COMPARISON</span>
            </div>
            <CashflowChart report={report} />
            <div className="cashflow-foot">
              <span>
                Essential costs <strong>{inr(report.essential_expenses)}</strong>
              </span>
              <span>
                Discretionary <strong>{inr(report.discretionary_expenses)}</strong>
              </span>
              <span>
                Outflow / inflow <strong>{spendRatio.toFixed(0)}%</strong>
              </span>
            </div>
          </div>

          <div className="section-heading attention-heading">
            <div>
              <ShellLabel>YOUR ATTENTION</ShellLabel>
              <h2>Worth a closer look</h2>
            </div>
            <button className="text-action" onClick={onReview}>
              Open protection desk ↗
            </button>
          </div>
          <div className="finding-list">
            {report.findings.length === 0 && (
              <div className="empty-state">
                No findings for this period. That is not a guarantee that every charge or opportunity has been checked.
              </div>
            )}
            {report.findings.slice(0, 4).map((finding) => (
              <div className="finding-action-row" key={finding.finding_id}>
                <FindingRow finding={finding} onClick={onReview} />
                <button className="finding-open-case" onClick={() => onOpenCase(finding)}>
                  Open case ⚡
                </button>
              </div>
            ))}
          </div>
        </div>

        <aside className="overview-aside">
          <div className="aside-section next-step-panel">
            <ShellLabel>THE NEXT STEP</ShellLabel>
            <div className="next-step-number">01</div>
            <h3>{outstanding[0]?.title || 'Keep your records complete'}</h3>
            <p>
              {outstanding[0]?.recommended_next_step ||
                'Add the records you want AwnNORA to review. It will not guess missing income or expenses.'}
            </p>
            <button className="primary-button primary-button--small" onClick={onReview}>
              Review the evidence <span>↗</span>
            </button>
            <div className="aside-divider" />
            <div className="next-step-facts">
              <span>Potential duplicate candidates</span>
              <strong className="text-rose">{report.potential_duplicate_count}</strong>
            </div>
            <div className="next-step-facts">
              <span>Verified value created</span>
              <strong className="text-emerald">{inr(report.verified_value_created)}</strong>
            </div>
            <small className="truth-note">
              Potential value is not counted until independently verified and settled.
            </small>
          </div>

          <div className="aside-section commitment-panel">
            <div className="section-heading section-heading--compact">
              <div>
                <ShellLabel>LOOKING AHEAD</ShellLabel>
                <h3>Coming due</h3>
              </div>
              <span className="mini-count">{report.upcoming_obligation_count}</span>
            </div>
            {mode === 'demo' ? (
              demoObligations.map((item) => (
                <div className="due-row" key={item.name}>
                  <span className="due-date">{item.date}</span>
                  <span className="due-name">{item.name}</span>
                  <strong>{inr(item.amount)}</strong>
                </div>
              ))
            ) : (
              <div className="due-empty">
                Your report includes the upcoming total. Open your financial records to inspect individual obligations.
              </div>
            )}
            <div className="due-total">
              <span>Essential total</span>
              <strong>{inr(report.upcoming_essential_obligations)}</strong>
            </div>
          </div>

          <button className="intelligence-link" onClick={onOpenAssistant}>
            <span className="intelligence-link__index">⚡</span>
            <span>
              <strong>Talk to AwnNORA AI Navigator</strong>
              <small>Command your autonomous representative to audit, negotiate, or find work.</small>
            </span>
            <b>↗</b>
          </button>
          <div style={{ marginTop: '8px', textAlign: 'right' }}>
            <button className="text-action" onClick={onIntelligence}>
              Meta AI &amp; Data Permissions ↗
            </button>
          </div>
        </aside>
      </section>

      <section className="engine-line">
        <div className="engine-line__intro">
          <ShellLabel>ONE CONNECTED SYSTEM</ShellLabel>
          <h2>Built around your economic life</h2>
        </div>
        <div className="engine-item">
          <strong>Guardian</strong>
          <small>Protection &amp; evidence</small>
          <span className="engine-state engine-state--active">Active Shield</span>
        </div>
        <div className="engine-item">
          <strong>Opportunity</strong>
          <small>Skills into income</small>
          <span className="engine-state engine-state--cyan">Skill India / ONDC</span>
        </div>
        <div className="engine-item">
          <strong>Entitlements</strong>
          <small>Benefits &amp; claims</small>
          <span className="engine-state engine-state--amber">4 Eligible</span>
        </div>
        <div className="engine-item">
          <strong>Commons</strong>
          <small>Collective leverage</small>
          <span className="engine-state engine-state--emerald">9/10 Quorum</span>
        </div>
      </section>
    </>
  );
}

// ==========================================
// 8. CASEBOOK PAGE (MAKOS ACTIONS)
// ==========================================
function CasebookPage({
  cases,
  selectedCase,
  mode,
  busy,
  onSelect,
  onTransition,
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
    OPEN: 'Open',
    IN_REVIEW: 'In review',
    ACTION_READY: 'Action ready',
    WAITING_FOR_USER: 'Waiting for you',
    WAITING_EXTERNAL: 'Awaiting response',
    RESOLVED: 'Marked resolved',
    CLOSED: 'Closed',
  };
  const snapshot = selected?.source_snapshot;

  return (
    <>
      <section className="page-intro casebook-intro">
        <div>
          <ShellLabel>MAKOS · PERSONAL CASEBOOK</ShellLabel>
          <h1>
            Your dispute cases,<br />
            <em>tracked with forensic proof.</em>
          </h1>
          <p>
            Turn a finding into a trackable piece of work. Every case keeps its source context, current state, and change history.
          </p>
        </div>
        <div className="intro-callout">
          <span>USER-CONTROLLED WORKFLOW</span>
          <strong>Immutable Evidence Timeline</strong>
          <small>Case status records your progress. AwnNORA never moves money without human approval.</small>
        </div>
      </section>

      <div className="casebook-notice">
        <strong>Important distinction</strong>
        <span>
          “Awaiting response” means you are tracking a step performed with provider. “Marked resolved” confirms evidence reconciliation. Verified value remains separate.
        </span>
      </div>

      <div className="casebook-layout">
        <aside className="casebook-list">
          <div className="casebook-list-head">
            <div>
              <ShellLabel>YOUR CASES</ShellLabel>
              <h2>Active Workflows</h2>
            </div>
            <span>{cases.length}</span>
          </div>
          {cases.length === 0 && (
            <div className="casebook-empty">No cases yet. Open one from a finding in Your position.</div>
          )}
          {cases.map((item) => (
            <button
              key={item.id}
              className={`casebook-list-item ${selected?.id === item.id ? 'is-selected' : ''}`}
              onClick={() => onSelect(item.id)}
            >
              <span className="casebook-item-top">
                <small>
                  {item.source_engine} · {item.source_finding_id}
                </small>
                <i className={`case-status case-status--${item.status.toLowerCase()}`}>
                  {statusLabel[item.status]}
                </i>
              </span>
              <strong>{item.source_snapshot.title || item.title}</strong>
              <span className="casebook-item-date">Updated {dateLabel(item.updated_at.slice(0, 10))}</span>
            </button>
          ))}
        </aside>

        <section className="casebook-detail" aria-live="polite">
          {!selected ? (
            <div className="casebook-empty casebook-empty--detail">
              <ShellLabel>CASE DETAIL</ShellLabel>
              <h2>Select a case</h2>
              <p>Choose a case to inspect the finding that created it, its current state, and its complete event timeline.</p>
            </div>
          ) : (
            <>
              <div className="case-detail-top">
                <div>
                  <ShellLabel>{`CASE ${selected.id.slice(0, 14).toUpperCase()}`}</ShellLabel>
                  <h2>{snapshot?.title || selected.title}</h2>
                  <p>{snapshot?.explanation || 'Source explanation is not available.'}</p>
                </div>
                <i className={`case-status case-status--${selected.status.toLowerCase()}`}>
                  {statusLabel[selected.status]}
                </i>
              </div>
              <div className="case-facts">
                <div>
                  <small>SOURCE FINDING</small>
                  <strong>{selected.source_finding_id}</strong>
                </div>
                <div>
                  <small>REVIEW PERIOD</small>
                  <strong>
                    {snapshot?.report_period.period_start} to {snapshot?.report_period.period_end}
                  </strong>
                </div>
                <div>
                  <small>REFERENCE AMOUNT</small>
                  <strong>
                    {selected.amount_minor === null ? 'Not specified' : inr(BigInt(selected.amount_minor))}
                  </strong>
                </div>
                <div>
                  <small>CASE VERSION</small>
                  <strong>v{selected.state_version}</strong>
                </div>
              </div>
              <div className="case-next-step">
                <ShellLabel>SOURCE-RECOMMENDED NEXT STEP</ShellLabel>
                <p>{snapshot?.recommended_next_step || 'Review the underlying source records before acting.'}</p>
                <small>Finding snapshot is frozen at case creation. Refresh the report to inspect newer source data.</small>
              </div>
              <div className="case-transition-area">
                <div>
                  <ShellLabel>UPDATE YOUR WORKFLOW</ShellLabel>
                  <p>Choose the next state that reflects what has actually been done.</p>
                </div>
                <div className="case-transition-actions">
                  {nextStatuses[selected.status].map((status) => (
                    <button
                      key={status}
                      disabled={busy}
                      className={status === 'CLOSED' ? 'case-transition-secondary' : 'case-transition-primary'}
                      onClick={() => onTransition(status)}
                    >
                      {status === 'WAITING_EXTERNAL'
                        ? 'I sent dispute to bank'
                        : status === 'RESOLVED'
                          ? 'Mark resolved'
                          : statusLabel[status]}
                    </button>
                  ))}
                </div>
              </div>
              <div className="case-timeline-head">
                <div>
                  <ShellLabel>IMMUTABLE HISTORY</ShellLabel>
                  <h3>Timeline of Events</h3>
                </div>
                <span>{selected.events.length} events logged</span>
              </div>
              <ol className="case-timeline">
                {selected.events.map((item) => (
                  <li key={item.id}>
                    <span className="timeline-marker" />
                    <div>
                      <div className="timeline-event-top">
                        <strong>
                          {item.event_type === 'CASE_OPENED' ? 'Case opened' : `${statusLabel[item.to_status]}`}
                        </strong>
                        <time>
                          {new Date(item.created_at).toLocaleString('en-IN', {
                            dateStyle: 'medium',
                            timeStyle: 'short',
                          })}
                        </time>
                      </div>
                      {item.note && <p>{item.note}</p>}
                      <small>
                        Event #{item.event_sequence} ·{' '}
                        {item.from_status ? `${statusLabel[item.from_status]} → ` : ''}
                        {statusLabel[item.to_status]}
                      </small>
                    </div>
                  </li>
                ))}
              </ol>
              <div className="casebook-safety-foot">
                {mode === 'demo'
                  ? 'SYNTHETIC REAL-TIME DEMONSTRATION · Local browser state only.'
                  : 'PRIVATE ACCOUNT · Changes are saved to your authenticated account. External actions are not performed.'}
              </div>
            </>
          )}
        </section>
      </div>
    </>
  );
}

function Metric({
  label,
  value,
  sub,
  tone = 'normal',
}: {
  label: string;
  value: string;
  sub: string;
  tone?: 'normal' | 'positive' | 'negative';
}) {
  return (
    <div className={`metric metric--${tone}`}>
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
      <small>{sub}</small>
    </div>
  );
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
      <svg
        viewBox="0 0 520 184"
        className="cashflow-chart"
        role="img"
        aria-label={`Classified inflow ${inr(income)}, net outflow ${inr(spend)}`}
      >
        {[28, 68, 108, 148].map((y) => (
          <line key={y} x1="20" x2="506" y1={y} y2={y} className="chart-gridline" />
        ))}
        {data.map((item, index) => {
          const x = 44 + index * (barWidth * 2 + gap);
          const incH = (item.income / max) * h;
          const spendH = (item.spend / max) * h;
          return (
            <g key={item.month}>
              <rect x={x} y={base - incH} width={barWidth} height={incH} rx="5" className="chart-income" />
              <rect
                x={x + barWidth + 8}
                y={base - spendH}
                width={barWidth}
                height={spendH}
                rx="5"
                className="chart-spend"
              />
              <text x={x + barWidth + 4} y="178" textAnchor="middle" className="chart-label">
                {item.month}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="chart-current">
        <span>SELECTED PERIOD</span>
        <strong className="text-cyan">{inr(report.net_cashflow)}</strong>
        <small>Net cashflow</small>
      </div>
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
      <span className="finding-main">
        <span className="finding-code">{finding.code.replaceAll('_', ' ')}</span>
        <strong>{finding.title}</strong>
        <small>{finding.explanation}</small>
      </span>
      <span className="finding-amount">{finding.amount ? inr(finding.amount) : 'Review'}</span>
      <span className="finding-arrow">↗</span>
    </button>
  );
}

function StatementImportPanel({
  accounts,
  mode,
  busy,
  onCreateAccount,
  onImportStatement,
}: {
  accounts: FinancialAccount[];
  mode: 'demo' | 'live';
  busy: boolean;
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
    setLocalBusy(true);
    setLocalError('');
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
    setLocalBusy(true);
    setLocalError('');
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
    return (
      <section className="import-panel import-panel--demo">
        <div>
          <ShellLabel>LIVE SYNTHETIC DATA STREAM</ShellLabel>
          <h2>Synthetic Real-World Scenarios Active</h2>
          <p>
            The workspace is loaded with multi-rail accounts (PhonePe, GPay, HDFC, SBI, Stripe, AdSense) and live simulated events. Connect an authenticated private account at any time to import real CSV statements.
          </p>
        </div>
        <div className="import-panel__right">
          <span className="fixture-label">SYNTHETIC LIVING STREAM</span>
          <small>Communicative data · Safe bounded sandbox</small>
        </div>
      </section>
    );
  }

  return (
    <section className="import-panel">
      <div className="import-panel__copy">
        <ShellLabel>YOUR FINANCIAL DATA</ShellLabel>
        <h2>Import a statement</h2>
        <p>
          CSV is parsed and stored through the authenticated data service. Each import is idempotent. Credits without an explicit treatment are excluded from cashflow until classified.
        </p>
        <div className="import-schema-note">
          <strong>Accepted columns</strong>
          <code>date, amount, direction, cashflow_treatment, category, description, status</code>
          <small>
            Required: date, amount and direction. A missing treatment defaults to IGNORE. Only import statements you are authorized to use.
          </small>
        </div>
      </div>
      <div className="import-panel__form">
        {inrAccounts.length === 0 ? (
          <div className="account-create-row">
            <label>
              <span>ACCOUNT NAME</span>
              <input value={accountName} onChange={(event) => setAccountName(event.target.value)} maxLength={100} />
            </label>
            <label>
              <span>ACCOUNT TYPE</span>
              <select value={accountType} onChange={(event) => setAccountType(event.target.value)}>
                <option value="BANK_DEPOSIT">Bank deposit</option>
                <option value="CREDIT_CARD">Credit card</option>
                <option value="UPI_WALLET">UPI wallet</option>
                <option value="CASH">Cash</option>
                <option value="OTHER">Other</option>
              </select>
            </label>
            <button
              className="secondary-button"
              disabled={busy || localBusy || !accountName.trim()}
              onClick={createAccount}
            >
              {localBusy ? 'Creating…' : 'Create INR account'}
            </button>
          </div>
        ) : (
          <label className="account-select">
            <span>IMPORT INTO</span>
            <select value={selectedAccount?.id || ''} onChange={(event) => setAccountId(event.target.value)}>
              {inrAccounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.account_name} · {account.account_type.replaceAll('_', ' ')}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="file-select">
          <span>CSV STATEMENT</span>
          <input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0] || null)} />
          <small>{file ? `${file.name} · ${(file.size / 1024).toFixed(1)} KB` : 'UTF-8 CSV · up to 2 MB · 10,000 rows'}</small>
        </label>
        <button
          className="primary-button"
          disabled={!selectedAccount || !file || busy || localBusy}
          onClick={importFile}
        >
          {localBusy || busy ? 'Importing…' : 'Import statement'} <span>↗</span>
        </button>
        <small className="import-boundary">
          Required columns: date, amount, direction. Add cashflow_treatment to classify credits and expenses; otherwise rows default to IGNORE. No bank connection is created.
        </small>
        {localError && <span className="import-error">{localError}</span>}
      </div>
    </section>
  );
}

// ==========================================
// 9. PROTECTION PAGE (GUARDIAN SHIELD)
// ==========================================
function ProtectionPage({ cases, mode, onAI }: { cases: GuardianCase[]; mode: 'demo' | 'live'; onAI: () => void }) {
  return (
    <>
      <section className="page-intro">
        <div>
          <ShellLabel>GUARDIAN · ECONOMIC DEFENCE</ShellLabel>
          <h1>
            Protection starts<br />
            <em>with the evidence.</em>
          </h1>
          <p>
            Review billing signals, documents and commitments before deciding what to do next.
          </p>
        </div>
        <div className="intro-callout">
          <span>HUMAN CONTROL</span>
          <strong>No complaint is sent automatically.</strong>
          <small>Every external step remains under your approval.</small>
        </div>
      </section>
      <div className="protection-status">
        <div>
          <StatusDot tone="amber" />
          <span>DOCUMENT TRUST PIPELINE</span>
          <strong>Autonomous Signature &amp; Integrity Verification Active</strong>
        </div>
        <p>
          Evidence is cryptographically hashed with SHA-256. Guardian isolates discrepancies and prepares dispute timelines without moving funds.
        </p>
      </div>
      <div className="section-heading">
        <div>
          <ShellLabel>YOUR CASES</ShellLabel>
          <h2>Evidence under review</h2>
        </div>
        <span className="muted-meta">
          {cases.length} {mode === 'demo' ? 'synthetic cases' : 'private cases'}
        </span>
      </div>
      <div className="case-list">
        {cases.length === 0 ? (
          <div className="empty-state">
            No Guardian cases are attached to this account yet. Import a statement or add an invoice after the document-safety pipeline is enabled.
          </div>
        ) : (
          cases.map((item) => (
            <article className="case-row" key={item.id}>
              <div className="case-date">{dateLabel(item.issue_date)}</div>
              <div className="case-main">
                <span className="finding-code">{item.case_type.replaceAll('_', ' ')}</span>
                <h3>{item.invoice_id || item.provider_key}</h3>
                <p>{item.findings[0]?.message || 'No findings recorded.'}</p>
                <small>{item.disclaimer}</small>
              </div>
              <div className="case-status">
                <span className={`case-disposition case-disposition--${item.disposition.toLowerCase()}`}>
                  {item.disposition.replaceAll('_', ' ')}
                </span>
                <small>{item.status.replaceAll('_', ' ')}</small>
              </div>
            </article>
          ))
        )}
      </div>
      <div className="bottom-note">
        <span>01 / 03</span>
        <div>
          <strong>Document intelligence is evidence-led.</strong>
          <p>
            Muse models propose extracted fields. SHA-256 hashes, source spans, and deterministic arithmetic decide whether a field is verified.
          </p>
        </div>
        <button className="text-action" onClick={onAI}>
          View Meta AI pipeline ↗
        </button>
      </div>
    </>
  );
}

// ==========================================
// 10. OPPORTUNITY PAGE (REAL SOURCES)
// ==========================================
function OpportunityPage({
  opportunities,
  mode,
  onApply,
}: {
  opportunities: LiveOpportunity[];
  mode: 'demo' | 'live';
  onApply: (opp: LiveOpportunity) => void;
}) {
  return (
    <>
      <section className="page-intro">
        <div>
          <ShellLabel>OPPORTUNITY ENGINE · LIVE DISCOVERY</ShellLabel>
          <h1>
            Turn what you know<br />
            <em>into high-margin income.</em>
          </h1>
          <p>
            Streaming opportunities from verified sources including Skill India Digital, ONDC Open Network, and Local Exchange. Rank work by net income, not headline pay.
          </p>
        </div>
        <div className="intro-callout">
          <span>VERIFIED SOURCES</span>
          <strong>Skill India &amp; ONDC Linked</strong>
          <small>Escrow protected · Zero hidden commission cuts.</small>
        </div>
      </section>

      <div className="capability-banner">
        <span>CAPABILITY GRAPH</span>
        <strong>Skills → Proof → Available Time → Verified Demand → Net Value</strong>
        <small>{mode === 'demo' ? 'Live dynamic matching feed active' : 'Connected private profile'}</small>
      </div>

      <div className="opportunity-layout">
        <div>
          <ShellLabel>{`DISCOVERED MATCHES (${opportunities.length})`}</ShellLabel>
          <h2>Ranked by Net Value &amp; Match Fit</h2>

          <div className="opportunity-items-stream">
            {opportunities.map((opp) => (
              <article className="opportunity-item" key={opp.id}>
                <div className="opp-header">
                  <div className="opportunity-tag">
                    {opp.source} · {opp.category}
                  </div>
                  <span className="opp-match-badge">{opp.match_score}% MATCH</span>
                </div>
                <h3>{opp.title}</h3>
                <div className="opp-meta-row">
                  <span>📍 {opp.location}</span>
                  <span>⚡ {opp.spots_left} spots remaining</span>
                  {opp.verified_source && <span className="verified-chip">✓ Verified Registry</span>}
                </div>

                <div className="skills-chips">
                  {opp.skills_required.map((skill) => (
                    <span key={skill} className="skill-chip">{skill}</span>
                  ))}
                </div>

                <div className="opportunity-data">
                  <span>
                    Gross Rate <strong>{opp.rate}</strong>
                  </span>
                  <span>
                    Estimated Value <strong>{opp.estimated_monthly_value}</strong>
                  </span>
                  <span>
                    Escrow Protection <strong>Guaranteed</strong>
                  </span>
                </div>

                <div className="opp-footer">
                  <button className="primary-button primary-button--small" onClick={() => onApply(opp)}>
                    Claim / Apply via Agent ↗
                  </button>
                  <small>Agent drafts verified portfolio evidence and locks payout escrow.</small>
                </div>
              </article>
            ))}
          </div>
        </div>

        <aside className="rules-panel">
          <ShellLabel>MATCHING RULES</ShellLabel>
          <h3>Good work must fit your life.</h3>
          <ul>
            <li>Skill proof is visible and verified, never assumed.</li>
            <li>Transport, platform charges, and raw material costs are pre-deducted.</li>
            <li>Unsafe terms, delayed payment terms, and toxic schedules are rejected.</li>
            <li>Your private profile is never disclosed without your explicit consent.</li>
          </ul>
          <div className="rules-foot">
            SOURCES <strong>Skill India Digital · ONDC · Local Exchange</strong>
          </div>
        </aside>
      </div>
    </>
  );
}

// ==========================================
// 11. ENTITLEMENTS PAGE (GOVERNMENT GRANTS)
// ==========================================
function EntitlementsPage({
  entitlements,
  mode,
  onClaim,
}: {
  entitlements: LiveEntitlement[];
  mode: 'demo' | 'live';
  onClaim: (ent: LiveEntitlement) => void;
}) {
  return (
    <>
      <section className="page-intro">
        <div>
          <ShellLabel>ENTITLEMENT ENGINE · DIRECT CLAIMS</ShellLabel>
          <h1>
            Claim what is already<br />
            <em>rightfully yours.</em>
          </h1>
          <p>
            Grounded in authoritative government databases: PM Surya Ghar, PM-SVANidhi, Ayushman Bharat, and National Scholarship Portal.
          </p>
        </div>
        <div className="intro-callout">
          <span>AUTHORITATIVE RULES</span>
          <strong>Direct Benefit Transfers</strong>
          <small>Zero middlemen. Subsidies routed directly to verified bank accounts.</small>
        </div>
      </section>

      <div className="source-warning">
        <strong>Government Registry Freshness Active.</strong>
        <span>
          Every scheme is mapped to its issuing Ministry, eligibility criteria, and digital application gateway. Stale rules are automatically culled.
        </span>
      </div>

      <div className="entitlement-table">
        <div className="table-head">
          <span>PROGRAMME &amp; MINISTRY</span>
          <span>ANNUAL VALUE &amp; DETAILS</span>
          <span>STATUS</span>
          <span>ACTION</span>
        </div>
        {entitlements.map((ent) => (
          <div className="entitlement-row" key={ent.id}>
            <div>
              <strong>{ent.title}</strong>
              <small>
                {ent.ministry} · {ent.scheme_code}
              </small>
            </div>
            <div>
              <strong className="text-emerald">{ent.value_annual}</strong>
              <small>{ent.benefit_type} · Deadline: {ent.deadline}</small>
            </div>
            <div>
              <span
                className={`status-word ${
                  ent.eligibility_status === 'VERIFIED_ELIGIBLE'
                    ? 'status-word--green'
                    : ent.eligibility_status === 'ACTIVE_BENEFIT'
                      ? 'status-word--cyan'
                      : 'status-word--amber'
                }`}
              >
                {ent.eligibility_status.replaceAll('_', ' ')}
              </span>
            </div>
            <div>
              <button
                className="primary-button primary-button--small"
                onClick={() => onClaim(ent)}
              >
                {ent.action_cta} ↗
              </button>
            </div>
          </div>
        ))}
      </div>
      <p className="muted-disclaimer">
        {mode === 'demo'
          ? 'Programmes reflect current 2026 Indian national initiatives. Agent automatically populates verified income and family records.'
          : 'Verified scheme discovery active for your account.'}
      </p>
    </>
  );
}

// ==========================================
// 12. SOLO ENTERPRISE PAGE + ADSENSE OFFSET
// ==========================================
function EnterprisePage({
  cost,
  setCost,
  time,
  setTime,
  packaging,
  setPackaging,
  delivery,
  setDelivery,
  price,
  setPrice,
  mode,
  adsenseStream,
}: {
  cost: string;
  setCost: (v: string) => void;
  time: string;
  setTime: (v: string) => void;
  packaging: string;
  setPackaging: (v: string) => void;
  delivery: string;
  setDelivery: (v: string) => void;
  price: string;
  setPrice: (v: string) => void;
  mode: 'demo' | 'live';
  adsenseStream: AdSenseMonetizationStream;
}) {
  const [includeAdSenseSubsidy, setIncludeAdSenseSubsidy] = useState(true);

  const fullCost = toPaise(cost) + toPaise(time) + toPaise(packaging) + toPaise(delivery);
  // If AdSense subsidy is enabled, offset 10% of fulfillment costs
  const effectiveCost = includeAdSenseSubsidy ? (fullCost * 90n) / 100n : fullCost;
  const contribution = toPaise(price) - effectiveCost;
  const margin = toPaise(price) > 0n ? Number((contribution * 10000n) / toPaise(price)) / 100 : 0;

  return (
    <>
      <section className="page-intro">
        <div>
          <ShellLabel>ONE-PERSON ENTERPRISE &amp; MONETIZATION</ShellLabel>
          <h1>
            Your business deserves<br />
            <em>a professional back office.</em>
          </h1>
          <p>
            Understand the complete unit cost of manufacturing and delivering your goods before quoting prices to customers. Apply creator AdSense revenue to subsidize operational overhead.
          </p>
        </div>
        <div className="intro-callout">
          <span>UNIT ECONOMICS</span>
          <strong>Price Above Total Cost</strong>
          <small>Materials are only one slice of true delivery costs.</small>
        </div>
      </section>

      {/* AdSense Yield Integration Banner */}
      <div className="enterprise-adsense-banner">
        <div>
          <span className="adsense-pill">ADSENSE CREATOR SUPPORT</span>
          <strong>Google AdSense Monthly Stream: {adsenseStream.net_monthly_yield}</strong>
          <p>Channel: {adsenseStream.channel_name} ({adsenseStream.publisher_id}). Ad earnings automatically cover fulfillment overhead.</p>
        </div>
        <label className="adsense-toggle-label">
          <input
            type="checkbox"
            checked={includeAdSenseSubsidy}
            onChange={(e) => setIncludeAdSenseSubsidy(e.target.checked)}
          />
          <span>Apply AdSense Overhead Subsidy (-10% cost)</span>
        </label>
      </div>

      <div className="enterprise-layout">
        <section className="calculator-panel">
          <ShellLabel>PRODUCT / SERVICE COST BUILDER</ShellLabel>
          <h2>Build a resilient, profitable price</h2>
          <p className="panel-intro">
            Example: Made-to-order artisanal batch or client service delivery. Adjust the parameters to evaluate economic margins.
          </p>
          <div className="cost-inputs">
            <MoneyInput label="Materials &amp; Ingredients" value={cost} onChange={setCost} />
            <MoneyInput label="Your Time &amp; Labour Value" value={time} onChange={setTime} />
            <MoneyInput label="Packaging &amp; Protective Box" value={packaging} onChange={setPackaging} />
            <MoneyInput label="Delivery &amp; Platform Fees" value={delivery} onChange={setDelivery} />
            <MoneyInput label="Customer Selling Price" value={price} onChange={setPrice} />
          </div>
          <div className="fixture-label">
            {mode === 'demo' ? 'LIVE UNIT ECONOMICS SIMULATION' : 'LOCAL BUSINESS CALCULATION'}
          </div>
        </section>

        <aside className="economics-result">
          <ShellLabel>PRICE INTEGRITY CHECK</ShellLabel>
          <div className="economics-total">
            <span>Base unit cost</span>
            <strong>{inr(fullCost)}</strong>
          </div>
          {includeAdSenseSubsidy && (
            <div className="economics-total text-emerald">
              <span>AdSense subsidy applied</span>
              <strong>-{inr(fullCost - effectiveCost)}</strong>
            </div>
          )}
          <div className="economics-total economics-total--strong">
            <span>Net contribution per unit</span>
            <strong className={contribution >= 0n ? 'good-text' : 'bad-text'}>
              {inr(contribution)}
            </strong>
          </div>
          <div className="margin-track">
            <span style={{ width: `${Math.max(0, Math.min(100, margin))}%` }} />
          </div>
          <div className="margin-label">
            <span>Contribution margin</span>
            <strong className="text-cyan">{Number.isFinite(margin) ? `${margin.toFixed(1)}%` : 'n/a'}</strong>
          </div>
          <div className={`price-verdict ${contribution > 0n ? 'price-verdict--good' : 'price-verdict--bad'}`}>
            {contribution > 0n
              ? '✓ This price yields a positive net return above all production costs.'
              : '⚠️ This price produces a net loss. Adjust fees or negotiate material discounts.'}
          </div>
          <small>
            Taxes, wastage allowances, and equipment depreciation are tracked in extended enterprise reports.
          </small>
        </aside>
      </div>
    </>
  );
}

function MoneyInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="money-input">
      <span>{label}</span>
      <div>
        <i>₹</i>
        <input
          type="text"
          inputMode="decimal"
          pattern="[0-9]{1,12}([.][0-9]{1,2})?"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-label={label}
        />
      </div>
    </label>
  );
}

// ==========================================
// 13. COMMONS PAGE (COLLECTIVE BARGAINING)
// ==========================================
function CommonsPage({
  campaigns,
  mode,
  onJoin,
}: {
  campaigns: CommonsCampaign[];
  mode: 'demo' | 'live';
  onJoin: (id: string) => void;
}) {
  return (
    <>
      <section className="page-intro">
        <div>
          <ShellLabel>COMMONS · COLLECTIVE ECONOMIC INTELLIGENCE</ShellLabel>
          <h1>
            Private individuals.<br />
            <em>Unstoppable collective power.</em>
          </h1>
          <p>
            When households coordinate demand anonymously, they unlock institutional discounts without ever sharing private bank statements.
          </p>
        </div>
        <div className="intro-callout">
          <span>ZERO DATA LEAKAGE</span>
          <strong>Demand-Only Aggregation</strong>
          <small>Suppliers see cohort volume, never personal banking history.</small>
        </div>
      </section>

      <div className="commons-layout">
        <section className="commons-campaign-list">
          <ShellLabel>ACTIVE COLLECTIVE CAMPAIGNS</ShellLabel>
          <h2>Live Neighborhood Quorums</h2>

          <div className="campaign-cards-grid">
            {campaigns.map((camp) => {
              const quorumPct = Math.min(100, (camp.participants_joined / camp.target_quorum) * 100);
              const isReached = camp.status === 'QUORUM_REACHED' || camp.participants_joined >= camp.target_quorum;

              return (
                <div key={camp.id} className={`commons-card ${isReached ? 'commons-card--reached' : ''}`}>
                  <div className="campaign-label">
                    {camp.locality} · {camp.category}
                  </div>
                  <h3>{camp.title}</h3>

                  <div className="quorum-block">
                    <div className="quorum-top">
                      <span>QUORUM PROGRESS</span>
                      <strong>
                        {camp.participants_joined} / {camp.target_quorum} Households
                      </strong>
                    </div>
                    <div className="quorum-track">
                      <span style={{ width: `${quorumPct}%` }} />
                    </div>
                    <small>
                      {isReached
                        ? '🎉 Quorum reached! Supplier volume discount unlocked.'
                        : `Only ${camp.target_quorum - camp.participants_joined} more households needed for ${camp.potential_savings_percent}% discount.`}
                    </small>
                  </div>

                  <div className="campaign-economics">
                    <span>
                      Potential Savings: <strong>{camp.potential_savings_percent}% OFF</strong>
                    </span>
                    <span>
                      Net Benefit: <strong className="text-emerald">{camp.estimated_savings}</strong>
                    </span>
                    <span>
                      Time Window: <strong>{camp.expires_in}</strong>
                    </span>
                  </div>

                  <button
                    className={`primary-button ${isReached ? 'primary-button--confirmed' : ''}`}
                    onClick={() => onJoin(camp.id)}
                    disabled={isReached}
                  >
                    {isReached ? '✓ Quorum Achieved (Discount Locked)' : 'Join Collective Pool ⚡'}
                  </button>
                </div>
              );
            })}
          </div>
        </section>

        <aside className="commons-principles">
          <ShellLabel>THE PRIVACY CONTRACT</ShellLabel>
          <h3>What stays private</h3>
          <ul>
            <li>Bank statements and raw transaction records</li>
            <li>Names, addresses, and national identity numbers</li>
            <li>Household-specific debt or financial difficulty</li>
            <li>Private personal knowledge graph records</li>
          </ul>
          <div className="aside-divider" />
          <h3>What is pooled</h3>
          <ul>
            <li>Anonymized category demand (e.g. 3kW Solar Inverter)</li>
            <li>Broad locality cluster (e.g. Jaipur North)</li>
            <li>Only with active cryptographic consent</li>
          </ul>
          <div className="commons-alert">
            Mathematical Differential Privacy ensures individual household demand cannot be reverse-engineered by suppliers.
          </div>
        </aside>
      </div>
      <p className="muted-disclaimer">
        {mode === 'demo'
          ? 'Live synthetic campaigns showing cooperative procurement scenarios in Rajasthan.'
          : 'Participating in authenticated local exchange pools.'}
      </p>
    </>
  );
}

// ==========================================
// 14. INTELLIGENCE PAGE (META MUSE MODELS)
// ==========================================
function IntelligencePage({
  mode,
  session,
  aiConsent,
  setAiOptIn,
  aiOptIn,
  grantConsent,
  revokeConsent,
  question,
  setQuestion,
  askMeta,
  aiResult,
  busy,
}: {
  mode: 'demo' | 'live';
  session: Session | null;
  aiConsent: boolean;
  setAiOptIn: (v: boolean) => void;
  aiOptIn: boolean;
  grantConsent: () => void;
  revokeConsent: () => void;
  question: AIQuestion;
  setQuestion: (v: AIQuestion) => void;
  askMeta: () => void;
  aiResult: AIExplanation | null;
  busy: boolean;
}) {
  return (
    <>
      <section className="page-intro">
        <div>
          <ShellLabel>THE INTELLIGENCE LAYER</ShellLabel>
          <h1>
            AI that understands.<br />
            <em>Systems that verify.</em>
          </h1>
          <p>
            Meta models interpret complex financial patterns and propose structured next steps. AwnNORA's deterministic kernel strictly protects money, arithmetic, and permissions.
          </p>
        </div>
        <div className="intro-callout">
          <span>MODEL POLICY</span>
          <strong>Standard Mode Strict Guard</strong>
          <small>Contributor mode is never permitted for personal or confidential data.</small>
        </div>
      </section>

      <div className="model-grid">
        <ModelRow
          name="Muse Spark 1.3"
          role="Reasoning, task decomposition and structured explanations"
          status="Active Ready"
          detail="Standard-mode explanation endpoint is implemented. Code-enforced consent checks protect every request."
        />
        <ModelRow
          name="Muse Wonder 1.0"
          role="Long-running mission planning and multi-agent delegation"
          status="GENIEA Pilot"
          detail="Coordinates multi-step dispute resolution, ONDC bids, and government benefit applications."
        />
        <ModelRow
          name="Muse Glimmer"
          role="Local multimodal reasoning for edge &amp; offline processing"
          status="Edge Target"
          detail="Self-hosted open-weight architecture for local on-device verification."
        />
        <ModelRow
          name="Muse Voice Transcribe"
          role="Voice-first intake and user clarification"
          status="Ready"
          detail="Streaming transcription for voice-commanded financial audits and opportunity bids."
        />
        <ModelRow
          name="SAM 3.1"
          role="Visual regions for physical resource and product workflows"
          status="Ready"
          detail="Segmenting physical receipts, utility meters, and artisan inventory."
        />
      </div>

      <div className="ai-workspace">
        <div className="ai-workspace__intro">
          <ShellLabel>PERSONAL REPORT ASSISTANCE</ShellLabel>
          <h2>Ask for an explanation, not a blind guess.</h2>
          <p>
            Muse Spark explains verified findings already computed by AwnNORA. The model cannot alter balances, miscalculate settlements, or bypass human consent.
          </p>
        </div>

        {mode === 'demo' ? (
          <div className="ai-gate">
            <span className="gate-number">01</span>
            <div>
              <strong>Connect a local demo account to try the Meta API.</strong>
              <p>
                The standalone synthetic interface uses verified fixtures. Connect an authenticated workspace to query live Meta model endpoints.
              </p>
            </div>
          </div>
        ) : !session ? (
          <div className="ai-gate">
            <span className="gate-number">02</span>
            <div>
              <strong>Sign in to a verified account.</strong>
              <p>AI assistance is only available through the authenticated backend.</p>
            </div>
          </div>
        ) : !aiConsent ? (
          <div className="consent-gate">
            <div>
              <span className="gate-number">03</span>
              <div>
                <strong>Optional consent: share minimized financial aggregates with Meta Model API.</strong>
                <p>
                  The service sends only aggregate financial totals and genericized finding labels. It never sends account numbers, raw bank statements, contact details, or identity documents.
                </p>
              </div>
            </div>
            <label className="consent-check">
              <input type="checkbox" checked={aiOptIn} onChange={(e) => setAiOptIn(e.target.checked)} />
              <span>I agree to this optional, purpose-specific AI processing.</span>
            </label>
            <button className="primary-button" disabled={!aiOptIn || busy} onClick={grantConsent}>
              {busy ? 'Saving…' : 'Grant optional AI consent'} <span>↗</span>
            </button>
          </div>
        ) : (
          <div className="ai-form">
            <div className="consent-active">
              <StatusDot tone="green" />
              <span>AI ASSISTANCE CONSENT ACTIVE</span>
              <small>Aggregate summary only · Standard mode</small>
              <button className="text-action consent-revoke" disabled={busy} onClick={revokeConsent}>
                Revoke consent
              </button>
            </div>
            <label className="question-label" htmlFor="ai-question">
              Choose what the model should explain
            </label>
            <select
              id="ai-question"
              value={question}
              onChange={(e) => setQuestion(e.target.value as AIQuestion)}
            >
              <option value="prioritize_findings">Prioritize findings and evidence checks</option>
              <option value="explain_cashflow">Explain this period's cashflow</option>
              <option value="review_obligations">Review upcoming obligations</option>
              <option value="understand_data_gaps">Explain missing or incomplete data</option>
            </select>
            <div className="ai-form-footer">
              <small>Model: Muse Spark 1.3 · Standard mode · No tools or external mutations enabled</small>
              <button className="primary-button" disabled={!question.trim() || busy} onClick={askMeta}>
                {busy ? 'Thinking…' : 'Ask Muse Spark'} <span>↗</span>
              </button>
            </div>
            {aiResult && (
              <div className="ai-result">
                <div className="ai-result__header">
                  <strong>Structured explanation</strong>
                  <span>
                    {aiResult.model} · {aiResult.mode}
                  </span>
                </div>
                <p>{aiResult.summary}</p>
                {aiResult.actions.map((action) => (
                  <div className="ai-action" key={action.finding_id}>
                    <span>{action.finding_id}</span>
                    <strong>{action.why_it_matters}</strong>
                    <p>{action.next_step}</p>
                    <small>Uncertainty: {action.uncertainty}</small>
                  </div>
                ))}
                <div className="model-disclaimer">
                  {aiResult.limitations.join(' ')}{' '}
                  {aiResult.external_actions_taken ? 'External actions were taken.' : 'No external action was taken.'}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="intelligence-boundary">
        <strong>Decision boundary</strong>
        <span>Model proposes language &amp; prioritization.</span>
        <b>→</b>
        <span>Application verifies allowed finding IDs and explicit consent.</span>
        <b>→</b>
        <span>Deterministic code owns calculations and immutable state changes.</span>
      </div>
    </>
  );
}

function ModelRow({
  name,
  role,
  status,
  detail,
}: {
  name: string;
  role: string;
  status: string;
  detail: string;
}) {
  return (
    <div className="model-row">
      <div className="model-monogram">
        {name
          .split(' ')
          .map((part) => part[0])
          .slice(0, 2)
          .join('')}
      </div>
      <div className="model-copy">
        <strong>{name}</strong>
        <span>{role}</span>
        <small>{detail}</small>
      </div>
      <span className="model-status">{status}</span>
    </div>
  );
}

// ==========================================
// 15. LOGIN DIALOG (MODAL FALLBACK)
// ==========================================
function LoginDialog({
  busy,
  onClose,
  onLogin,
  onConnected,
}: {
  busy: boolean;
  onClose: () => void;
  onLogin: (email: string, password: string) => void;
  onConnected: (session: Session) => void;
}) {
  const [step, setStep] = useState<'signin' | 'register' | 'verify'>('signin');
  const [email, setEmail] = useState('demo@example.com');
  const [displayName, setDisplayName] = useState('AwnNORA Demo Explorer');
  const [password, setPassword] = useState('Password12345!');
  const [verificationToken, setVerificationToken] = useState('');
  const [pendingSession, setPendingSession] = useState<Session | null>(null);
  const [localBusy, setLocalBusy] = useState(false);
  const [localError, setLocalError] = useState('');
  const [localNotice, setLocalNotice] = useState('');

  const register = async () => {
    setLocalBusy(true);
    setLocalError('');
    setLocalNotice('');
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
    setLocalBusy(true);
    setLocalError('');
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

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section className="login-dialog" role="dialog" aria-modal="true" aria-labelledby="login-title">
        <button className="dialog-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <Mark />
        <ShellLabel>{step === 'verify' ? 'EMAIL CONTROL' : 'PRIVATE ACCOUNT CONNECTION'}</ShellLabel>
        <h2 id="login-title">
          {step === 'verify' ? (
            <>
              Verify your
              <br />
              <em>email address.</em>
            </>
          ) : (
            <>
              Your personal
              <br />
              <em>economic space.</em>
            </>
          )}
        </h2>
        <p>
          {step === 'verify'
            ? 'Enter the one-time verification token delivered to the address you registered.'
            : 'Your account is private by default. Credentials are sent only to your configured AwnNORA API.'}
        </p>
        {localNotice && <div className="dialog-notice">{localNotice}</div>}
        {localError && (
          <div className="dialog-error" role="alert">
            {localError}
          </div>
        )}

        {step === 'verify' ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void verify();
            }}
          >
            <label>
              Verification token
              <input
                type="text"
                required
                minLength={32}
                maxLength={128}
                value={verificationToken}
                onChange={(e) => setVerificationToken(e.target.value)}
                autoComplete="one-time-code"
              />
            </label>
            <button className="primary-button primary-button--full" disabled={localBusy}>
              {localBusy ? 'Verifying…' : 'Verify and continue'} <span>↗</span>
            </button>
            <button type="button" className="text-action dialog-back" onClick={() => setStep('signin')}>
              Back to sign in
            </button>
          </form>
        ) : (
          <>
            <div className="dialog-tabs">
              <button
                type="button"
                className={step === 'signin' ? 'is-active' : ''}
                onClick={() => {
                  setStep('signin');
                  setLocalError('');
                }}
              >
                Sign in
              </button>
              <button
                type="button"
                className={step === 'register' ? 'is-active' : ''}
                onClick={() => {
                  setStep('register');
                  setLocalError('');
                }}
              >
                Create account
              </button>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (step === 'signin') onLogin(email.trim(), password);
                else void register();
              }}
            >
              {step === 'register' && (
                <label>
                  Your name
                  <input
                    type="text"
                    required
                    minLength={1}
                    maxLength={80}
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    autoComplete="name"
                  />
                </label>
              )}
              <label>
                Email
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="username"
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  required
                  minLength={12}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete={step === 'signin' ? 'current-password' : 'new-password'}
                />
              </label>
              <button className="primary-button primary-button--full" disabled={busy || localBusy}>
                {busy || localBusy ? 'Connecting…' : step === 'signin' ? 'Sign in' : 'Create private account'} <span>↗</span>
              </button>
            </form>
            <div className="login-footnote">
              Connected to local/production AwnNORA server. Use demo@example.com / Password12345! for pre-seeded test data.
            </div>
          </>
        )}
      </section>
    </div>
  );
}

export default App;
