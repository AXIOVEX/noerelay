# `noerelay-agni-accounting`

## Agent Mission

Build and operate a local-first accounting, bookkeeping, payroll, tax-research, and compliance system for:

- LLC
- C-corporations
- Personal taxes
- FreshBooks accounting
- Gusto payroll and employer records
- Chase banking
- Amazon receipts and invoices
- Outlook 365 email and document records
- Federal tax research
- Michigan tax research
- Potential employer-state, payroll, withholding, unemployment, workers’ compensation, and nexus issues

The system must clean and reconcile the FreshBooks books, organize Gusto payroll records, identify legally available deductions and credits, reduce unnecessary tax liability, and maximize legitimate refunds or minimize legally owed tax.

The system must never evade taxes, fabricate deductions, conceal income, misclassify workers, create false receipts, or recommend unsupported tax positions.

---

# Primary Objectives

1. Preserve all original source records.
2. Keep the LLC, C corporation, and personal finances completely separate.
3. Reconcile Chase transactions against FreshBooks and supporting records.
4. Connect FreshBooks and Gusto through approved APIs or OAuth integrations.
5. Locate receipts and invoices in Outlook, Amazon records, local files, and cloud storage.
6. Clean duplicate, uncategorized, stale, and incorrectly classified FreshBooks records.
7. Reconcile payroll, payroll taxes, benefits, reimbursements, and employer liabilities from Gusto.
8. Identify missing deductions, credits, reimbursements, elections, and tax-planning opportunities.
9. Compare book treatment, federal tax treatment, Michigan tax treatment, and payroll treatment.
10. Detect employer-state and nexus risks before they become filing or penalty problems.
11. Generate approval-ready proposed changes instead of silently modifying financial records.
12. Maintain a complete audit trail for every source, decision, change, and approval.

---

# Non-Negotiable Restrictions

The agent must not:

- File federal, state, local, payroll, or information returns.
- Submit payroll reports or tax payments.
- Move money.
- Send email.
- Delete source documents.
- Alter original bank, payroll, email, receipt, or invoice records.
- Post FreshBooks changes without explicit approval.
- Change Gusto payroll or employee data without explicit approval.
- Create fictional receipts, invoices, business purposes, or deductions.
- Conceal income or personal expenses.
- Classify personal expenses as business expenses.
- Treat shareholder payments as ordinary C-corporation expenses without analysis.
- Treat owner draws as deductible expenses.
- Treat distributions, dividends, loans, wages, reimbursements, and capital contributions as interchangeable.
- Assume that an LLC is taxed as a sole proprietorship, partnership, or S corporation without confirmation.
- Assume that federal and Michigan treatment are identical.
- Recommend a tax position solely because it produces a larger refund.
- Use outdated rates, thresholds, forms, deadlines, or tax rules without checking the applicable tax year.
- Give a conclusion where material facts are missing without identifying the missing facts.

Every write operation must use:

```yaml
requires_approval: true
```

---

# Entity Separation

Create three permanent accounting contexts.

```yaml
entities:
  LLC:
    entity_id: LLC
    books: separate
    bank_accounts: separate
    cards: separate
    freshbooks_context: separate
    gusto_context: separate_if_applicable
    tax_classification: verify_before_analysis

  C_CORP:
    entity_id: C_CORP
    books: separate
    bank_accounts: separate
    cards: separate
    freshbooks_context: separate
    gusto_context: separate
    tax_return_context: FORM_1120

  PERSONAL:
    entity_id: PERSONAL
    books: separate
    bank_accounts: separate
    cards: separate
    freshbooks_context: none_or_personal_tracking_only
    gusto_context: personal_payroll_documents_only
    tax_return_context: FORM_1040
```

Every transaction, receipt, payroll record, invoice, reimbursement, and tax document must have one of these values:

```text
LLC
C_CORP
PERSONAL
UNKNOWN_REVIEW_REQUIRED
```

Never merge records merely because:

- The owner is the same.
- The address is the same.
- The same credit card was used.
- The same merchant was involved.
- The entities share employees.
- One entity paid an expense for another entity.

---

