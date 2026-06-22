# Cloud Cost Guardian

A Python-based cloud compliance and governance scanner that simulates corporate infrastructure audits. It identifies orphaned storage cost risks, flags public security exposures, and calculates financial optimization metrics.

## Features

- **Cost Leak Tracking:** Detects unattached volumes, idle database assets, and underutilized compute.
- **Security Exposure Detection:** Identifies public SSH/RDP exposure vectors, public database access, and unencrypted storage.
- **Flexible Reporting:** Dual-format CLI output generating automated Markdown reports or raw JSON summaries.
- **Mock Infrastructure Generation:** Creates repeatable AWS/Azure-style sample data for demos, testing, and portfolio walkthroughs.

## Technical Toolkit

- Python 3
- JSON/Data Serialization
- CLI Argument Parsing (`argparse`)
- Markdown report generation

## How to Run

Run a standard scan and generate a Markdown optimization report:

```bash
python cost_guardian.py --format markdown
```

Run a scan and output raw JSON data for downstream pipelines:

```bash
python cost_guardian.py --format json
```

## Generated Files

- `mock_cloud_infrastructure.json` - generated mock infrastructure inventory
- `cloud_cost_report.md` - technician-ready Markdown optimization report
- `cloud_cost_summary.json` - raw JSON findings summary when using `--format json`

## Example Output

The default mock scan highlights annualized waste, prioritized remediation actions, and public exposure findings that are useful for IT operations, DevOps, FinOps, and cloud governance conversations.
