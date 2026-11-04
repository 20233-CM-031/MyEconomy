import type { GuardianCase, PersonalCaseDetail, PowerReport } from './types';

export const demoReport: PowerReport = {
  report_version: 'personal-power-v1',
  currency: 'INR',
  period_start: '2026-10-01',
  period_end: '2026-10-31',
  as_of: '2026-11-04',
  account_count: 2,
  posted_transaction_count: 86,
  income_total: '72000.00',
  gross_expenses: '58450.00',
  refunds: '1250.00',
  net_expenses_after_refunds: '57200.00',
  essential_expenses: '43100.00',
  discretionary_expenses: '15350.00',
  net_cashflow: '14800.00',
  upcoming_essential_obligations: '12600.00',
  upcoming_obligation_count: 5,
  potential_duplicate_count: 2,
  verified_value_created: '0.00',
  findings: [
    {
      finding_id: 'DUP-001', code: 'POSSIBLE_DUPLICATE_TRANSACTION', priority: 'MEDIUM',
      title: 'A payment may have been recorded twice',
      explanation: 'Two posted entries share a transaction fingerprint. This is a review signal, not proof of a double charge.',
      recommended_next_step: 'Compare the two entries with the original bank statement or merchant receipt before raising a dispute.',
      amount: '649.00', currency: 'INR', source_references: ['SYNTH-TX-0204', 'SYNTH-TX-0188'], value_status: 'NOT_A_VALUE_OUTCOME',
    },
    {
      finding_id: 'CASH-002', code: 'ESSENTIAL_COST_PRESSURE', priority: 'LOW',
      title: 'Upcoming essentials need a quick review',
      explanation: 'Five recurring obligations fall within the next 30 days. Their total is shown separately from this month’s posted spending.',
      recommended_next_step: 'Review the due dates and confirm the amounts still match the provider terms.',
      amount: '12600.00', currency: 'INR', source_references: ['SYNTH-OBL-001', 'SYNTH-OBL-004'], value_status: 'NOT_A_VALUE_OUTCOME',
    },
    {
      finding_id: 'DATA-002', code: 'UNCLASSIFIED_CREDIT', priority: 'INFO',
      title: 'One credit is not classified as income',
      explanation: 'The import contains an incoming credit that was left unclassified. AwnNORA has not assumed it is salary.',
      recommended_next_step: 'Check the source entry and classify it only when you know what it represents.',
      amount: '2400.00', currency: 'INR', source_references: ['SYNTH-TX-0301'], value_status: 'NOT_A_VALUE_OUTCOME',
    },
  ],
  read_only: true,
  external_actions_taken: false,
  commons_required: false,
  limitations: [
    'This synthetic report is a demonstration fixture, not a real household statement.',
    'Potential savings and duplicate candidates are not counted as verified value.',
    'No external provider, bank, employer, insurer, government or payment system was contacted.',
  ],
};

export const demoCases: GuardianCase[] = [
  {
    id: 'SYN-CASE-001', case_type: 'INVOICE_REVIEW', invoice_id: 'DFC-DEMO-1101',
    provider_key: 'demo-connectivity-provider', currency: 'INR', issue_date: '2026-11-01',
    disposition: 'REVIEW_REQUIRED', status: 'DRAFT_AVAILABLE', evidence_document_id: 'SYN-EVIDENCE-01',
    findings: [{ code: 'UNUSUAL_INCREASE', severity: 'MEDIUM', message: 'The amount is materially higher than the prior comparable fixture invoice.' }],
    disclaimer: 'Synthetic demonstration only. This is not a finding of fraud or legal wrongdoing.',
    action_draft: null, created_at: '2026-11-04T09:00:00Z', updated_at: '2026-11-04T09:00:00Z',
  },
  {
    id: 'SYN-CASE-002', case_type: 'INVOICE_REVIEW', invoice_id: 'DFC-DEMO-ARITH-03',
    provider_key: 'demo-connectivity-provider', currency: 'INR', issue_date: '2026-11-02',
    disposition: 'REVIEW_REQUIRED', status: 'REVIEW_REQUIRED', evidence_document_id: 'SYN-EVIDENCE-02',
    findings: [{ code: 'LINE_ARITHMETIC_MISMATCH', severity: 'HIGH', message: 'Quantity × unit price does not reconcile with the declared line amount.' }],
    disclaimer: 'Synthetic demonstration only. Verify the original document before acting.',
    action_draft: null, created_at: '2026-11-04T10:00:00Z', updated_at: '2026-11-04T10:00:00Z',
  },
];

