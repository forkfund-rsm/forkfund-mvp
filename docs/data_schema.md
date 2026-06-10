# ForkFund Synthetic Data Schema

**Purpose:** This document specifies the structure of five CSV files that power the ForkFund MVP. The schema is designed to support the nine-dimension scoring model, lender dashboard filters, and restaurant-specific operating metrics defined in `docs/mvp_design.md`.

**Key design principles:**
- CSV files store **raw inputs only**. All derived fields (ratios, percentiles, scores) are computed at load time by the data loader.
- Data is **consistent and reconcilable** across monthly and annual views.
- **No stored flags or pre-computed scores** in the CSVs; all scoring logic runs at runtime.
- **Single source of truth** for each value: raw data in CSV, derived results in memory.

---

## Overview

The MVP uses approximately **80 synthetic restaurants** distributed across:
- **Revenue bands:** Four bands with ≥15 restaurants each (see below)
- **Dutch cities:** Amsterdam, Rotterdam, Utrecht, The Hague, Eindhoven, Groningen, Breda, Maastricht, Arnhem, and others
- **Three target demo profiles:** designed to score approximately A, C, and D grades (actual grades determined by the scoring engine)
- **Fixed random seed:** for reproducibility across runs (e.g., seed=42)

Five CSV files form the data model:
1. `data/restaurants.csv` — restaurant identity, loan request, and operational baseline
2. `data/monthly_bank.csv` — 12 months of bank transaction summaries per restaurant
3. `data/monthly_pos.csv` — 12 months of POS sales and operational metrics per restaurant
4. `data/accounting.csv` — annual financial summary per restaurant
5. `data/lenders.csv` — lender profiles (dashboard support file)

---

## Revenue Bands

To ensure meaningful peer-percentile context within each band, every band contains ≥15 restaurants:

| Revenue band | Annual revenue range | Restaurant count | Notes |
|--------------|---------------------|-------------------|-------|
| Band 1 | €0–500k | 20 | Small neighbourhood restaurants |
| Band 2 | €500k–1M | 25 | Mid-size suburban and city restaurants |
| Band 3 | €1M–1.5M | 20 | Larger established restaurants |
| Band 4 | €1.5M+ | 15 | Premium and high-volume restaurants |
| **Total** | | **80** | Distributed across Dutch cities |

Each restaurant's band is derived from expected annual revenue (in restaurants.csv) and used for peer-percentile calculations within the Credit Passport.

---

## 1. `data/restaurants.csv`

### What one row represents
A single restaurant entity requesting a loan, with identity information, operational baseline, and financing request.

### Primary key
`restaurant_id` (integer, sequential 1–80)

### Rows per restaurant
1 row (static snapshot; not time-indexed)

### Columns

| Column | Data type | Example | Scoring dimension / Feature | Storage or Computed | Notes |
|--------|-----------|---------|----------------------------|---------------------|-------|
| restaurant_id | int | 1 | Identifier | **Raw (stored)** | PK; used to join all other files |
| kvk_number | string | 91234567 | Data completeness; identity verification | **Raw (stored)** | Simulated KvK lookup; unique per restaurant |
| legal_name | string | De Gouden Vork | Passport display | **Raw (stored)** | Restaurant name |
| registration_date | string (YYYY-MM-DD) | 2019-03-15 | Business maturity | **Raw (stored)** | Used to compute years_active at load time |
| city | string | Amsterdam | Lender filter; passport display | **Raw (stored)** | Valid Dutch city |
| legal_form | string | B.V. or Eenmanszaak | Passport context | **Raw (stored)** | Legal structure; informative |
| sbi_code | string | 5610 | Business classification | **Raw (stored)** | Confirms restaurant/food sector |
| cuisine_type | string | Italian, French, Asian, Dutch, Mediterranean | Peer grouping context | **Raw (stored)** | Informational |
| seats | int | 50 | POS demand quality; rent pressure | **Raw (stored)** | Used to compute RevPASH and table-turnover proxy at load time |
| opening_hours_per_day | float | 10.5 | POS demand quality context | **Raw (stored)** | Average operating hours per day (typically 10–14 hours) |
| requested_loan_amount | float (EUR) | 100000 | Lender filter; debt burden context | **Raw (stored)** | Proposed new borrowing; supports lender min/max filter |
| loan_purpose | string | "Term loan", "Working capital", "Equipment", "Renovation" | Lender filter | **Raw (stored)** | Fixed vocabulary; one of exactly four values |
| annual_revenue_estimate | float (EUR) | 750000 | Revenue band classification | **Raw (stored)** | Used to assign revenue_band at load time |
| demo_profile | string or null | "strong", "medium", "high_risk", or null | Demo highlighting | **Raw (stored)** | Marks three target demo restaurants; null for others |

