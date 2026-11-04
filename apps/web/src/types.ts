export type ViewKey =
  | 'intro'
  | 'tour'
  | 'auth'
  | 'assistant'
  | 'accounts'
  | 'overview'
  | 'casebook'
  | 'protection'
  | 'opportunity'
  | 'entitlements'
  | 'enterprise'
  | 'commons'
  | 'intelligence';

export type TourChapter = {
  id: string;
  stepNumber: number;
  title: string;
  subtitle: string;
  tag: string;
  tagColor: string;
  description: string;
  highlights: string[];
  metrics: Array<{ label: string; value: string; tone?: string }>;
  interactiveView: ViewKey;
  actionLabel: string;
};

export type AdSenseMonetizationStream = {
  publisher_id: string;
  channel_name: string;
  monthly_impressions: string;
  average_ecpm: string;
  net_monthly_yield: string;
  offset_target_obligation: string;
  status: 'ACTIVE_YIELD' | 'OPTIMIZING';
  last_payout_date: string;
};

export type RailIntegrationMethod =
  | 'ACCOUNT_AGGREGATOR_REBIT'
  | 'UPI_AUTOPAY_MANDATE'
  | 'CARD_ON_FILE_COFT'
  | 'STRIPE_CONNECT_OAUTH'
  | 'GOOGLE_ADSENSE_PAYMENT';

export type RailType = 'upi' | 'bank' | 'card' | 'global' | 'wallet';

export type ConnectedRail = {
  id: string;
  name: string;
  type: RailType;
  provider: string;
  masked_identifier: string;
  balance_minor: string;
  balance_formatted: string;
  currency: string;
  status: 'ACTIVE' | 'SYNCING' | 'ATTENTION_REQUIRED';
  color: string;
  accent_gradient: string;
  icon_label: string;
  last_activity: string;
  is_default?: boolean;
};

export type LiveEconomicEvent = {
  id: string;
  timestamp: string;
  engine: 'GUARDIAN' | 'OPPORTUNITY' | 'ENTITLEMENT' | 'COMMONS' | 'ENTERPRISE' | 'RAILS';
  title: string;
  description: string;
  amount: string | null;
  tone: 'positive' | 'warning' | 'info' | 'accent';
  action_label?: string;
  action_view?: ViewKey;
};

export type LiveOpportunity = {
  id: string;
  title: string;
  source: 'Skill India Digital' | 'ONDC Open Network' | 'National Benefit Portal' | 'Freelance Escrow' | 'Local Jaipur Exchange';
  category: 'Tech & Software' | 'Education & Tutoring' | 'Logistics & Delivery' | 'Govt Grant' | 'Artisan & Craft';
  match_score: number;
  rate: string;
  estimated_monthly_value: string;
  skills_required: string[];
  location: string;
  spots_left: number;
  verified_source: boolean;
};

export type LiveEntitlement = {
  id: string;
  title: string;
  scheme_code: string;
  ministry: string;
  benefit_type: 'Direct Cash Transfer' | 'Health Insurance' | 'Interest Subsidy' | 'Education Grant';
  value_annual: string;
  eligibility_status: 'VERIFIED_ELIGIBLE' | 'APPLICATION_READY' | 'ACTIVE_BENEFIT';
  deadline: string;
  action_cta: string;
};

export type CommonsCampaign = {
  id: string;
  title: string;
  category: string;
  participants_joined: number;
  target_quorum: number;
  potential_savings_percent: number;
  estimated_savings: string;
  locality: string;
  expires_in: string;
  status: 'ACTIVE_GATHERING' | 'QUORUM_REACHED' | 'DISPATCHED';
};

export type AIAssistantMessage = {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  actionCard?: {
    title: string;
    description: string;
    actionType: 'NAVIGATE' | 'OPEN_CASE' | 'CONNECT_RAIL' | 'CLAIM_BENEFIT';
    targetView?: ViewKey;
    buttonLabel: string;
    payload?: Record<string, unknown>;
  };
};