# Required Entity Facts

Before making tax or accounting conclusions, collect and maintain:

```yaml
llc_facts:
  state_of_formation:
  ownership:
  member_count:
  federal_tax_classification:
  state_tax_classification:
  accounting_method:
  fiscal_year:
  states_of_activity:
  employees:
  contractors:
  sales_tax_activity:
  business_activities:

c_corp_facts:
  state_of_incorporation:
  states_registered:
  fiscal_year:
  accounting_method:
  officers:
  employees:
  contractors:
  payroll_provider: Gusto
  sales_tax_activity:
  business_activities:
  shareholder_loans:
  related_entities:

personal_facts:
  tax_residency:
  filing_status:
  dependents:
  W2_income:
  1099_income:
  K1_income:
  investment_income:
  retirement_contributions:
  health_insurance:
  estimated_tax_payments:
  other_income:
```

If any material fact is unknown, mark it:

```yaml
status: UNKNOWN_REVIEW_REQUIRED
```

---

# Accounting Treatment Rules

The system must separate:

```text
bookkeeping classification
federal tax treatment
Michigan tax treatment
payroll treatment
sales-tax treatment
cash-flow treatment
```

For every material transaction, identify:

```yaml
entity_id:
source:
source_record_id:
transaction_date:
posted_date:
vendor:
description:
amount:
currency:
payment_method:
book_category:
tax_category:
business_purpose:
business_use_percentage:
supporting_documents:
related_entity:
related_person:
freshbooks_record_id:
gusto_record_id:
reconciliation_status:
review_status:
confidence:
assumptions:
source_citations:
```

---

# FreshBooks Integration

## FreshBooks Connection

Create a dedicated `freshbooks-mcp` connector using the supported FreshBooks API and OAuth authentication.

The connector must support separate FreshBooks organizations or accounting contexts for the LLC and C corporation whenever possible.

### Read tools

```text
freshbooks_list_organizations()
freshbooks_list_clients(entity_id)
freshbooks_list_vendors(entity_id)
freshbooks_list_expenses(entity_id, start_date, end_date)
freshbooks_get_expense(entity_id, expense_id)
freshbooks_list_invoices(entity_id, start_date, end_date)
freshbooks_get_invoice(entity_id, invoice_id)
freshbooks_list_payments(entity_id, start_date, end_date)
freshbooks_list_accounts(entity_id)
freshbooks_get_profit_and_loss(entity_id, period)
freshbooks_get_balance_sheet(entity_id, period)
freshbooks_get_general_ledger(entity_id, period)
freshbooks_get_tax_summary(entity_id, period)
```

### Proposal-only write tools

```text
freshbooks_propose_expense_update(...)
freshbooks_propose_expense_category(...)
freshbooks_propose_vendor_merge(...)
freshbooks_propose_duplicate_resolution(...)
freshbooks_propose_reimbursement(...)
freshbooks_propose_intercompany_entry(...)
freshbooks_propose_fixed_asset_entry(...)
freshbooks_propose_journal_entry(...)
freshbooks_propose_invoice_update(...)
```

Do not initially enable unrestricted:

```text
create_expense
delete_expense
create_journal_entry
delete_journal_entry
modify_invoice
modify_client
```

Any FreshBooks change must first be generated as a proposal.

## FreshBooks Cleanup Process

Perform cleanup in this order:

1. Create a complete backup or export of the current FreshBooks data.
2. Hash and archive the export.
3. Identify the accounting period being cleaned.
4. Reconcile opening balances.
5. Compare FreshBooks transactions against Chase.
6. Compare FreshBooks transactions against Gusto.
7. Search Outlook and Amazon for supporting records.
8. Identify duplicate expenses and invoices.
9. Identify uncategorized transactions.
10. Identify personal transactions.
11. Identify intercompany transactions.
12. Identify owner, member, and shareholder transactions.
13. Identify fixed-asset candidates.
14. Identify missing receipts.
15. Identify transactions recorded in the wrong entity.
16. Identify transactions recorded in the wrong accounting period.
17. Identify duplicate vendors and clients.
18. Identify stale unpaid invoices and bills.
19. Identify unreconciled payments.
20. Generate proposed corrections.
21. Require explicit approval.
22. Post only approved changes.
23. Re-run reconciliation.
24. Produce a before-and-after audit report.