### Derived fields (computed at load time)

| Field | Computation | Purpose |
|-------|-----------|---------|
| years_active | (today − registration_date) / 365 | Business maturity score; capped at 10 years |
| opening_hours_per_month | opening_hours_per_day × ~25 (operating days per month) | RevPASH calculation |
| revenue_band | Assigned based on annual_revenue_estimate | Peer-percentile grouping (€0–500k, €500k–1M, €1M–1.5M, €1.5M+) |

### What is NOT included

- Owner/founder names or identity verification (iDIN, BKR checks — lender responsibility)
- Contact details (email, phone) — not in MVP scope
- Real KvK data — all data is synthetic
- Multiple locations or branches — each row is one legal entity
- Historical loan performance — first-time requests only

---

## 2. `data/monthly_bank.csv`

### What one row represents
One month of aggregated bank transaction data for one restaurant: inflows, outflows, ending balance, and debt-service payments.

### Primary key
Composite: (`restaurant_id`, `period`)

### Foreign keys
`restaurant_id` references `restaurants.csv`

### Rows per restaurant
12 rows (one per calendar month, January–December of a simulated year)

### Time grain
Monthly (calendar month aggregation)

### Period representation
`period` column uses format `YYYY-MM` (e.g., `2025-01`, `2025-02`, ..., `2025-12`)

### Columns

| Column | Data type | Example | Scoring dimension / Feature | Storage or Computed | Notes |
|--------|-----------|---------|----------------------------|---------------------|-------|
| restaurant_id | int | 1 | Identifier | **Raw (stored)** | FK to restaurants.csv |
| period | string (YYYY-MM) | 2025-01 | Time identifier | **Raw (stored)** | Sorted chronologically; all restaurants use same year |
| month_number | int (1–12) | 1 | Sorting helper | **Raw (stored)** | Redundant with period but useful for ordering |
| total_inflows | float (EUR) | 85000 | Cash-flow strength; revenue stability cross-check | **Raw (stored)** | Monthly sum of all deposits/income |
| total_outflows | float (EUR) | 62000 | Cash-flow strength | **Raw (stored)** | Monthly sum of all expenses/withdrawals |
| ending_balance | float (EUR) | 45000 | Passport display; cash-buffer context | **Raw (stored)** | Account balance at month end; working capital indicator |
| debt_service_outflows | float (EUR) | 5000 | Debt burden and repayment capacity | **Raw (stored)** | Monthly principal + interest on existing debt; derived from annual existing_debt in accounting.csv |
| cash_deposits | float (EUR) | 20000 | Cash/card consistency | **Raw (stored)** | Monthly cash received |
| card_deposits | float (EUR) | 65000 | Cash/card consistency | **Raw (stored)** | Monthly card/transfer received |

### Derived fields (computed at load time)

| Field | Computation | Purpose |
|-------|-----------|---------|
| net_cash_inflow_margin | (total_inflows − total_outflows) / total_inflows | Cash-flow strength score; benchmark 30% |

### Reconciliation and coherence