export const demoObligations = [
  { name: 'Home rent', amount: 8500, date: 'Nov 05', type: 'Essential' },
  { name: 'Electricity', amount: 1800, date: 'Nov 08', type: 'Essential' },
  { name: 'Internet', amount: 900, date: 'Nov 12', type: 'Essential' },
  { name: 'Education fee', amount: 1400, date: 'Nov 17', type: 'Essential' },
];

export const demoMonthly = [
  { month: 'Jun', income: 65000, spend: 54800 },
  { month: 'Jul', income: 68000, spend: 57100 },
  { month: 'Aug', income: 68000, spend: 59200 },
  { month: 'Sep', income: 70000, spend: 58600 },
  { month: 'Oct', income: 72000, spend: 57200 },
];

export const demoPersonalCases: PersonalCaseDetail[] = [
  {
    id: 'SYN-CASE-LOCAL-001', source_engine: 'PERSONAL', source_finding_id: 'DUP-001',
    title: 'A payment may have been recorded twice', currency: 'INR', amount_minor: '64900',
    source_snapshot: {
      finding_id: 'DUP-001', code: 'POSSIBLE_DUPLICATE_TRANSACTION', priority: 'MEDIUM',
      title: 'A payment may have been recorded twice',
      explanation: 'Two synthetic posted entries share a transaction fingerprint. This is a review signal, not proof of double charging.',
      recommended_next_step: 'Compare the original statement and merchant receipt before raising a dispute.',
      amount: '649.00', currency: 'INR', source_references: ['SYNTH-TX-0204', 'SYNTH-TX-0188'],
      value_status: 'NOT_A_VALUE_OUTCOME',
      report_period: { period_start: '2026-10-01', period_end: '2026-10-31', as_of: '2026-11-04' },
      origin: 'SYNTHETIC_DEMO_FIXTURE',
    },
    status: 'IN_REVIEW', state_version: 2,
    created_at: '2026-11-04T08:30:00.000Z', updated_at: '2026-11-04T09:10:00.000Z',
    events: [
      { id: 'SYN-CASE-LOCAL-001-E1', event_sequence: 1, event_type: 'CASE_OPENED', from_status: null, to_status: 'OPEN', note: 'Opened from a synthetic Power Report finding.', created_at: '2026-11-04T08:30:00.000Z' },
      { id: 'SYN-CASE-LOCAL-001-E2', event_sequence: 2, event_type: 'STATUS_CHANGED', from_status: 'OPEN', to_status: 'IN_REVIEW', note: 'The source statement is being compared. No provider has been contacted.', created_at: '2026-11-04T09:10:00.000Z' },
    ],
  },
  {
    id: 'SYN-CASE-LOCAL-002', source_engine: 'PERSONAL', source_finding_id: 'CASH-002',
    title: 'Upcoming essentials need a quick review', currency: 'INR', amount_minor: '1260000',
    source_snapshot: {
      finding_id: 'CASH-002', code: 'ESSENTIAL_COST_PRESSURE', priority: 'LOW',
      title: 'Upcoming essentials need a quick review',
      explanation: 'Five synthetic recurring obligations fall within the review horizon. Their total is separate from posted spending.',
      recommended_next_step: 'Confirm due dates and amounts with the original provider before making a payment decision.',
      amount: '12600.00', currency: 'INR', source_references: ['SYNTH-OBL-001', 'SYNTH-OBL-004'],
      value_status: 'NOT_A_VALUE_OUTCOME',
      report_period: { period_start: '2026-10-01', period_end: '2026-10-31', as_of: '2026-11-04' },
      origin: 'SYNTHETIC_DEMO_FIXTURE',
    },
    status: 'OPEN', state_version: 1,
    created_at: '2026-11-04T10:00:00.000Z', updated_at: '2026-11-04T10:00:00.000Z',
    events: [
      { id: 'SYN-CASE-LOCAL-002-E1', event_sequence: 1, event_type: 'CASE_OPENED', from_status: null, to_status: 'OPEN', note: 'Opened from a synthetic upcoming-obligation finding.', created_at: '2026-11-04T10:00:00.000Z' },
    ],
  },
];