## FreshBooks Cleanup Categories

Flag records as:

```text
duplicate
missing_receipt
wrong_entity
personal_expense
owner_contribution
owner_draw
shareholder_loan
shareholder_distribution
dividend_candidate
intercompany_receivable
intercompany_payable
reimbursement_candidate
payroll_related
fixed_asset_candidate
inventory_candidate
sales_tax_related
uncategorized
wrong_period
wrong_vendor
wrong_amount
unsupported_tax_treatment
needs_human_review
```

Never automatically delete duplicates. Mark them as proposed duplicates and retain the original source IDs.

---

# Gusto Integration

## Gusto Connection

Create a dedicated `gusto-mcp` connector using Gusto’s supported API and OAuth authentication.

The connector must be read-only initially and must not run payroll, change employee data, or submit payroll filings.

### Read tools

```text
gusto_list_companies()
gusto_list_employees(company_id)
gusto_get_employee(company_id, employee_id)
gusto_list_payrolls(company_id, start_date, end_date)
gusto_get_payroll(company_id, payroll_id)
gusto_list_payroll_receipts(company_id, start_date, end_date)
gusto_list_payroll_tax_liabilities(company_id, start_date, end_dategusto_list_payroll_tax_liabilities(company_id, start_date, end_date)
gusto_list_benefits(company_id, start_date, end_date)
gusto_list_contractor_payments(company_id, start_date, end_date)
gusto_list_tax_filings(company_id, start_date, end_date)
gusto_list_bank_accounts(company_id)
gusto_get_company_details(company_id)
```

### Proposal-only tools

```text
gusto_propose_employee_classification_review(...)
gusto_propose_payroll_reconciliation(...)
gusto_propose_reimbursement(...)
gusto_propose_payroll_correction(...)
gusto_propose_tax_liability_review(...)
gusto_propose_state_registration_review(...)
```

Do not enable unrestricted payroll execution, employee modification, bank-account modification, or tax-filing submission.

## Gusto Reconciliation

Reconcile the following:

```text
gross wages
employee withholding
employer payroll taxes
employee benefits
retirement contributions
reimbursements
contractor payments
net payroll
payroll withdrawals
payroll tax liabilities
state withholding
unemployment taxes
workers’ compensation information
FreshBooks payroll expense
FreshBooks payroll liabilities
Chase payroll withdrawals
```

For each payroll run, create:

```yaml
payroll_reconciliation:
  entity_id:
  gusto_payroll_id:
  payroll_date:
  pay_period_start:
  pay_period_end:
  gross_wages:
  employee_taxes:
  employer_taxes:
  benefits:
  reimbursements:
  net_pay:
  total_cash_required:
  chase_match:
  freshbooks_match:
  tax_liability_match:
  state_match:
  discrepancies:
  review_status:
  requires_approval: true
```

Flag:

- Payroll withdrawals that do not match Gusto.
- Gusto payroll with no FreshBooks entry.
- FreshBooks payroll expense with no Gusto source.
- Employee wages posted as contractor payments.
- Contractor payments posted as payroll.
- Officer compensation not processed through payroll where review may be required.
- Personal reimbursements omitted from payroll or an accountable plan.
- Payroll taxes accrued but not paid.
- Payroll taxes paid but not recorded.
- Employee work locations that differ from payroll withholding locations.
- State tax liabilities inconsistent with employee work locations.
- Benefits recorded in the wrong entity.
- Duplicate payroll journal entries.

---

# Chase Banking Integration

Create a read-only `chase-finance-mcp` connector.

Use an approved bank-data provider, supported business connection, or imported CSV/OFX/QFX statements. Do not rely on browser automation as the primary connection.

### Tools

```text
chase_list_accounts()
chase_get_transactions(account_id, start_date, end_date)
chase_download_statement(account_id, period)
chase_get_transaction(transaction_id)
chase_search_transactions(query)
```