- **total_inflows ≈ cash_deposits + card_deposits** (within ±2% tolerance for rounding and transfers)
- **debt_service_outflows** should match the monthly equivalent of accounting.debt_service_estimated (annual) divided by 12
- **total_outflows** typically 60–85% of total_inflows (depending on restaurant profile)
- **ending_balance** fluctuates month-to-month but stays within typical working-capital range (€10k–€100k for most restaurants)

### What is NOT included

- Individual transaction details (only monthly aggregates)
- Real bank account numbers or IBAN
- Third-party payments or transfers (bundled into inflows/outflows)
- Loan originations or capital injections (baseline data only)
- Inter-account transfers (net deposits/withdrawals only)

---

## 3. `data/monthly_pos.csv`

### What one row represents
One month of aggregated point-of-sale data for one restaurant: revenue, covers, payment method split, delivery sales, and weekend revenue.

### Primary key
Composite: (`restaurant_id`, `period`)

### Foreign keys
`restaurant_id` references `restaurants.csv`

### Rows per restaurant
12 rows (one per calendar month)

### Time grain
Monthly (calendar month aggregation)

### Period representation
`period` column uses format `YYYY-MM` (same as monthly_bank.csv, for easy joining)

### Columns

| Column | Data type | Example | Scoring dimension / Feature | Storage or Computed | Notes |
|--------|-----------|---------|----------------------------|---------------------|-------|
| restaurant_id | int | 1 | Identifier | **Raw (stored)** | FK to restaurants.csv |
| period | string (YYYY-MM) | 2025-01 | Time identifier | **Raw (stored)** | Matches monthly_bank.period |
| month_number | int (1–12) | 1 | Sorting helper | **Raw (stored)** | Redundant with period |
| total_revenue | float (EUR) | 85000 | Revenue stability; all demand metrics | **Raw (stored)** | Monthly food + beverage revenue from POS |
| covers | int | 850 | POS demand quality; table-turnover proxy | **Raw (stored)** | Number of customers served in the month |
| card_sales | float (EUR) | 70000 | Payment method consistency | **Raw (stored)** | Revenue paid by card |
| cash_sales | float (EUR) | 15000 | Payment method consistency | **Raw (stored)** | Revenue paid by cash |
| delivery_platform_sales | float (EUR) | 17000 | Seasonality and concentration risk | **Raw (stored)** | Revenue from Uber Eats, Deliveroo, etc. |
| dine_in_sales | float (EUR) | 68000 | POS demand quality context | **Raw (stored)** | Revenue from on-premise dining |
| weekend_revenue | float (EUR) | 28000 | Seasonality and concentration risk | **Raw (stored)** | Revenue Friday–Sunday (approximate) |
| weekday_revenue | float (EUR) | 57000 | Seasonality and concentration risk baseline | **Raw (stored)** | Revenue Monday–Thursday (approximate) |

### Derived fields (computed at load time)

| Field | Computation | Purpose |
|-------|-----------|---------|
| average_check | total_revenue / covers | POS demand quality indicator |
| delivery_platform_share | delivery_platform_sales / total_revenue | Concentration risk (high delivery dependency if >35%) |
| weekend_share | weekend_revenue / total_revenue | Seasonality risk (high weekend dependency if >60%) |
| revenue_cv (across 12 months) | coefficient of variation of total_revenue | Revenue stability score |
| table_turnover_proxy | covers / (restaurants.seats × ~25 operating days per month) | Table utilisation proxy |

### Reconciliation and coherence

- **card_sales + cash_sales ≈ total_revenue** (within ±1%)
- **dine_in_sales + delivery_platform_sales ≈ total_revenue** (approximately; some revenue may go to other channels)
- **weekend_revenue + weekday_revenue ≈ total_revenue** (approximately; weekends typically 35–55% of revenue)
- **monthly volatility** in total_revenue feeds revenue-stability score

### What is NOT included

- Individual transaction records (only monthly aggregates)
- Real POS system identifiers (Lightspeed, Toast, Square, etc.)
- Loyalty program or discount detail
- Staff costs or labour detail (in accounting.csv)
- Menu-item breakdown or pricing

