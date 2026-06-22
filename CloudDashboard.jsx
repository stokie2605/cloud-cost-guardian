import { useMemo, useState } from "react";

const findings = [
  {
    severity: "critical",
    category: "Security Exposure",
    resourceId: "db-old-crm",
    provider: "AWS",
    region: "us-east-1",
    monthlyWaste: 0,
    status: "Needs Review",
    detail: "Database is publicly accessible.",
  },
  {
    severity: "critical",
    category: "Security Exposure",
    resourceId: "i-0b45admin01",
    provider: "AWS",
    region: "us-east-1",
    monthlyWaste: 0,
    status: "Lock Down",
    detail: "Public instance exposes admin ports 22 and 3389.",
  },
  {
    severity: "high",
    category: "Orphaned Storage",
    resourceId: "vol-0cc333",
    provider: "AWS",
    region: "eu-west-2",
    monthlyWaste: 256,
    status: "Safe to Delete",
    detail: "2048 GB io2 volume is unattached.",
  },
  {
    severity: "high",
    category: "Idle Database",
    resourceId: "db-old-crm",
    provider: "AWS",
    region: "us-east-1",
    monthlyWaste: 24.82,
    status: "Needs Review",
    detail: "db.t3.small averages 0.7% CPU and 0 connections.",
  },
  {
    severity: "medium",
    category: "Orphaned Storage",
    resourceId: "vol-0bb222",
    provider: "AWS",
    region: "us-east-1",
    monthlyWaste: 76,
    status: "Safe to Delete",
    detail: "950 GB gp3 volume is unattached.",
  },
  {
    severity: "medium",
    category: "Orphaned Storage",
    resourceId: "disk-az-4477",
    provider: "Azure",
    region: "eastus",
    monthlyWaste: 25.6,
    status: "Safe to Delete",
    detail: "512 GB standard volume is unattached.",
  },
  {
    severity: "medium",
    category: "Underutilized Compute",
    resourceId: "vm-az-dev-analytics-01",
    provider: "Azure",
    region: "eastus",
    monthlyWaste: 15.18,
    status: "Rightsize",
    detail: "t3.medium averages 1.4% CPU over 14 days.",
  },
  {
    severity: "medium",
    category: "Idle Database",
    resourceId: "sql-az-test-ledger",
    provider: "Azure",
    region: "eastus",
    monthlyWaste: 12.41,
    status: "Needs Review",
    detail: "db.t3.micro averages 1.1% CPU and 1 connection.",
  },
  {
    severity: "medium",
    category: "Underutilized Compute",
    resourceId: "i-0b45admin01",
    provider: "AWS",
    region: "us-east-1",
    monthlyWaste: 3.8,
    status: "Rightsize",
    detail: "t3.micro averages 3.2% CPU over 14 days.",
  },
  {
    severity: "medium",
    category: "Security Exposure",
    resourceId: "vol-0bb222",
    provider: "AWS",
    region: "us-east-1",
    monthlyWaste: 0,
    status: "Encrypt",
    detail: "Volume is not encrypted at rest.",
  },
];

const severityStyles = {
  critical: "border-red-400/40 bg-red-500/15 text-red-100",
  high: "border-amber-300/40 bg-amber-400/15 text-amber-100",
  medium: "border-sky-300/40 bg-sky-400/15 text-sky-100",
};

const statusStyles = {
  "Safe to Delete": "bg-emerald-400/15 text-emerald-100 ring-emerald-300/30",
  "Needs Review": "bg-amber-400/15 text-amber-100 ring-amber-300/30",
  "Lock Down": "bg-red-500/15 text-red-100 ring-red-300/30",
  Rightsize: "bg-cyan-400/15 text-cyan-100 ring-cyan-300/30",
  Encrypt: "bg-violet-400/15 text-violet-100 ring-violet-300/30",
};

