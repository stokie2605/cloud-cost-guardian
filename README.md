# Cloud Cost Guardian

[🚀 Live Demo](https://cloud-cost-guardian-ten.vercel.app)

Built by Dean Wilshaw.

Cloud Cost Guardian is a full-stack cloud governance simulation that combines cost analysis, security exposure detection, executive reporting, and containerized delivery. It generates a realistic AWS/Azure-style infrastructure dataset, identifies waste and risk, exports technician-ready reports, and presents the findings through a modern React dashboard.

The project is designed to demonstrate practical FinOps, DevOps, cloud compliance, and frontend integration skills in one portfolio-ready repository.

### Visual Output / Preview

![Cloud Cost Guardian dashboard](screenshots/cloud-cost-dashboard.png)

```text
+--------------------------+----------------+
| Governance Metric        | Current Scan   |
+--------------------------+----------------+
| Monthly waste detected   | $413.81        |
| Annualized waste         | $4,965.72      |
| Security exposures       | 3              |
| Total findings           | 10             |
+--------------------------+----------------+
```

### Scanner Architecture & Governance Logic

- Generates a repeatable mock cloud estate containing compute instances, storage volumes, and managed databases.
- Detects unattached EBS/Azure storage, idle RDS-style databases, underutilized compute, public admin ingress, public database access, and unencrypted storage.
- Calculates monthly and annualized waste from resource type, size, instance class, and hourly/monthly cost assumptions.
- Sorts findings by severity and financial impact so security-critical and high-cost items rise to the top.
- Exports either a Markdown optimization report or a raw JSON summary through the `--format` CLI flag.
- Provides a React/Vite dashboard with search, executive metrics, severity badges, and a report-to-JSON view toggle.
- Ships with Docker and Docker Compose so reports can be generated in a clean container with host volume persistence.

## The Business Problem

Cloud environments often accumulate unused storage, idle databases, forgotten development compute, and overly permissive public access rules. These issues create two visible operational problems: unnecessary monthly spend and avoidable security exposure.

For IT leaders, DevOps teams, and cloud administrators, the challenge is not only finding the waste, but presenting it in a way that creates fast remediation decisions.

## The Solution & Architecture

Cloud Cost Guardian simulates that governance workflow end to end:

```text
Mock Cloud Estate
       |
       v
Python Scanner
       |
       +--> Cost Leak Detection
       +--> Security Exposure Detection
       +--> Severity + Recommendation Mapping
       |
       v
Markdown / JSON Reports
       |
       v
React Executive Dashboard
       |
       v
Dockerized Runtime with Host Report Volume
```

## Technical Toolkit

- **Python 3.11** for scanner logic, cost calculations, data modeling, and report generation.
- **argparse** for CLI execution with `--format markdown` and `--format json` modes.
- **JSON** for mock infrastructure inventory and automation-friendly output.
- **Markdown** for technician-ready optimization reports.
- **React + Vite** for the interactive cloud optimization dashboard.
- **Tailwind CDN utilities** for the dark operations-console style UI.
- **Docker + Docker Compose** for portable scanner execution and host-mounted report output.
- **Git/GitHub** for version-controlled delivery and public portfolio presentation.

## Local Scanner Usage

Generate a Markdown optimization report:

```bash
python cost_guardian.py --format markdown
```

Generate a raw JSON summary for downstream tooling:

```bash
python cost_guardian.py --format json
```

The scanner writes the mock inventory and output files into the current working directory.

## Frontend Dashboard Usage

Install dependencies:

```bash
npm install
```

Run the Vite development server:

```bash
npm run dev
```

Create a production build:

```bash
npm run build
```

The dashboard highlights the same simulated governance results as an executive-facing visual report card, with a searchable findings table and raw JSON log view.

## Container Deployment (Docker)

Build the image:

```bash
docker build -t cloud-cost-guardian .
```

Run the scanner directly with Docker and write reports to the host:

```bash
docker run --rm -v "${PWD}/reports:/app/reports" -w /app/reports cloud-cost-guardian --format markdown
```

Run the JSON mode directly with Docker:

```bash
docker run --rm -v "${PWD}/reports:/app/reports" -w /app/reports cloud-cost-guardian --format json
```

Run the default Markdown scan through Docker Compose:

```bash
docker compose up --build
```

Pass CLI flags through Docker Compose:

```bash
docker compose run --rm cost-scanner --format markdown
docker compose run --rm cost-scanner --format json
```

Docker Compose maps `./reports` on the host to `/app/reports` inside the container so generated evidence survives after the container exits.

## Generated Files

| File | Purpose |
| --- | --- |
| `mock_cloud_infrastructure.json` | Generated AWS/Azure-style infrastructure inventory |
| `cloud_cost_report.md` | Markdown optimization report for technicians and stakeholders |
| `cloud_cost_summary.json` | Raw JSON summary for pipeline or API-style consumption |
| `reports/` | Host-mounted Docker output directory |

## Finding Categories

| Category | Example Detection |
| --- | --- |
| Orphaned storage | Unattached GP3, IO2, or standard managed disks |
| Idle database | Low CPU and near-zero connection managed databases |
| Underutilized compute | Running instances averaging under 5% CPU |
| Security exposure | Public SSH/RDP, public database access, or unencrypted storage |

## Production Readiness Notes

- The scanner keeps cost assumptions centralized in a `RATES` table for simple tuning.
- Findings include severity, category, provider, region, monthly waste, recommendation, and detail fields.
- Markdown output is suitable for evidence packs, ticket attachments, and portfolio walkthroughs.
- JSON output is structured for future API ingestion, dashboards, or CI/CD governance checks.
- The container workflow keeps generated reports outside the image through a host-mounted volume.
