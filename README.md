# NVIDIA Job Hunter

Starter project for monitoring NVIDIA early-career opportunities in Israel and sending new matches by Gmail.

## Current stage

This starter includes:
- Gmail SMTP notification module (using a Gmail App Password for a prototype).
- Job filtering rules.
- Persistent duplicate tracking in `data/seen_jobs.json`.
- A scheduled GitHub Actions workflow template.

**Important:** NVIDIA's current public careers portal is `https://jobs.nvidia.com/careers` and is powered by Eightfold. The job-source adapter in `agent/job_search.py` is intentionally a safe placeholder until its current public search response/API is inspected and implemented. The program will not pretend that it searched successfully or send false alerts. Do not enable the scheduled workflow until the source adapter is completed and tested.

## 1. Requirements

- Windows 10/11
- Python 3.11+
- A GitHub account/repository (for cloud scheduling)
- Gmail account with 2-Step Verification and an App Password, if Google offers App Passwords for your account

## 2. Run locally

Open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and fill in:
- `GMAIL_ADDRESS`: Gmail address used to send the alerts
- `GMAIL_APP_PASSWORD`: 16-character Google App Password (not your normal Gmail password)
- `ALERT_TO_EMAIL`: address that should receive alerts (can be the same Gmail address)

Never commit `.env` to GitHub.

Send a test email:

```powershell
python -m agent.main --test-email
```

Expected result: a test message arrives at `ALERT_TO_EMAIL`.

## 3. Gmail setup

1. Open your Google Account security settings.
2. Enable 2-Step Verification.
3. If App Passwords are available, create one for this project.
4. Copy the generated password into `.env` as `GMAIL_APP_PASSWORD`.
5. Do not share the password in chat or commit it to Git.

For a production-grade deployment, Gmail OAuth 2.0 is preferable to an App Password. This prototype uses SMTP over SSL on `smtp.gmail.com:465`.

## 4. GitHub Actions secrets

After the local email test succeeds, create a **private** GitHub repository and upload the project (excluding `.env` and `.venv`).

In GitHub:
`Repository → Settings → Secrets and variables → Actions → New repository secret`

Create:
- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD`
- `ALERT_TO_EMAIL`

The workflow uses `Asia/Jerusalem` timezone and is configured for 08:00 and 20:00 local time. GitHub scheduled runs can be delayed, so treat these as target times, not guaranteed exact delivery times.

**Keep the workflow disabled until `job_search.py` is implemented and verified.**

## 5. Project layout

```text
agent/
  config.py          Environment configuration
  email_notifier.py  Gmail notification
  job_filter.py      Student/junior relevance rules
  job_search.py      NVIDIA source adapter (TODO)
  storage.py         Persistent deduplication
  main.py            Orchestrator
data/
  seen_jobs.json     IDs already notified
.github/workflows/
  job_hunter.yml     Twice-daily schedule
```

## 6. Search policy

- NVIDIA only.
- Israel locations only (e.g. Tel Aviv, Yokneam, Ra'anana, Jerusalem, Haifa and other Israeli locations).
- Include Student, Intern, Internship, New College Grad, Entry Level, Junior and Early Career roles.
- Include relevant software, CS, AI/ML, data, algorithms, security, systems and engineering roles.
- Exclude senior, staff, principal, lead, director and management roles unless a future rule explicitly overrides this.
- Send only newly discovered matching jobs; suppress repeats by stable job ID or canonical URL.

## Next development milestone

Implement and test the official NVIDIA job-source adapter against live search results. Only after it correctly extracts job ID, title, location, description and application URL should the schedule be enabled.
