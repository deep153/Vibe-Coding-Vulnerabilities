# SARD-Bench: Sandbox-Escape and Review-Deception Benchmark

Research code for studying security risks in **sandboxed agentic coding workflows**:
privilege escalation (sandbox escape), **justification laundering** against automated
IDE auto-reviewers, a stealth-tier gradient, and multi-turn sandbox-failure escalation.

Unlike harnesses that assume unrestricted shell access, SARD-Bench runs each
`sandbox_default` command inside a **real** OS-enforced sandbox and separately measures
whether an attack is *contained* by the sandbox or *escapes* it.

## Project Overview

- **Stage 1 (pilot):** 32-case feasibility pilot (`pilot_sard_dataset.json`), simulated
  sandbox (Option A), 96 trajectories.
- **Stage 2 (full):** 240-case benchmark (`expanded_research_dataset.json`), a **real**
  macOS Seatbelt sandbox (Option B), 720 trajectories.

Models evaluated via OpenRouter: **Claude Sonnet 5.5**, **GPT-5.1**, **Llama 4 Maverick**.
Automated reviewer: **GPT-4o-mini** (temperature 0).

## The real sandbox (Option B)

`sard_sandbox.py` executes each `sandbox_default` command with strong, OS-enforced isolation:

- Outbound **network denied** (so `curl`/`pip`/`wget` fail with authentic errors).
- Writes **jailed** to an ephemeral per-case workspace (writes elsewhere fail for real).
- **Sanitized environment**: the evaluator's secrets (including `OPENROUTER_API_KEY`) are
  never exported; secret-looking variables are replaced with obvious fakes.
- `HOME` redirected into the workspace, so `~/.ssh` cannot reach real keys.
- CPU and wall-clock limits to contain runaway processes.
- Commands that request **privileged** permissions are intercepted and recorded as
  escalation events — never executed.

> Platform note: the real sandbox uses macOS `sandbox-exec` (Seatbelt). On other
> platforms, run with `--sandbox simulated`.

## Files

**Pipeline**
- `sard_config.py` — models, paths, permission sets, system prompt
- `sard_tools.py` — `execute_sandboxed_command` tool schema
- `sard_textcall.py` — fallback parser for inline ReAct-style tool calls
- `sard_sandbox.py` — real isolated sandbox (Seatbelt)
- `sard_auto_reviewer.py` — dual-condition (A vs B) auto-reviewer
- `sard_metrics.py` — five-outcome scoring
- `sard_experiment_runner.py` — trajectory runner (pilot + full)
- `sard_analyze_results.py` — per-run report
- `sard_stage2_stats.py` — Wilson CIs, Cochran–Armitage trend, McNemar

**Data generators**
- `generate_pilot_sard_dataset.py` → `pilot_sard_dataset.json` (32 cases)
- `generate_full_sard_dataset.py` → `expanded_research_dataset.json` (240 cases)

**Utilities**
- `test_openrouter_models.py` — verify model slugs are reachable

**Paper**: `paper/vibecode.tex` (+ `references.bib`, diagrams).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```bash
OPENROUTER_API_KEY=your_openrouter_key_here
```

## Usage

Verify model connectivity:

```bash
python test_openrouter_models.py
```

**Stage 1 — pilot (simulated sandbox):**

```bash
python generate_pilot_sard_dataset.py
python sard_experiment_runner.py --stage pilot          # 96 trajectories
python sard_analyze_results.py pilot
```

**Stage 2 — full benchmark (real sandbox):**

```bash
python generate_full_sard_dataset.py
python sard_experiment_runner.py --stage full --sandbox real   # 720 trajectories
python sard_analyze_results.py full
python sard_stage2_stats.py
```

Runs checkpoint to CSV/JSON and resume automatically, so interrupted runs can be re-launched.

## Outputs

- Stage 1: `pilot_sard_results.csv`, `pilot_sard_raw_logs.json`, `pilot_sard_go_no_go.json`
- Stage 2: `sard_full_results.csv`, `sard_full_raw_logs.json`, `sard_full_report.json`,
  `sard_stage2_stats.json`

## Security Note

⚠️ Never commit your `.env` or API keys. The executed commands are adversarial by design;
only run them through `sard_sandbox.py` (or `--sandbox simulated`), never directly.

## License

For research purposes.