function currency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export default function CloudDashboard() {
  const [query, setQuery] = useState("");
  const [viewMode, setViewMode] = useState("report");

  const filteredFindings = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      return findings;
    }

    return findings.filter((finding) =>
      [
        finding.resourceId,
        finding.provider,
        finding.region,
        finding.category,
        finding.status,
        finding.detail,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery)
    );
  }, [query]);

  const totals = useMemo(() => {
    const monthlyWaste = findings.reduce((sum, finding) => sum + finding.monthlyWaste, 0);
    const exposures = findings.filter((finding) => finding.category === "Security Exposure").length;
    const critical = findings.filter((finding) => finding.severity === "critical").length;

    return {
      monthlyWaste,
      annualWaste: monthlyWaste * 12,
      exposures,
      critical,
    };
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
      <section className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="flex flex-col justify-between gap-4 border-b border-white/10 pb-6 md:flex-row md:items-end">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-cyan-300">
              Cloud Cost Guardian
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">
              Cloud Optimization Dashboard
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
              Visual scanner console for prioritizing cost leaks, security exposures, and
              remediation work across AWS and Azure estates.
            </p>
          </div>

          <div className="inline-flex rounded-lg border border-white/10 bg-white/5 p-1">
            <button
              className={`rounded-md px-4 py-2 text-sm font-medium transition ${
                viewMode === "report"
                  ? "bg-cyan-300 text-slate-950"
                  : "text-slate-300 hover:bg-white/10 hover:text-white"
              }`}
              type="button"
              onClick={() => setViewMode("report")}
            >
              Visual Report Card
            </button>
            <button
              className={`rounded-md px-4 py-2 text-sm font-medium transition ${
                viewMode === "json"
                  ? "bg-cyan-300 text-slate-950"
                  : "text-slate-300 hover:bg-white/10 hover:text-white"
              }`}
              type="button"
              onClick={() => setViewMode("json")}
            >
              Raw JSON Log View
            </button>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-slate-950/30">
            <p className="text-sm text-slate-400">Monthly waste detected</p>
            <p className="mt-3 text-4xl font-semibold text-white">{currency(totals.monthlyWaste)}</p>
            <p className="mt-2 text-sm text-emerald-300">Immediate FinOps opportunity</p>
          </div>

          <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-slate-950/30">
            <p className="text-sm text-slate-400">Annualized waste</p>
            <p className="mt-3 text-4xl font-semibold text-white">{currency(totals.annualWaste)}</p>
            <p className="mt-2 text-sm text-slate-300">Projected 12-month exposure</p>
          </div>

          <div className="rounded-lg border border-red-300/30 bg-red-500/10 p-5 shadow-2xl shadow-red-950/20">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-red-100">Security warning</p>
              <span className="rounded-full border border-red-300/30 bg-red-400/15 px-3 py-1 text-xs font-semibold text-red-100">
                {totals.critical} critical
              </span>
            </div>
            <p className="mt-3 text-3xl font-semibold text-white">
              {totals.exposures} Public Exposures Detected
            </p>
            <p className="mt-2 text-sm text-red-100/80">Prioritize before cost cleanup.</p>
          </div>
        </section>

        {viewMode === "report" ? (
          <section className="rounded-lg border border-white/10 bg-white/[0.04] shadow-2xl shadow-slate-950/30">
            <div className="flex flex-col gap-4 border-b border-white/10 p-5 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">Prioritized Findings</h2>
                <p className="mt-1 text-sm text-slate-400">
                  Search by resource, region, provider, status, or finding type.
                </p>
              </div>

              <label className="w-full md:w-80">
                <span className="sr-only">Search findings</span>
                <input
                  className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-4 py-2.5 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300 focus:ring-2 focus:ring-cyan-300/20"
                  placeholder="Search resources..."
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
              </label>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-white/10 text-left text-sm">
                <thead className="bg-white/[0.03] text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-5 py-3 font-medium">Resource</th>
                    <th className="px-5 py-3 font-medium">Region</th>
                    <th className="px-5 py-3 font-medium">Monthly Cost</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Severity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {filteredFindings.map((finding, index) => (
                    <tr className="transition hover:bg-white/[0.03]" key={`${finding.resourceId}-${index}`}>
                      <td className="px-5 py-4">
                        <div className="font-medium text-white">{finding.resourceId}</div>
                        <div className="mt-1 text-xs text-slate-400">
                          {finding.provider} · {finding.category}
                        </div>
                      </td>
                      <td className="px-5 py-4 text-slate-300">{finding.region}</td>
                      <td className="px-5 py-4 font-medium text-white">
                        {currency(finding.monthlyWaste)}
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${
                            statusStyles[finding.status]
                          }`}
                        >
                          {finding.status}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold capitalize ${
                            severityStyles[finding.severity]
                          }`}
                        >
                          {finding.severity}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : (
          <section className="rounded-lg border border-white/10 bg-slate-900 shadow-2xl shadow-slate-950/30">
            <div className="border-b border-white/10 p-5">
              <h2 className="text-lg font-semibold text-white">Raw JSON Log View</h2>
              <p className="mt-1 text-sm text-slate-400">
                Scanner-style payload for downstream automation or evidence packs.
              </p>
            </div>
            <pre className="max-h-[560px] overflow-auto p-5 text-xs leading-6 text-cyan-100">
              {JSON.stringify(
                {
                  generatedBy: "cloud-cost-guardian",
                  totals,
                  findings,
                },
                null,
                2
              )}
            </pre>
          </section>
        )}
      </section>
    </main>
  );
}