---

## 4. `data/accounting.csv`

### What one row represents
Annual financial summary for one restaurant: revenue, costs (food, labour, rent), EBITDA, debt, and debt service.

### Primary key
Composite: (`restaurant_id`, `year`)

### Foreign keys
`restaurant_id` references `restaurants.csv`

### Rows per restaurant
1 row per restaurant (most recent fiscal year; 2025 for MVP)

### Time grain
Annual (fiscal year aggregation)

### Period representation
`year` column uses format `YYYY` (e.g., `2025`)

### Columns

| Column | Data type | Example | Scoring dimension / Feature | Storage or Computed | Notes |
|--------|-----------|---------|----------------------------|---------------------|-------|
| restaurant_id | int | 1 | Identifier | **Raw (stored)** | FK to restaurants.csv |
| year | int | 2025 | Time identifier | **Raw (stored)** | Fiscal year; single year for MVP |
| annual_revenue | float (EUR) | 950000 | All scoring dimensions baseline | **Raw (stored)** | Total annual revenue; should align with sum of 12 months of monthly_pos.total_revenue |
| food_cost | float (EUR) | 285000 | Prime cost efficiency | **Raw (stored)** | Annual COGS (food and beverages) |
| labour_cost | float (EUR) | 380000 | Prime cost efficiency | **Raw (stored)** | Annual wages, payroll taxes, benefits |
| rent_annual | float (EUR) | 90000 | Rent / occupancy pressure | **Raw (stored)** | Annual rent/lease payments |
| ebitda | float (EUR) | 95000 | Debt burden and repayment capacity | **Raw (stored)** | Earnings before interest, tax, depreciation, amortisation |
| net_profit | float (EUR) | 70000 | Profitability context | **Raw (stored)** | Net income after all costs and taxes |
| existing_debt | float (EUR) | 150000 | Debt burden and repayment capacity | **Raw (stored)** | Total outstanding debt (mortgages, equipment loans, lines of credit) |
| debt_service_estimated | float (EUR) | 25000 | Debt burden and repayment capacity | **Raw (stored)** | Annual estimated principal + interest on existing_debt |

### Derived fields (computed at load time)

| Field | Computation | Purpose |
|-------|-----------|---------|
| prime_cost_ratio | (food_cost + labour_cost) / annual_revenue | Prime cost efficiency score; scored in bands: ≤0.60, 0.60–0.65, 0.65–0.70, 0.70–0.80, >0.80 |
| rent_to_revenue | rent_annual / annual_revenue | Rent pressure score; scored in bands: ≤0.08, 0.08–0.10, 0.10–0.12, 0.12–0.15, >0.15 |
| debt_to_revenue | existing_debt / annual_revenue | Debt burden ratio component |
| ebitda_margin | ebitda / annual_revenue | Operating profitability; context for debt-service coverage |
| dscr_proxy | ebitda / debt_service_estimated | Debt-service coverage ratio proxy (or 100 if existing_debt = 0) |
| monthly_debt_service | debt_service_estimated / 12 | Used to populate monthly_bank.debt_service_outflows |

### DSCR proxy special case

When **existing_debt = 0** (no existing debt):
- **dscr_proxy = 100** (maximal repayment capacity; no competing obligations)
- This avoids divide-by-zero and signals zero debt burden

When **existing_debt > 0**:
- **dscr_proxy = ebitda / debt_service_estimated**
- Benchmark is 1.50; values >1.50 are capped at score 100 in the sub-score formula

### Reconciliation and coherence

- **annual_revenue** should approximately match sum of 12 months of monthly_pos.total_revenue (within ±3%)
- **debt_service_estimated** reconciles with monthly_bank.debt_service_outflows: debt_service_estimated / 12 ≈ monthly outflow
- **ebitda** is provided as raw input (not computed from revenue − costs, for flexibility in synthetic generation)
- **monthly_bank.debt_service_outflows × 12 ≈ debt_service_estimated** (within ±5%)

