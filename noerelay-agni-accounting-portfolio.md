# noerelay-agni-accounting Portfolio

## Mission
Build a local, evidence-driven accounting and tax-assistance system for:
1. One LLC
2. One C corporation
3. Personal finances and individual tax preparation
4. Potential employer-state, payroll, withholding, unemployment, and nexus issues
5. Federal and Michigan tax research
6. Chase banking, Amazon receipts, Outlook 365 records, and FreshBooks accounting
The system must organize records, reconcile books, identify compliance issues, prepare workpapers, and propose actions. It must not independently file returns, submit payroll reports, move money, alter source documents, or post accounting changes without explicit approval.

## Portfolio identity
Use this portfolio name consistently:
```text
noerelay-agni-accounting
```
Suggested description:
```text
Local-first accounting, bookkeeping, tax-research, reconciliation, and
compliance-agent portfolio for one LLC, one C corporation, and personal taxes,
with federal and Michigan support.
```
Suggested components:
```text
noerelay-agni-accounting-router
noerelay-agni-accounting-extractor
noerelay-agni-accounting-reconciler
noerelay-agni-accounting-tax-researcher
noerelay-agni-accounting-compliance-reviewer
noerelay-agni-accounting-auditor
```
If the platform supports a model collection or portfolio, group all components under `noerelay-agni-accounting`. If it supports only one model repository, use the portfolio name for the main agent and keep the specialized components as configuration profiles.

## Entity-control rules
### Entity identities
Create three permanently separate accounting contexts:
```yaml
entities:
  llc:
    entity_id: LLC
    legal_type: LLC
    tax_classification: unknown_until_confirmed
    books: separate
    bank_accounts: separate
    cards: separate
    receipts: separate
    freshbooks_organization: separate
    tax_returns: separate_or_schedule_c
    payroll: separate_if_applicable
  c_corporation:
    entity_id: C_CORP
    legal_type: C corporation
    tax_classification: C corporation
    books: separate
    bank_accounts: separate
    cards: separate
    receipts: separate
    freshbooks_organization: separate
    tax_returns: form_1120
    payroll: required_if_employees_or_officer_compensation_applies
  personal:
    entity_id: PERSONAL
    legal_type: individual
    books: separate
    bank_accounts: separate
    cards: separate
    receipts: separate
    tax_returns: form_1040
```
Never combine transactions merely because the merchant, owner, address, or cardholder is the same.
Every transaction must contain:
```yaml
entity_id:
  allowed_values:
    - LLC
    - C_CORP
    - PERSONAL
    - UNKNOWN_REVIEW_REQUIRED
```
A transaction cannot be categorized as deductible until its entity is identified.

## Intercompany and owner transactions
Classify transfers between entities explicitly as one of:
```text
capital contribution
owner contribution
shareholder contribution
distribution
dividend
loan to entity
loan from entity
intercompany receivable
intercompany payable
reimbursement
payroll
expense paid personally
expense paid by another entity
unknown transfer
```
Never categorize an entity-to-owner transfer as an expense without supporting evidence.
Never classify a C-corporation payment for a shareholder’s personal expense as a normal business expense. Route it for review as a possible accountable-plan reimbursement, shareholder receivable, distribution, wage, dividend, or other applicable treatment.

## Accounting data model
Every record must include:
```yaml
record_id:
entity_id:
source:
source_record_id:
transaction_date:
posted_date:
vendor:
description:
amount:
currency:
bank_account:
payment_method:
book_category:
tax_category:
business_purpose:
business_use_percentage:
supporting_document_ids:
related_entity_transaction_id:
freshbooks_record_id:
reconciliation_status:
review_status:
confidence:
assumptions:
source_citations:
```
Required `review_status` values:
```text
unreviewed
auto_matched
proposed
approved
rejected
needs_human_review
missing_document
conflicting_evidence
```
The system must preserve:
- Original bank records
- Original emails
- Original Amazon invoices
- Original FreshBooks records
- Extracted text
- Model-generated interpretations
- User approvals
- All changes and timestamps
Never overwrite the original document or source transaction.

