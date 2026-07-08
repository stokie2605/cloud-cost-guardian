# CLAUDE.md

This file is lightweight project memory for AI-assisted work on Cloud Cost Guardian.
It is documentation only and does not affect the application runtime.

## 1. Git Workflow

- Main branch: main
- Commit style: short, practical messages that describe the user-facing change.
- Push policy: push only after checks pass or documentation-only changes are reviewed.
- Avoid unrelated cleanup while working on a focused change.

## 2. Project Purpose

AWS FinOps automation project that detects idle EBS volumes and Elastic IP waste, estimates recurring cost, and presents operational evidence through scripts and a dashboard.

Primary stack: Python, boto3, Docker, React, Vite, GitHub Actions.

## 3. Decisions

- Use AWS APIs and mocked tests rather than hardcoded findings.
- Keep credentials out of the repo and rely on standard AWS credential providers.
- Preserve Docker/ECS/Fargate positioning as an automation pattern.
- Do not add destructive cleanup actions without explicit dry-run and approval controls.

## 4. Session Mode

- Read this file and README.md before making non-trivial changes.
- Explain intent before multi-file edits.
- Run the relevant check command where practical: $(System.Collections.Hashtable.Check).
- Keep copy technical, plain, and recruiter-safe.
- Do not introduce secrets, real customer data, or unrelated commercial positioning.

## 5. Current State

### What got done

- Repository is part of the active portfolio set.
- README explains the project purpose and reviewer-facing evidence.
- Project memory has been added so future work starts with context.

### Where things stand

- Current positioning: AWS FinOps automation project that detects idle EBS volumes and Elastic IP waste, estimates recurring cost, and presents operational evidence through scripts and a dashboard.
- Review command/context: $(System.Collections.Hashtable.Check).

### Next

- Clean README encoding artefacts and document any live/demo boundary more clearly.

### Blocked on

- Nothing.