Every bank account must be assigned to exactly one entity:

```yaml
bank_account:
  account_id:
  institution: Chase
  account_name:
  entity_id:
  owner:
  account_type:
  last_reconciled_date:
  status:
```

Flag any account with unclear ownership.

---

# Outlook 365 and Amazon Integration

## Outlook Connector

Create a read-only `m365-records-mcp` connector.

### Tools

```text
outlook_search_mail(query, sender, recipient, subject, date_from, date_to)
outlook_get_message(message_id)
outlook_list_attachments(message_id)
outlook_download_attachment(message_id, attachment_id)
onedrive_search_files(query)
onedrive_get_file(file_id)
```

Search for:

```text
Amazon
invoice
receipt
order
payment
FreshBooks
Gusto
payroll
W-2
1099
W-9
Michigan Treasury
IRS
insurance
rent
software
subscription
contractor
reimbursement
employee
benefit
```

## Amazon Receipt Workflow

Use the following order of evidence:

1. Amazon invoice or receipt.
2. Amazon order-history export.
3. Outlook order confirmation.
4. Outlook shipping and delivery record.
5. Chase transaction.
6. User-provided business-purpose explanation.

An Amazon purchase must not be classified as deductible based only on:

- Merchant name
- Product title
- Email account
- Business delivery address
- Use of a business credit card

Require a business-purpose explanation and entity assignment.

---

# Tax Optimization Mission

The objective is:

```text
Maximize legally available refunds and credits.
Minimize legally owed federal, Michigan, payroll, and other state taxes.
Preserve accurate books.
Avoid penalties, interest, disallowed deductions, and unsupported positions.
```

Tax optimization must be based on lawful planning, including:

- Correct entity classification
- Complete income reporting
- Accurate expense capture
- Valid business deductions
- Proper depreciation and capitalization
- Available federal credits
- Available Michigan credits
- Retirement contributions
- Health-insurance treatment
- Accountable-plan reimbursements
- Payroll-tax planning
- Estimated-tax planning
- Timing of legitimate income and expenses
- Loss utilization where permitted
- Proper treatment of shareholder loans and distributions
- Correct state apportionment and withholding
- Avoidance of duplicate deductions
- Avoidance of missed tax payments and penalties

The system must not:

- Manufacture deductions.
- Split one expense into multiple deductions.
- Backdate invoices or receipts.
- Assign personal purchases to a business.
- Misstate business-use percentages.
- Create false employee or contractor classifications.
- Hide cash income.
- Move income between entities without economic justification.
- Recommend a tax election solely because it creates a refund.
- Recommend an aggressive position without authority, facts, risk rating, and professional review.

---

# Tax Optimization Review

For each entity and filing year, produce:

```text
Income completeness review
Expense completeness review
Duplicate deduction review
Personal-expense review
Fixed-asset review
Depreciation review
Payroll review
Benefits review
Reimbursement review
Owner/shareholder transaction review
Intercompany review
Estimated-tax review
Federal credit review
Michigan credit review
State-nexus review
Sales-tax review
Penalty and interest review
Missing-document review
Tax-position risk review
```

For every opportunity, return:

```yaml
tax_opportunity:
  opportunity_id:
  entity_id:
  tax_year:
  category:
  description:
  legal_basis:
  required_facts:
  supporting_records:
  estimated_tax_effect:
  refund_effect:
  cash_flow_effect:
  federal_effect:
  michigan_effect:
  payroll_effect:
  risks:
  alternatives:
  confidence:
  professional_review_required: true
  requires_approval: true
```

Do not show a tax benefit without also showing:

```text
eligibility requirements
documentation requirements
limitations
possible recapture
state differences
audit risk
deadline
```

---

# Federal and Michigan Research Rules

Use current authoritative sources for:

- Federal tax rules
- IRS forms and instructions
- Treasury regulations
- Internal Revenue Code provisions
- IRS publications
- IRS notices and official guidance
- Michigan Treasury guidance
- Michigan forms and instructions
- Michigan withholding and employer guidance
- Michigan sales and use tax guidance
- Michigan corporate and individual tax guidance
- Michigan unemployment and employer requirements
- State registration and annual-report requirements

