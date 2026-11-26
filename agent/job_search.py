
import requests
import time

from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from .job_filter import is_candidate_for_details


BASE_URL = "https://jobs.nvidia.com/api/pcsx"

SEARCH_URL = f"{BASE_URL}/search"
DETAILS_URL = f"{BASE_URL}/position_details"

LOCATIONS = [
    "Tel Aviv-Yafo, Tel Aviv District, Israel",
    "Ra'anana, Center District, Israel",
    "Jerusalem, Jerusalem District, Israel",
]


def clean_html(html):
    """Convert HTML job descriptions into readable text."""
    if not html:
        return "Not available"

    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def format_date(timestamp):
    """Convert a timestamp into a readable date."""
    if not timestamp:
        return "Not specified"

    return datetime.fromtimestamp(
        timestamp, tz=timezone.utc
    ).strftime("%Y-%m-%d")



def search_location(location):
    """Fetch jobs from both Intern and New College Graduate categories."""

    jobs = []
    job_types = [
        "Intern (Fixed Term)",
        "New College Graduate",
    ]

    for job_type in job_types:
        print(f"\nSearching job type: {job_type}")

        start = 0
        page_size = 10

        while True:
            params = {
                "domain": "nvidia.com",
                "query": "",
                "location": location,
                "start": start,
                "sort_by": "relevance",
                "filter_distance": 160,
                "filter_include_remote": 1,
                "filter_job_type": job_type,
            }

            response = None

            for attempt in range(4):
                try:
                    response = requests.get(
                        SEARCH_URL,
                        params=params,
                        timeout=30,
                    )

                    if response.status_code == 429:
                        wait_time = 15 * (attempt + 1)
                        print(
                            f"Rate limit reached. "
                            f"Waiting {wait_time} seconds..."
                        )
                        time.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    break

                except RequestException:
                    if attempt == 3:
                        raise

                    wait_time = 5 * (attempt + 1)
                    print(
                        f"Request failed. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)

            if response is None or response.status_code == 429:
                raise RuntimeError(
                    f"NVIDIA rate limit persisted for {location}"
                )

            payload = response.json()

            if payload.get("status") != 200:
                raise RuntimeError(
                    f"NVIDIA search API error: {payload}"
                )

            positions = payload.get("data", {}).get("positions", [])

            if not positions:
                break

            for position in positions:
                position_with_type = dict(position)
                position_with_type["_job_types"] = [job_type]
                jobs.append(position_with_type)

            start += len(positions)

            print(
                f"Retrieved {len(positions)} jobs "
                f"for {job_type}. Total: {len(jobs)}"
            )

            if len(positions) < page_size:
                break

            time.sleep(2)

    return jobs


def get_job_details(position_id, queried_location):
    """Fetch full job details with retry protection."""

    params = {
        "position_id": position_id,
        "domain": "nvidia.com",
        "hl": "en",
        "queried_location": queried_location,
    }

    response = None

    # Try up to four times if the request fails.
    for attempt in range(4):
        try:
            response = requests.get(
                DETAILS_URL,
                params=params,
                timeout=30,
            )

            if response.status_code == 429:
                wait_time = 15 * (attempt + 1)

                print(
                    f"Rate limit reached while fetching job "
                    f"{position_id}. "
                    f"Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)
                continue

            response.raise_for_status()
            break

        except RequestException:
            if attempt == 3:
                raise

            wait_time = 5 * (attempt + 1)

            print(
                f"Request failed for job {position_id}. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)

    if response is None or response.status_code == 429:
        raise RuntimeError(
            f"Could not fetch details for job {position_id}"
        )

    payload = response.json()

    if payload.get("status") != 200:
        raise RuntimeError(
            f"NVIDIA job details API error: {payload}"
        )

    return payload.get("data", {})


def fetch_nvidia_jobs():
    """Fetch and filter NVIDIA jobs in the requested locations."""

    positions_by_id = {}

    # Step 1: Search all requested locations.
    for location in LOCATIONS:
        print(f"\nSearching NVIDIA jobs in: {location}")

        positions = search_location(location)

        for position in positions:
            position_id = str(position.get("id", "")).strip()

            if not position_id:
                continue

            if position_id not in positions_by_id:
                positions_by_id[position_id] = {
                    "position": position,
                    "queried_location": location,
                    "job_types": list(position.get("_job_types", [])),
                }
            else:
                existing_types = positions_by_id[position_id]["job_types"]

                for job_type in position.get("_job_types", []):
                    if job_type not in existing_types:
                        existing_types.append(job_type)

    print(
        f"\nTotal unique positions found: "
        f"{len(positions_by_id)}"
    )

    # Step 2: Filter positions before requesting full details.
    candidate_positions = {}

    for position_id, item in positions_by_id.items():
        position = item["position"]

        if is_candidate_for_details(position):
            candidate_positions[position_id] = item

    print(
        f"Positions passing preliminary filter: "
        f"{len(candidate_positions)}"
    )

    # Step 3: Fetch full details only for candidates.
    jobs = []

    for position_id, item in candidate_positions.items():
        position = item["position"]

        print(
            f"Fetching details for: "
            f"{position.get('name', position_id)}"
        )

        details = get_job_details(
            position_id,
            item["queried_location"],
        )

        locations = (
            details.get("locations")
            or position.get("locations")
            or []
        )

        standardized_locations = (
            details.get("standardizedLocations")
            or position.get("standardizedLocations")
            or []
        )

        job_url = details.get("publicUrl")

        if not job_url:
            job_url = position.get("positionUrl", "")

            if job_url.startswith("/"):
                job_url = "https://jobs.nvidia.com" + job_url

        apply_action = (
            details.get("positionUserActions", {})
            .get("applyAction", {})
        )

        jobs.append({
            "id": position_id,

            "job_id": (
                details.get("displayJobId")
                or position.get("displayJobId")
            ),

            "title": (
                details.get("name")
                or position.get("name", "")
            ),

            "location": locations,

            "standardizedLocations": standardized_locations,

            "description": clean_html(
                details.get("jobDescription", "")
            ),

            "posted_date": format_date(
                details.get("postedTs")
                or position.get("postedTs")
            ),

            # Working hours: Full time or Part time.
            "time_type": ", ".join(
                details.get("efcustomTextTimeType") or []
            ),

            # Employment category has not yet been identified.
            # Employment category: Internship or New College Graduate.
            "job_type": ", ".join(item["job_types"]) or "Not specified",

            "department": (
                details.get("department")
                or position.get("department", "")
            ),

            "url": job_url,

            "apply_url": (
                apply_action.get("applyUrl")
                or job_url
            ),
        })

        # Small pause between details requests.
        time.sleep(0.5)

    print(
        f"\nFetched details for {len(jobs)} candidate positions."
    )

    return jobs