### What is NOT included

- Line-item detail on costs (only top-level: food, labour, rent)
- Utilities, insurance, marketing, maintenance (bundled into EBITDA calculation)
- Tax provisions or detailed tax reconciliation
- Depreciation detail (included in EBITDA definition per concept)
- Loan origination dates or amortisation terms (only outstanding balance and estimated annual service)
- Owner compensation or draws (not separated in MVP)
- Real accounting software exports (synthesised from first principles)

---

## 5. `data/lenders.csv` (Dashboard Support File)

### What one row represents
A single lender profile that filters and selects restaurants from the dashboard.

### Primary key
`lender_id` (integer)

### Rows
One row per lender; typical MVP has 5–10 demo lenders (optional for MVP; can be empty or minimal)

### Purpose
Lender filtering on the dashboard. Lenders are **not** part of the scoring model; they are reference data for lender-user profiles and dashboard filters.

### Columns

| Column | Data type | Example | Dashboard feature | Notes |
|--------|-----------|---------|-------------------|-------|
| lender_id | int | 1 | Identifier | PK |
| lender_name | string | ABN AMRO | Lender profile | Name of lending institution |
| focus_city | string or null | Amsterdam | Optional location filter | City of focus; null if nationwide |
| min_loan_amount | float (EUR) | 50000 | Lender filter | Minimum loan the lender will consider |
| max_loan_amount | float (EUR) | 500000 | Lender filter | Maximum loan the lender will consider |
| preferred_loan_purposes | string (comma-separated) | "Term loan, Working capital" | Lender filter | Loan purposes this lender focuses on (from fixed vocabulary) |

### What is NOT included

- Lender contact details or websites
- Interest rates, terms, or real offers
- Lender approval criteria (lenders filter manually; ForkFund does not automate lending decisions)
- Historical funding history or performance metrics
- Real lender data (all synthetic)

---

## Demo Profiles

Three restaurants are marked as target demo profiles designed to score approximately A, C, and D grades **when the scoring engine runs** (grades are computed, not assigned). These are demonstration profiles; actual grades depend on scoring formula outputs.

### Profile 1: Target A-grade ("Strong restaurant")
- **Characteristics:**
  - Prime cost ≤0.60 (efficient operations)
  - Rent-to-revenue ≤0.08 (low occupancy pressure)
  - Revenue stability: high (low coefficient of variation)
  - Cash flow: strong (>30% net cash inflow margin)
  - Business maturity: ≥3 years
  - Debt burden: low (existing_debt < 25% of annual_revenue)
  - Seasonality risk: low (weekend share 40–50%, delivery share <20%)
- **Example:** restaurant_id = 1, "Bonne Table" in Amsterdam
- **Expected score:** 85–100 (Grade A)

### Profile 2: Target C-grade ("Medium-risk restaurant")
- **Characteristics:**
  - Prime cost 0.65–0.70 (borderline efficiency)
  - Rent-to-revenue 0.10–0.12 (caution zone)
  - Revenue stability: moderate (moderate coefficient of variation)
  - Cash flow: adequate (20–30% net cash inflow margin)
  - Business maturity: 1–2 years (young but operating)
  - Debt burden: moderate (existing_debt 30–50% of annual_revenue)
  - Seasonality risk: moderate (weekend share 50–55%, delivery share 25–35%)
- **Example:** restaurant_id = 41, "Trattoria Pietro" in Rotterdam
- **Expected score:** 55–69 (Grade C)

### Profile 3: Target D-grade ("High-risk restaurant")
- **Characteristics:**
  - Prime cost 0.70–0.78 (warning zone)
  - Rent-to-revenue 0.12–0.15 (high pressure)
  - Revenue stability: low (high coefficient of variation; unstable)
  - Cash flow: weak (<15% net cash inflow margin; possible negative months)
  - Business maturity: <1 year (very new; below common lender thresholds)
  - Debt burden: high (existing_debt 50–80% of annual_revenue)
  - Seasonality risk: high (weekend share ≥60%, delivery share ≥40%)