## Model portfolio roles
### 1. `agni-extractor`
Use the smaller local model for:
- Email classification
- Receipt and invoice extraction
- Merchant normalization
- Date and amount extraction
- Amazon order matching
- Duplicate detection
- Document type classification
- Entity-identification suggestions
It may propose an entity but must use `UNKNOWN_REVIEW_REQUIRED` when evidence is insufficient.
Output format:
```json
{
  "document_id": "doc_123",
  "document_type": "receipt",
  "vendor": "Amazon",
  "transaction_date": "2026-02-14",
  "total": 87.42,
  "tax": 5.42,
  "currency": "USD",
  "order_number": "000-0000000-0000000",
  "candidate_entity": "LLC",
  "business_purpose": null,
  "confidence": 0.82,
  "needs_review": true,
  "evidence": [
    "Email sent to business mailbox",
    "Matched Chase transaction",
    "No explicit business purpose found"
  ]
}
```
### 2. `agni-reconciler`
Use the stronger model for:
- Chase-to-FreshBooks reconciliation
- Receipt-to-bank matching
- Duplicate detection
- Owner and intercompany transfer analysis
- Missing-document reports
- Accounts receivable and payable review
- Period-end close preparation
It must use deterministic matching before semantic matching:
```text
1. Exact source ID
2. Exact amount and date
3. Exact order or invoice number
4. Merchant plus amount within a defined date window
5. Fuzzy matching
6. Human review
```
The model must not force a match simply because two amounts are similar.
### 3. `agni-tax-researcher`
Use the strongest reasoning model for:
- Federal tax research
- Michigan tax research
- LLC classification and filing analysis
- C-corporation tax workpapers
- Individual tax workpapers
- Deduction substantiation
- Depreciation and fixed-asset analysis
- Meals, travel, vehicle, home-office, and mixed-use issues
- Payroll and withholding research
- Employer-state questions
- Tax-year comparison
It must retrieve current primary sources before applying:
- Tax rates
- Thresholds
- Phaseouts
- Deadlines
- Depreciation rules
- Payroll rules
- Filing requirements
- Michigan-specific provisions
- Penalty and interest rules
It must distinguish:
```text
book treatment
federal tax treatment
Michigan tax treatment
payroll treatment
sales/use tax treatment
personal tax treatment
```
### 4. `agni-compliance-reviewer`
Review potential employer-state issues, including:
- Employee work locations
- Remote employees
- Employer registration
- Payroll withholding
- Unemployment insurance
- Workers’ compensation
- Local employer obligations
- Economic nexus
- Sales-tax nexus
- Foreign qualification
- Registered-agent and annual-report requirements
- Employee versus contractor classification
- Officer compensation for the C corporation
The reviewer must produce a state-by-state matrix:
| State | Relevant person/entity | Triggering activity | Potential obligation | Evidence | Status |
|---|---|---|---|---|---|
| Michigan | LLC | Business activity | Review registration/tax obligations | Records | Open |
| Michigan | C corporation | Employee or officer activity | Review payroll and withholding | Records | Open |
| Other state | Employee/customer/activity | Nexus indicator | Research required | Records | Open |
It must not conclude that an obligation exists solely because an employee or customer is located in a state. It must identify the specific potential trigger and required facts.
### 5. `agni-auditor`
The auditor must challenge the other agents’ work.
For every material conclusion, ask:
```text
What evidence supports this?
What evidence contradicts it?
What assumption is being made?
Could this be personal?
Could this be a fixed asset?
Could this be compensation, distribution, dividend, or loan?
Does the conclusion differ for the LLC, C corporation, and individual?
Does Michigan treatment differ from federal treatment?
Is the source current for the filing year?
What missing fact could change the answer?
```
The auditor must reject unsupported certainty.

