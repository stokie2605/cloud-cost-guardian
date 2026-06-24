import React, { useMemo, useState } from "react";
import scannerSummary from "./src/data/cloud_findings.json";

const severityStyles = {
  critical: "border-red-400/40 bg-red-500/15 text-red-100",
  high: "border-amber-300/40 bg-amber-400/15 text-amber-100",
  medium: "border-sky-300/40 bg-sky-400/15 text-sky-100",
  low: "border-emerald-300/40 bg-emerald-400/15 text-emerald-100",
};

const statusStyles = {
  "Safe to Delete": "bg-emerald-400/15 text-emerald-100 ring-emerald-300/30",
  "Needs Review": "bg-amber-400/15 text-amber-100 ring-amber-300/30",
  "Lock Down": "bg-red-500/15 text-red-100 ring-red-300/30",
  Rightsize: "bg-cyan-400/15 text-cyan-100 ring-cyan-300/30",
  Encrypt: "bg-violet-400/15 text-violet-100 ring-violet-300/30",
};

const categoryLabels = {
  orphaned_storage: "Orphaned Storage",
  idle_database: "Idle Database",
  underutilized_compute: "Underutilized Compute",
  security_exposure: "Security Exposure",
};

function currency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: scannerSummary.currency || "USD",
  }).format(value);
}

function formatProvider(provider) {
  if (provider.toLowerCase() === "aws") {
    return "AWS";
  }

  return provider.charAt(0).toUpperCase() + provider.slice(1);
}

function getStatus(finding) {
  const detail = finding.detail.toLowerCase();

  if (finding.category === "orphaned_storage") {
    return "Safe to Delete";
  }

  if (finding.category === "idle_database") {
    return "Needs Review";
  }

  if (finding.category === "underutilized_compute") {
    return "Rightsize";
  }

  if (detail.includes("encrypted")) {
    return "Encrypt";
  }

  if (detail.includes("admin") || detail.includes("port")) {
    return "Lock Down";
  }

  return "Needs Review";
}

function normalizeFinding(finding) {
  return {
    severity: finding.severity,
    category: categoryLabels[finding.category] || finding.category,
    rawCategory: finding.category,
    resourceId: finding.resource_id,
    provider: formatProvider(finding.provider),
    region: finding.region,
    monthlyWaste: finding.monthly_waste_usd,
    status: getStatus(finding),
    detail: finding.detail,
    recommendation: finding.recommendation,
  };
}

function buildMarkdownChecklist(summary, findings) {
  const groupedFindings = findings.reduce((groups, finding) => {
    const key = finding.severity.toUpperCase();
    return {
      ...groups,
      [key]: [...(groups[key] || []), finding],
    };
  }, {});

  const sections = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    .filter((severity) => groupedFindings[severity]?.length)
    .map((severity) => {
      const rows = groupedFindings[severity]
        .map(
          (finding) =>
            `- [ ] \`${finding.resourceId}\` (${finding.category}, ${finding.region}): ${finding.recommendation}`
        )
        .join("\n");

      return `## ${severity}\n\n${rows}`;
    })
    .join("\n\n");

  return `# Cloud Cost Guardian Remediation Checklist

Generated: ${summary.generated_at}
Organization: ${summary.organization}

## Executive Summary

- Estimated monthly waste: ${currency(summary.estimated_monthly_waste_usd)}
- Estimated annualized waste: ${currency(summary.estimated_annual_waste_usd)}
- Findings: ${summary.finding_count}
- Security exposures: ${summary.security_exposure_count}

${sections}
`;
}