- **Example:** restaurant_id = 75, "Levant Express" in Utrecht
- **Expected score:** 40–54 (Grade D)

---

## Synthetic Data Generation Strategy

### Random seed and reproducibility
- Use a fixed random seed (e.g., `seed=42`) for all synthetic data generation
- Document the seed in README and in code comments for reproducibility

### Restaurant distribution across 80 total

**By revenue band:**
- €0–500k: 20 restaurants
- €500k–1M: 25 restaurants
- €1M–1.5M: 20 restaurants
- €1.5M+: 15 restaurants

**By city:** Distribute across 8–10 Dutch cities (Amsterdam, Rotterdam, Utrecht, The Hague, Eindhoven, Groningen, Breda, Maastricht, Arnhem, Dordrecht) with realistic distribution (larger cities have more restaurants).

**By cuisine type:** Vary across Italian, French, Asian, Mediterranean, Dutch, Turkish, Spanish, fusion, vegetarian, fine-dining, casual, quick-service.

### Key synthetic data constraints

**Consistency across files:**
- **annual_revenue** (accounting.csv) ≈ sum of 12 months of monthly_pos.total_revenue (within ±3%)
- **debt_service_estimated** (accounting.csv) ≈ sum of 12 months of monthly_bank.debt_service_outflows (within ±5%)
- **monthly_bank.total_inflows** ≈ monthly_bank.cash_deposits + monthly_bank.card_deposits (within ±2%)
- **monthly_pos.total_revenue** ≈ monthly_pos.card_sales + monthly_pos.cash_sales (within ±1%)
- **monthly_pos.total_revenue** ≈ monthly_pos.dine_in_sales + monthly_pos.delivery_platform_sales (within ±1%, approximately)
- **monthly_pos.total_revenue** ≈ monthly_pos.weekend_revenue + monthly_pos.weekday_revenue (exactly or near-exactly)

**Realistic ranges for restaurant operations:**
- **Average check:** €40–€150 (higher for fine dining, lower for casual/quick-service)
- **Seats:** 20–200 (depending on restaurant size and concept)
- **Prime cost ratio:** 0.55–0.80 (healthy ≤0.65; warning >0.70)
- **Rent-to-revenue:** 0.07–0.16 (healthy ≤0.08; warning >0.15)
- **EBITDA margin:** 2–18% (varies with concept and efficiency)
- **Cash/card ratio:** 20/80 to 40/60 (modern restaurants skew card; traditional may skew cash)
- **Delivery share:** 0–40% (high delivery >35% is concentration risk flag)
- **Weekend share:** 35–65% (high weekend >60% is seasonality risk flag)
- **Outflows as % of inflows:** 60–85% (depending on profile; efficient restaurants closer to 60%; struggling restaurants closer to 85%)

### Data format standards

- **Dates:** ISO format YYYY-MM-DD (restaurants.csv: registration_date) and YYYY-MM (time-indexed files: period)
- **Currency:** EUR; use decimal separator `.` (e.g., 1000.50, not 1000,50)
- **Integers:** No thousand separators
- **CSV dialect:** Standard (comma-separated, no special quoting unless field contains commas or newlines)
- **Headers:** Snake_case, lowercase, with underscores (not spaces or camelCase)

---

## Data Completeness (Runtime Concept)

Data completeness is **not stored as a raw column**. Instead, it is computed at load time as a **runtime indicator**:

$$\text{Data completeness} = \frac{\text{number of connected data sources}}{3} \times 100\%$$

The three sources are:
1. **Bank data:** A restaurant has data_completeness for bank if it has rows in `monthly_bank.csv` (or user connected bank in onboarding)
2. **POS data:** A restaurant has data_completeness for POS if it has rows in `monthly_pos.csv` (or user connected POS in onboarding)
3. **Accounting data:** A restaurant has data_completeness for accounting if it has rows in `accounting.csv` (or user connected accounting in onboarding)