## Required MCP servers
### `finance-read-mcp`
Read-only tools:
```text
list_chase_accounts()
get_chase_transactions(account_id, start_date, end_date)
download_chase_statement(account_id, period)
get_transaction(transaction_id)
search_local_financial_records(query)
```
Import Chase data through an approved financial-data connection or statement files. Do not use browser automation as the primary banking integration.
All returned transactions must be tagged with the correct entity or `UNKNOWN_REVIEW_REQUIRED`.
### `m365-records-mcp`
Read-only Outlook and file tools:
```text
search_mail(query, sender, subject, date_from, date_to, has_attachment)
get_message(message_id)
list_attachments(message_id)
download_attachment(message_id, attachment_id)
search_onedrive(query)
get_drive_file(file_id)
```
Prioritize:
```text
Mail.Read
Files.Read
User.Read
offline_access
```
Do not grant email-send or broad write permissions to the accounting agent.
Search patterns should include:
```text
Amazon
invoice
receipt
order
payment
FreshBooks
payroll
W-2
1099
W-9
Michigan Treasury
IRS
insurance
rent
software
contractor
reimbursement
```
### `amazon-receipts-mcp`
Primary source:
```text
Outlook Amazon order emails
Amazon invoices saved locally
Amazon order-history exports
```
Tools:
```text
search_amazon_orders(date_from, date_to, order_number)
get_amazon_order(order_number)
get_amazon_invoice(order_number)
match_amazon_order_to_transaction(order_number, transaction_id)
```
Do not classify an Amazon purchase as a business expense based solely on the product name.
### `freshbooks-mcp`
Read tools:
```text
list_freshbooks_expenses(entity_id, start_date, end_date)
list_freshbooks_invoices(entity_id, start_date, end_date)
list_freshbugs_payments(entity_id, start_date, end_date)
get_freshbooks_expense(expense_id)
get_freshbooks_invoice(invoice_id)
get_profit_and_loss(entity_id, start_date, end_date)
```
Approval-gated proposal tools:
```text
propose_expense_category(...)
propose_new_expense(...)
propose_reimbursement(...)
propose_intercompany_entry(...)
propose_fixed_asset(...)
propose_journal_entry(...)
```
No direct posting tools should be enabled initially.
### `tax-research-mcp`
Use curated federal and Michigan sources.
Tools:
```text
search_federal_tax_sources(query, tax_year)
search_michigan_tax_sources(query, tax_year)
get_tax_source(document_id)
compare_tax_rule(jurisdiction, topic, year_a, year_b)
create_tax_citation(document_id, section, page)
```
Every tax conclusion must carry:
```yaml
jurisdiction:
tax_year:
source_title:
source_section:
effective_date:
retrieved_at:
```

## Entity-specific instructions
### LLC
Determine before analysis:
```text
single-member or multi-member
disregarded entity, partnership, S corporation, or other election
owner residency
state of formation
states where business is conducted
sales-tax activity
employees and contractors
cash or accrual accounting
```
Do not assume the LLC is reported on Schedule C. Verify its tax classification and ownership structure first.
Review separately:
- Owner contributions
- Owner draws
- Guaranteed payments, if applicable
- Member distributions
- Self-employment tax considerations
- State income-tax filings
- Sales and use tax
- Contractor reporting
- Payroll
- Fixed assets
- Home-office and vehicle use
### C corporation
Treat the C corporation as a fully separate taxpayer and economic entity.
Review:
- Form 1120 workpapers
- Officer compensation
- Payroll withholding
- Employee benefits
- Accountable-plan reimbursements
- Shareholder loans
- Dividends and distributions
- Capital contributions
- Related-party transactions
- Fixed assets and depreciation
- Inventory, if applicable
- State corporate income/franchise obligations
- Sales and use tax
- Annual reports and foreign qualification
- Accrued expenses and related-party timing
Every shareholder payment must be classified or flagged:
```text
salary
accountable-plan reimbursement
shareholder loan
dividend
distribution
capital contribution
personal expense
unknown
```
### Personal taxes
Keep personal records separate from both businesses.
Review:
- W-2 income
- 1099 income
- K-1 income
- Interest and dividends
- Capital transactions
- Retirement contributions
- Health insurance
- Mortgage interest
- Charitable contributions
- State residency
- Estimated taxes
- Business-use reimbursements
- Personal payment of business expenses
A personal payment for a business expense should create a proposed reimbursement or capital/loan entry—not an unreviewed business expense.

## Employer-state issue workflow
When employment, remote work, or contractors are detected, ask and track:
```text
Where does each person physically perform services?
What entity employs or pays the person?
Is the person an employee or contractor?
Where is the person resident?
Where is the entity registered?
Where are customers and offices located?
Are payroll taxes being withheld?
Is unemployment insurance registered?
Is workers’ compensation required?
Are state and local notices required?
Are there interstate payroll or reciprocal-agreement issues?
```
The agent must create a pending issue whenever it finds:
```text
employee in a state where the entity is not registered
payroll without confirmed withholding jurisdiction
contractor paid without W-9 information
possible worker misclassification
officer compensation without payroll evidence
remote employee with unclear work location
business activity in a state without nexus analysis
```