function downloadJson(summary) {
  const blob = new Blob([JSON.stringify(summary, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = "cloud_cost_summary.json";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "absolute";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

export default function CloudDashboard() {
  const [query, setQuery] = useState("");
  const [viewMode, setViewMode] = useState("report");
  const [exportMessage, setExportMessage] = useState("");

  const findings = useMemo(
    () => scannerSummary.findings.map((finding) => normalizeFinding(finding)),
    []
  );

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
        finding.recommendation,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery)
    );
  }, [findings, query]);

  const totals = useMemo(
    () => ({
      monthlyWaste: scannerSummary.estimated_monthly_waste_usd,
      annualWaste: scannerSummary.estimated_annual_waste_usd,
      exposures: scannerSummary.security_exposure_count,
      critical: scannerSummary.findings.filter((finding) => finding.severity === "critical")
        .length,
    }),
    []
  );

  function handleJsonExport() {
    downloadJson(scannerSummary);
    setExportMessage("JSON summary downloaded.");
  }

  async function handleMarkdownCopy() {
    const checklist = buildMarkdownChecklist(scannerSummary, findings);
    await copyText(checklist);
    setExportMessage("Markdown remediation checklist copied.");
  }

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
      <section className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="flex flex-col justify-between gap-4 border-b border-white/10 pb-6 lg:flex-row lg:items-end">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-cyan-300">
              Cloud Cost Guardian
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">
              Cloud Optimization Dashboard
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
              Scanner-backed console for prioritizing cost leaks, security exposures, and
              remediation work across AWS and Azure estates.
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Source: Python scanner output at src/data/cloud_findings.json
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:items-end">
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

            <div className="flex flex-wrap gap-2 sm:justify-end">
              <button
                className="rounded-md border border-emerald-300/30 bg-emerald-400/10 px-4 py-2 text-sm font-medium text-emerald-100 transition hover:bg-emerald-400/20"
                type="button"
                onClick={handleJsonExport}
              >
                Download JSON Summary
              </button>
              <button
                className="rounded-md border border-cyan-300/30 bg-cyan-400/10 px-4 py-2 text-sm font-medium text-cyan-100 transition hover:bg-cyan-400/20"
                type="button"
                onClick={handleMarkdownCopy}
              >
                Copy Markdown Checklist
              </button>
            </div>
            {exportMessage ? <p className="text-xs text-slate-400">{exportMessage}</p> : null}
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-4">
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
              {totals.exposures} Public Exposures
            </p>
            <p className="mt-2 text-sm text-red-100/80">Prioritize before cost cleanup.</p>
          </div>

          <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-slate-950/30">
            <p className="text-sm text-slate-400">Scanner findings</p>
            <p className="mt-3 text-4xl font-semibold text-white">{scannerSummary.finding_count}</p>
            <p className="mt-2 text-sm text-slate-300">
              {scannerSummary.asset_counts.ec2_instances} compute /{" "}
              {scannerSummary.asset_counts.ebs_volumes} storage /{" "}
              {scannerSummary.asset_counts.rds_databases} databases
            </p>
          </div>
        </section>

        <section className="rounded-lg border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-slate-950/30">
          <h2 className="text-lg font-semibold text-white">Scanner to UI Pipeline</h2>
          <div className="mt-4 grid gap-3 text-sm text-slate-300 md:grid-cols-4">
            {["Python scanner", "JSON findings", "React dashboard", "Export actions"].map(
              (step, index) => (
                <div className="rounded-md border border-white/10 bg-slate-950/50 p-4" key={step}>
                  <p className="text-xs uppercase tracking-wide text-cyan-300">Step {index + 1}</p>
                  <p className="mt-2 font-medium text-white">{step}</p>
                </div>
              )
            )}
          </div>
        </section>

        {viewMode === "report" ? (
          <section className="rounded-lg border border-white/10 bg-white/[0.04] shadow-2xl shadow-slate-950/30">
            <div className="flex flex-col gap-4 border-b border-white/10 p-5 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">Prioritized Findings</h2>
                <p className="mt-1 text-sm text-slate-400">
                  Search by resource, region, provider, status, recommendation, or finding type.
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
                    <th className="px-5 py-3 font-medium">Monthly Waste</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Severity</th>
                    <th className="px-5 py-3 font-medium">Recommendation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {filteredFindings.map((finding, index) => (
                    <tr className="transition hover:bg-white/[0.03]" key={`${finding.resourceId}-${index}`}>
                      <td className="px-5 py-4">
                        <div className="font-medium text-white">{finding.resourceId}</div>
                        <div className="mt-1 text-xs text-slate-400">
                          {finding.provider} / {finding.category}
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
                            severityStyles[finding.severity] || severityStyles.low
                          }`}
                        >
                          {finding.severity}
                        </span>
                      </td>
                      <td className="max-w-md px-5 py-4 text-slate-300">
                        <p>{finding.recommendation}</p>
                        <p className="mt-1 text-xs text-slate-500">{finding.detail}</p>
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
                Imported directly from the scanner-generated src/data/cloud_findings.json file.
              </p>
            </div>
            <pre className="max-h-[560px] overflow-auto p-5 text-xs leading-6 text-cyan-100">
              {JSON.stringify(scannerSummary, null, 2)}
            </pre>
          </section>
        )}
      </section>
    </main>
  );
}