**In the MVP:**
- All 80 restaurants have all three data sources in the CSV files (100% data completeness for pre-loaded profiles)
- During restaurant onboarding, the user may skip connecting certain sources; the app gracefully computes data-completeness based on what is connected
- The scoring engine assigns a neutral score of 50 to missing dimensions (e.g., if accounting data is missing, prime cost and rent-pressure dimensions receive neutral 50)

**Data-completeness score:**
- 100% if all 3 sources are present
- 67% if 2 sources are present
- 33% if 1 source is present
- 0% if no sources are present (Passport should still generate but with very low confidence)

---

## Scoring Dimension Coverage Table

This table confirms that every scoring dimension is supported by the appropriate columns:

| Dimension (weight) | Sub-dimension / Formula | Supporting Column(s) | File | Runtime Computation |
|-------------------|------------------------|----------------------|------|---------------------|
| **1. Data completeness and verification (0.10)** | Sources connected / 3 | Presence of rows in monthly_bank, monthly_pos, accounting | All | Count of non-null data sources per restaurant |
| **2. Revenue stability (0.125)** | Coefficient of variation of monthly revenue | monthly_pos.total_revenue (12 months) | monthly_pos | CV across 12 months; score = max(0, min(100, 100 × (1 − CV))) |
| **3. Cash-flow strength (0.15)** | Net cash inflow margin | monthly_bank.total_inflows, monthly_bank.total_outflows | monthly_bank | Average monthly (inflows − outflows) / inflows; benchmark 30%; score = max(0, min(100, 100 × margin / 0.30)) |
| **4. Debt burden and repayment capacity (0.15)** | Debt-to-revenue (50%) + DSCR proxy (50%) | accounting.existing_debt, accounting.annual_revenue, accounting.ebitda, accounting.debt_service_estimated | accounting | (1) debt_to_revenue = min(debt / revenue, 1); score = 100 × (1 − debt_to_revenue); (2) dscr_proxy = 100 if debt=0, else ebitda / debt_service; score = max(0, min(100, 100 × dscr / 1.50)); average = 50% × each |
| **5. Prime cost efficiency (0.15)** | Prime-cost ratio | accounting.food_cost, accounting.labour_cost, accounting.annual_revenue | accounting | prime_cost = (food_cost + labour_cost) / revenue; scored in bands: ≤0.60→100, 0.60–0.65→75, 0.65–0.70→50, 0.70–0.80→25, >0.80→0 |
| **6. Rent / occupancy pressure (0.10)** | Rent-to-revenue ratio | accounting.rent_annual, accounting.annual_revenue | accounting | rent_ratio = rent / revenue; scored in bands: ≤0.08→100, 0.08–0.10→80, 0.10–0.12→60, 0.12–0.15→30, >0.15→0 |
| **7. POS demand quality (0.10)** | Covers, average check, table-turnover proxy, RevPASH | monthly_pos.covers, monthly_pos.total_revenue, restaurants.seats, restaurants.opening_hours_per_day | monthly_pos, restaurants | 25% × each: (1) covers_score = percentile within population, (2) avg_check_score = percentile, (3) table_turnover = (covers / seats / ~25 days) percentile, (4) RevPASH = (revenue / seats / hours_per_month) percentile |
| **8. Seasonality and concentration risk (0.075)** | Revenue volatility (40%) + delivery dependency (30%) + weekend dependency (30%) | monthly_pos.total_revenue (CV), monthly_pos.delivery_platform_sales, monthly_pos.weekend_revenue | monthly_pos | (1) seasonality_score = based on high CV; (2) delivery_share = delivery / total_revenue; flag if >35%; (3) weekend_share = weekend / total_revenue; flag if >60%; score reduced for high concentrations |
| **9. Business maturity (0.05)** | Years active | restaurants.registration_date | restaurants | years = (today − registration_date) / 365; score = min(100, 100 × years / 10); capped at 10 years |

---

## Dashboard Filter Coverage Table

This table confirms that every lender dashboard filter is supported:

