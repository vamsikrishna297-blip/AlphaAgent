# India Market Feasibility Assessment for AlphaAgent

## Executive Summary

**Feasibility: High (with moderate integration work).**

AlphaAgent is structurally reusable for Indian equities because the core agent loop, factor execution pipeline, and backtest orchestration are market-agnostic. The current repository is, however, **operationally China-first** (and partially US-supported) due to hardcoded data paths, region defaults, and CN-focused templates/prompts.

A focused market-adaptation pass should make India support practical without changing the core architecture.

## What Already Works for an India Rollout

1. **Core multi-agent pipeline is generic**
   - Idea/Factor/Eval loop does not enforce China-specific symbols at architecture level.

2. **Qlib-based templates already support multiple regions conceptually**
   - Existing US template (`conf_us_combined_kdd_ver.yaml`) shows the project can be run with non-CN provider URI and region values.

3. **Factor merge/dedup/backtest runner is reusable**
   - Factor orchestration can be reused once an India-compatible Qlib dataset + market universe are supplied.

## Current India Blockers (Code + Config)

### 1) Environment bootstrapping is CN hardcoded
- Local environment preparation always checks/downloads `~/.qlib/qlib_data/cn_data` and sets `--region cn`.
- Local Qlib env checks only CN path existence.

### 2) Backtest config selection is CN hardcoded for combined runs
- Combined-factor runs always pick `conf_cn_combined_kdd_ver.yaml`.

### 3) Data generation template defaults to CN dataset
- `factor_data_template/generate.py` initializes Qlib with CN data URI.

### 4) Documentation + quickstart are CN-centric
- Current setup uses Baostock CN flow and CSI index examples.

### 5) Prompting language includes China-market assumptions
- Some prompt files explicitly reference China A-share context, which can bias idea generation for India.

## Feasibility Verdict

- **Technical feasibility:** ✅ Strong
- **Effort level:** ⚠️ Medium (mostly configuration/refactor + data pipeline)
- **Main dependency risk:** Availability/quality/licensing of India historical equities + index constituents in Qlib-compatible format

## Recommended Migration Plan (India)

### Phase 1 — Configurability Refactor (low risk)
1. Introduce environment variables for:
   - `QLIB_PROVIDER_URI` (e.g., `~/.qlib/qlib_data/in_data`)
   - `QLIB_REGION` (custom, or reuse supported market config approach)
   - `QLIB_MARKET` (e.g., `NIFTY500` / custom instrument file)
2. Replace CN literals in env bootstrap and runner config selection.
3. Add India-specific config templates (parallel to CN/US templates).

### Phase 2 — India Data Pipeline (critical path)
1. Build/plug a data collector for NSE/BSE (or approved vendor) OHLCV + adjustments.
2. Convert into Qlib binary format with correct calendar/instrument metadata.
3. Validate survivorship handling, splits/bonus adjustments, and liquidity filters.

### Phase 3 — Prompt/Universe Alignment
1. Add India-neutral prompt variants or parameterized market prompt context.
2. Update benchmark/index references (e.g., NIFTY50/NIFTY500).
3. Retune costs/limit rules for local market microstructure.

### Phase 4 — Validation
1. Reproduce baseline model metrics on India universe.
2. Run factor-mining loop for 2–3 hypotheses.
3. Compare IC/IR decay and turnover vs CN baseline expectations.

## Suggested Definition of Done

India support can be considered production-ready when:
- A single `.env` switch changes market from CN/US to India.
- Backtest templates load India data path and universe automatically.
- At least one stable baseline + one generated-factor run completes end-to-end.
- Documentation includes exact India data preparation commands.

## Practical Next Step

If you want, the next PR can implement a **minimal India-enablement skeleton**:
- remove CN hardcodes in env + runner,
- add `conf_in_combined_kdd_ver.yaml` template,
- wire `.env`-driven provider/region/market selection,
- keep data collection script as placeholder interface for your preferred India vendor.


## Implemented in this repo now

The following India-enablement pieces are now available:
- India factor templates for `NIFTY500` and `NIFTY300`:
  - `alphaagent/scenarios/qlib/experiment/factor_template/conf_in_nifty500.yaml`
  - `alphaagent/scenarios/qlib/experiment/factor_template/conf_in_nifty300.yaml`
  - `alphaagent/scenarios/qlib/experiment/factor_template/conf_in_nifty500_combined_kdd_ver.yaml`
  - `alphaagent/scenarios/qlib/experiment/factor_template/conf_in_nifty300_combined_kdd_ver.yaml`
- Environment-driven config selection via:
  - `QLIB_FACTOR_BASE_CONFIG`
  - `QLIB_FACTOR_COMBINED_CONFIG`
- Environment-driven default data bootstrap via:
  - `QLIB_DEFAULT_DATA_DIR`
  - `QLIB_DEFAULT_REGION`