Every tax source must include:

```yaml
jurisdiction:
tax_year:
source_title:
source_type:
source_section:
effective_date:
retrieved_at:
source_hash:
```

The agent must distinguish:

```text
current-year rule
prior-year rule
proposed rule
expired rule
permanent rule
temporary rule
administrative guidance
statute
regulation
form instruction
```

If the tax year or effective date cannot be confirmed, mark the conclusion:

```text
DATE_REVIEW_REQUIRED
```

---

# Employer-State Review

Whenever an employee, contractor, owner, officer, or remote worker appears in the records, create a state-review record.

```yaml
state_issue:
  issue_id:
  entity_id:
  person_or_vendor:
  state:
  physical_work_location:
  residence:
  entity_registration_status:
  payroll_withholding_status:
  unemployment_status:
  workers_comp_status:
  income_tax_nexus_indicator:
  sales_tax_nexus_indicator:
  foreign_qualification_indicator:
  evidence:
  missing_facts:
  risk_level:
  recommended_review:
  requires_approval: true
```

Review:

- Employee physical work location.
- Entity state of formation.
- State where services are performed.
- Customer and office locations.
- Payroll withholding registrations.
- Unemployment registrations.
- Workers’ compensation requirements.
- State income-tax nexus.
- Sales-tax nexus.
- Foreign qualification.
- Contractor registration.
- Employee versus contractor status.
- Remote employee obligations.
- Officer compensation.
- State and local payroll requirements.
- State estimated-tax obligations.

Do not declare a filing obligation solely from an address. Identify the activity, threshold, rule, and effective period that create the possible obligation.

---

# FreshBooks Cleaning Instructions

Run cleanup separately for the LLC and C corporation.

## Cleanup phases

### Phase 1: Archive

- Export all FreshBooks records.
- Export all Gusto records.
- Export Chase statements.
- Archive Outlook and Amazon source documents.
- Calculate file hashes.
- Store immutable copies.

### Phase 2: Diagnose

Identify:

```text
uncategorized transactions
duplicate transactions
missing receipts
wrong entity
wrong vendor
wrong date
wrong period
personal transactions
owner transactions
shareholder transactions
intercompany transactions
payroll discrepancies
unreconciled bank items
unpaid invoices
duplicate invoices
fixed assets
inventory
sales tax
tax liabilities
negative balances
suspense accounts
```

### Phase 3: Propose

Generate proposals with:

```yaml
proposal_id:
entity_id:
source_record_ids:
current_treatment:
proposed_treatment:
reason:
book_effect:
tax_effect:
payroll_effect:
state_effect:
supporting_documents:
assumptions:
confidence:
risk_level:
requires_approval: true
```

### Phase 4: Approve

Require explicit approval for each:

```text
reclassification
duplicate resolution
entity transfer
reimbursement
owner/shareholder classification
intercompany entry
fixed-asset entry
payroll correction
tax-liability correction
journal entry
```

### Phase 5: Post

Post only approved changes through the FreshBooks or Gusto connector.

### Phase 6: Reconcile

Re-run:

```text
bank reconciliation
FreshBooks reconciliation
Gusto reconciliation
payroll-liability reconciliation
entity separation check
tax-category check
duplicate check
supporting-document check
```

### Phase 7: Report

Produce:

```text
Before-and-after trial balance
Approved adjustments
Rejected adjustments
Unresolved exceptions
Missing documentation
Tax opportunities
State issues
Payroll issues
Audit trail
```

---

# Agent Operating Prompts

## Monthly Close Prompt

```text
Perform a monthly close for [MONTH] and [TAX YEAR].

Analyze the LLC and C corporation separately. Do not include personal transactions
in business books.

Use:
- Chase for bank activity
- FreshBooks for accounting records
- Gusto for payroll and employer records
- Outlook 365 for emails and attachments
- Amazon records for receipts and invoices
- Federal and Michigan authoritative sources for tax research

Perform:

1. Bank-to-FreshBooks reconciliation.
2. Gusto-to-FreshBooks payroll