| Dashboard Filter | Supporting Column(s) | File | Runtime Computation |
|------------------|----------------------|------|---------------------|
| **City** | restaurants.city | restaurants | Dropdown filter; list of unique cities |
| **Grade** | Composite score (0–100) computed by scoring engine | (computed at runtime) | Derived from nine sub-scores; bands: A (85–100), B (70–84), C (55–69), D (40–54), E (0–39) |
| **Loan amount** | restaurants.requested_loan_amount | restaurants | Slider or range filter; min/max from data |
| **Loan purpose** | restaurants.loan_purpose | restaurants | Dropdown filter; fixed vocabulary: "Term loan", "Working capital", "Equipment", "Renovation" |
| **Data completeness** | Presence of data in monthly_bank, monthly_pos, accounting | All files | Computed at load time; 0%, 33%, 67%, 100% |
| **Revenue band** | restaurants.annual_revenue_estimate → revenue_band | restaurants | Assigned at load time; bands: €0–500k, €500k–1M, €1M–1.5M, €1.5M+ |
| **Restaurant-specific risk indicators** | accounting.prime_cost_ratio, accounting.rent_to_revenue, monthly_pos.delivery_platform_share, monthly_pos.weekend_share | accounting, monthly_pos | Checkboxes or toggles: "High prime cost" (>0.70), "High rent" (>0.12), "High delivery dependency" (>35%), "High weekend dependency" (>60%) |

---

## Expected Data Coverage

| File | Restaurants | Rows per restaurant | Total rows | Notes |
|------|-------------|---------------------|------------|-------|
| restaurants.csv | 80 | 1 | 80 | Static profiles |
| monthly_bank.csv | 80 | 12 (months) | 960 | 12 months per restaurant |
| monthly_pos.csv | 80 | 12 (months) | 960 | 12 months per restaurant |
| accounting.csv | 80 | 1 (year) | 80 | Annual summary per restaurant |
| lenders.csv | N/A | N/A | 5–10 | Demo lenders (optional) |

---

## Missing Data Handling

The MVP scoring engine is designed to handle missing sources gracefully:

- If **monthly_bank.csv** data is absent for a restaurant: cash-flow dimension receives neutral score 50; data-completeness score reflects missing source
- If **monthly_pos.csv** data is absent: revenue stability, POS demand quality, seasonality dimensions receive neutral score 50; data-completeness reduced
- If **accounting.csv** data is absent: prime cost, rent pressure, debt burden dimensions receive neutral score 50; data-completeness reduced
- **Passport still generates and is displayable**, but lender confidence is lower due to reduced data-completeness score

---

## What Is Deliberately NOT Included

The CSV files store operational and financial inputs **only**. The following are computed at runtime and never stored in raw form:

- All derived ratios (prime cost, rent-to-revenue, EBITDA margin, debt-to-revenue, RevPASH, etc.)
- All sub-scores (0–100 per dimension)
- Composite score (0–100)
- Grade (A–E)
- Risk band (Low, Medium, High)
- Peer percentiles
- Written risk drivers
- Owner/identity verification flags
- Real lender offers or loan terms
- Real bank account numbers, POS system identifiers, or other sensitive identifiers

---

## Next Steps (Post-Approval)

Once this schema is approved, the implementation proceeds as follows:

1. **Synthetic data generation:** Write a Python script that generates 80 restaurants and 12 months of bank/POS/accounting data using the fixed seed, distribution strategy, and coherence constraints defined above.

2. **Data validation:** Load the CSV files and confirm all consistency constraints and reasonable ranges are met.

3. **Data-loading utilities:** Write Python functions to load CSVs, compute derived fields at load time, and provide clean interfaces for the scoring engine.

4. **Scoring engine:** Implement the nine-dimension scoring logic as per `docs/mvp_design.md`, using the derived fields from the data loader.

5. **Credit Passport and dashboard:** Build the frontend pages to display scores, grades, and lender filtering using the computed outputs.
