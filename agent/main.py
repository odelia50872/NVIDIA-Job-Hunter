
import argparse

from .config import get_settings
from .email_notifier import send_test_email, send_email
from .job_filter import (
    is_relevant,
    calculate_relevance_score,
    get_score_breakdown
)
from .job_search import fetch_nvidia_jobs
from .storage import load_seen_ids, save_seen_ids


# Minimum score required for a job to trigger an email alert.
MIN_MATCH_SCORE = 60


def format_job(job: dict, score: int) -> str:
    locations = job.get("location", [])

    if isinstance(locations, list):
        cleaned_locations = [
            loc.replace("Israel, ", "").strip()
            for loc in locations
        ]
        location_text = ", ".join(cleaned_locations)
        location_text += ", Israel"
    else:
        location_text = str(locations or "Not specified")

    description = job.get("description", "Not available")
    public_url = job.get("url", "")
    apply_url = job.get("apply_url", "") or public_url

    # Explain how the relevance score was calculated.
    breakdown = get_score_breakdown(job)

    score_details = "\n".join(
        f"+{points} points - {reason}"
        for reason, points in breakdown
    )

    return (
        "NVIDIA JOB ALERT\n"
        "==============================\n\n"
        f"{job.get('title', 'Not specified')}\n\n"
        f"Match Score: {score} points\n\n"
        "MATCH ANALYSIS\n"
        "------------------------------\n"
        f"{score_details}\n\n"
        f"Location: {location_text}\n"
        f"Job Type: {job.get('job_type', 'Not specified')}\n"
        f"Posted Date: {job.get('posted_date', 'Not specified')}\n\n"
        "JOB DESCRIPTION\n"
        "------------------------------\n"
        f"{description}\n\n"
        "JOB LINKS\n"
        "------------------------------\n"
        f"View Job: {public_url}\n"
        f"Apply Here: {apply_url}\n\n"
        "Good luck with your application!\n"
        "NVIDIA Job Hunter"
    )


def run_agent(dry_run: bool = False) -> None:
    settings = get_settings()

    jobs = fetch_nvidia_jobs()
    seen = load_seen_ids()

    new_jobs = []

    for job in jobs:
        job_id = str(job.get("id") or "").strip()

        if not job_id or job_id in seen:
            continue

        if is_relevant(job):
            score = calculate_relevance_score(job)

            # Include only jobs that meet the minimum score.
            if score >= MIN_MATCH_SCORE:
                new_jobs.append((score, job_id, job))

    # Send or display the strongest matches first.
    new_jobs.sort(key=lambda item: item[0], reverse=True)

    print(f"\nMinimum match score: {MIN_MATCH_SCORE}")
    print("\n--- MATCHING JOBS ---")

    for score, job_id, job in new_jobs:
        print(f"\nTitle: {job.get('title')}")
        print(f"Location: {job.get('location')}")
        print(f"Job Type: {job.get('job_type')}")
        print(f"Match Score: {score}")

        # Prepare the email subject with the match score.
        subject = (
            f"[{score} Points] NVIDIA Job Opportunity - "
            f"{job.get('title', 'New Position')}"
        )

        if dry_run:
            print("\n" + "=" * 70)
            print("EMAIL PREVIEW")
            print("=" * 70)

            print(f"\nTo: {settings.alert_to_email}")
            print(f"Subject: {subject}")

            print("\nEmail Body:")
            print("-" * 70)
            print(format_job(job, score))
            print("-" * 70)

            print("\nMode: DRY RUN - Email not sent")
            continue

        # Send the email.
        send_email(
            settings,
            subject,
            format_job(job, score)
        )

        # Mark this job as seen after a successful email.
        seen.add(job_id)

        # Save immediately to prevent duplicate emails
        # if a later email fails.
        save_seen_ids(seen)

    print(f"\nCompleted. Matching jobs found: {len(new_jobs)}")

    if dry_run:
        print("DRY RUN: No emails were sent and no IDs were saved.")


def main():
    parser = argparse.ArgumentParser(
        description="NVIDIA Job Hunter"
    )

    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Send a test email"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search and rank jobs without sending emails"
    )

    args = parser.parse_args()

    settings = get_settings()

    if args.test_email:
        send_test_email(settings)
        print(
            f"Test email sent to {settings.alert_to_email}"
        )
    else:
        run_agent(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