export type Finding = {
  finding_id: string;
  code: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO' | string;
  title: string;
  explanation: string;
  recommended_next_step: string;
  amount: string | null;
  currency: string | null;
  source_references: string[];
  value_status: string;
};

export type PowerReport = {
  report_version: string;
  currency: string;
  period_start: string;
  period_end: string;
  as_of: string;
  account_count: number;
  posted_transaction_count: number;
  income_total: string;
  gross_expenses: string;
  refunds: string;
  net_expenses_after_refunds: string;
  essential_expenses: string;
  discretionary_expenses: string;
  net_cashflow: string;
  upcoming_essential_obligations: string;
  upcoming_obligation_count: number;
  potential_duplicate_count: number;
  verified_value_created: string;
  findings: Finding[];
  read_only: boolean;
  external_actions_taken: boolean;
  commons_required: boolean;
  limitations: string[];
};

export type User = {
  id: string;
  email: string;
  display_name: string;
  email_verified: boolean;
};

export type Session = {
  access_token: string;
  user: User;
};

export type GuardianCase = {
  id: string;
  case_type: string;
  invoice_id: string | null;
  provider_key: string;
  currency: string;
  issue_date: string;
  disposition: string;
  status: string;
  evidence_document_id: string;
  findings: Array<{ code: string; severity: string; message: string }>;
  disclaimer: string;
  action_draft: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type AIQuestion = 'prioritize_findings' | 'explain_cashflow' | 'review_obligations' | 'understand_data_gaps';

export type AIAction = {
  finding_id: string;
  why_it_matters: string;
  next_step: string;
  uncertainty: string;
};

export type AIExplanation = {
  model: 'muse-spark-1.3';
  mode: 'STANDARD';
  summary: string;
  actions: AIAction[];
  limitations: string[];
  external_actions_taken: false;
};


export type FinancialAccount = {
  id: string;
  account_name: string;
  account_type: string;
  currency: string;
  institution_label: string | null;
  masked_reference: string | null;
  opening_balance: string;
  opening_balance_as_of: string | null;
  status: string;
  source_type: string;
  created_at: string;
};

export type ImportBatch = {
  batch_id: string;
  status: string;
  source_sha256: string;
  row_count: number;
  inserted_count: number;
  updated_count: number;
  duplicate_count: number;
  potential_duplicate_count: number;
  replayed: boolean;
  validation_errors: Array<{ row_number: number; code: string; message: string }>;
};

export type PersonalCaseStatus =
  | 'OPEN' | 'IN_REVIEW' | 'ACTION_READY' | 'WAITING_FOR_USER'
  | 'WAITING_EXTERNAL' | 'RESOLVED' | 'CLOSED';

export type PersonalCaseFindingSnapshot = {
  finding_id: string;
  code: string;
  priority: string;
  title: string;
  explanation: string;
  recommended_next_step: string;
  amount: string | null;
  currency: string | null;
  source_references: string[];
  value_status: string;
  report_period: { period_start: string; period_end: string; as_of: string };
  origin: 'SERVER_COMPUTED_PERSONAL_POWER_REPORT' | 'SYNTHETIC_DEMO_FIXTURE';
};

export type PersonalCaseEvent = {
  id: string;
  event_sequence: number;
  event_type: 'CASE_OPENED' | 'STATUS_CHANGED';
  from_status: PersonalCaseStatus | null;
  to_status: PersonalCaseStatus;
  note: string | null;
  created_at: string;
};

export type PersonalCase = {
  id: string;
  source_engine: string;
  source_finding_id: string;
  title: string;
  source_snapshot: PersonalCaseFindingSnapshot;
  currency: string;
  amount_minor: string | null;
  status: PersonalCaseStatus;
  state_version: number;
  created_at: string;
  updated_at: string;
  replayed?: boolean;
};

export type PersonalCaseDetail = PersonalCase & { events: PersonalCaseEvent[] };