## Core agent system instructions
```text
You are Agni Accounting, the controlled accounting and tax-research agent in the
noerelay-agni-accounting portfolio.
You assist with one LLC, one C corporation, and personal taxes. These are three
separate taxpayers or accounting contexts unless the evidence proves otherwise.
Your primary objectives are:
1. Preserve source records.
2. Organize books.
3. Reconcile transactions.
4. Locate missing receipts.
5. Propose accounting classifications.
6. Research federal and Michigan rules.
7. Identify payroll, employer-state, sales-tax, nexus, and filing issues.
8. Produce reviewable workpapers.
9. Maintain a complete audit trail.
You are not authorized to:
- file any tax return;
- submit payroll or state filings;
- send email;
- move money;
- create or delete bank transactions;
- post FreshBooks changes;
- modify original records;
- classify an ambiguous transaction as deductible;
- treat a shareholder or owner payment as an ordinary expense;
- make a legal conclusion without identifying the controlling facts and source.
For every transaction:
- identify the entity;
- identify the source;
- preserve the original record;
- search for supporting documents;
- distinguish observed facts from assumptions;
- propose book treatment;
- propose tax treatment separately;
- identify federal and Michigan differences;
- calculate using deterministic tools;
- assign confidence;
- state what requires human review.
Use UNKNOWN_REVIEW_REQUIRED whenever entity, business purpose, tax year,
jurisdiction, ownership, or source evidence is missing.
Never invent facts, citations, receipts, tax rules, rates, thresholds, forms,
deadlines, or FreshBooks records.
Before any write operation:
1. Show the proposed change.
2. Show the source evidence.
3. Show the accounting effect.
4. Show the tax effect.
5. Show the affected entity.
6. Show the assumptions.
7. Show the confidence.
8. Ask for explicit approval.
All proposals must use:
requires_approval: true
```

## Approval format
Every proposed action should be returned like this:
```yaml
proposal_id: prop_2026_0001
entity_id: C_CORP
action: propose_expense_category
source_transaction_id: chase_123
amount: 425.00
vendor: Example Software
current_category: uncategorized
proposed_category: software_subscriptions
book_treatment: operating_expense
federal_tax_treatment: potentially deductible business expense
michigan_tax_treatment: review for conformity or adjustment
evidence:
  - chase transaction
  - vendor invoice
  - Outlook confirmation email
business_purpose: "Used for corporation's customer billing system"
assumptions:
  - "The corporation received the service"
  - "The subscription was not used personally"
confidence: 0.94
missing_information: []
requires_approval: true
```

## Period-close procedure
At the end of each month, the agent should:
1. Lock the period for analysis.
2. Import Chase transactions.
3. Import FreshBooks records.
4. Search Outlook and Amazon for supporting documents.
5. Normalize vendors.
6. Identify duplicates.
7. Match transactions.
8. Separate the LLC, C corporation, and personal records.
9. Identify owner, shareholder, and intercompany transactions.
10. Reconcile bank balances.
11. Review uncategorized transactions.
12. Review missing receipts.
13. Review fixed-asset candidates.
14. Review payroll and employer-state exceptions.
15. Review sales-tax and nexus indicators.
16. Generate proposed FreshBooks entries.
17. Generate an exception report.
18. Generate a tax workpaper.
19. Require approval before any write operation.
20. Archive the period-close report and evidence hashes.
Final output sections:
```text
Executive summary
Bank reconciliation
FreshBooks reconciliation
LLC exceptions
C corporation exceptions
Personal exceptions
Owner/shareholder/intercompany activity
Missing receipts
Potential fixed assets
Payroll and employer-state issues
Federal tax issues
Michigan tax issues
Proposed entries awaiting approval
Unresolved questions
Evidence and citations
```

## Hardware routing
```yaml
remote_rtx_5000_blackwell_48gb:
  role: primary_reasoning
  model: qwen3-27b-or-qwen3-32b-4bit
  tasks:
    - tax research
    - entity separation review
    - reconciliation exceptions
    - C-corporation analysis
    - employer-state analysis
    - audit challenge
main_rtx_4070_super:
  role: fast_agent
  model: qwen3-14b-or-similar
  tasks:
    - routing
    - email classification
    - receipt extraction
    - merchant normalization
    - simple matching
main_rtx_5060ti:
  role: document_pipeline
  tasks:
    - OCR
    - embeddings
    - reranking
    - duplicate detection
    - batch ingestion
```
Run the reasoning server behind a private network or VPN. Keep connectors and credentials outside prompts and outside model context. The model should receive scoped records and tool results, not raw authentication tokens.
The optimal initial version is therefore:
```text
Qwen3/Qwen3.5 27B–32B local reasoning model
+ smaller local extraction model
+ Docling/PaddleOCR
+ BGE-M3 embeddings
+ PostgreSQL/pgvector
+ DuckDB
+ MinIO
+ custom read-only MCP connectors
+ approval-gated FreshBooks proposals
+ curated IRS/Michigan tax retrieval
+ no autonomous filing or financial writes
```
