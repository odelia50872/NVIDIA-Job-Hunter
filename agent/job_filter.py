
import re
from typing import Any


# Only these locations are allowed.
ALLOWED_CITIES = (
    "tel aviv",
    "tel aviv-yafo",
    "tel-aviv",
    "raanana",
    "ra'anana",
    "jerusalem",
)


# Explicitly exclude experienced or management positions.
SENIOR_EXCLUSION_TERMS = (
    "senior",
    "staff",
    "principal",
    "director",
    "manager",
    "vice president",
    "architect",
    "lead engineer",
    "technical lead",
)


# Phrases indicating that no previous experience is required.
NO_EXPERIENCE_TERMS = (
    "no prior work experience required",
    "no previous experience required",
    "no experience required",
    "without prior experience",
)


# Phrases indicating an early-career position.
EARLY_CAREER_TERMS = (
    "intern",
    "internship",
    "student",
    "new college grad",
    "new graduate",
    "recent graduate",
    "entry level",
    "entry-level",
    "junior",
    "early career",
    "early-career",
    "0-3 years",
    "0–3 years",
    "1-2 years",
    "1–2 years",
    "up to 2 years",
    "up to 3 years",
)


# Technical areas relevant to a Computer Science graduate.
RELEVANT_TECH_TERMS = (
    "software",
    "computer science",
    "software development",
    "software engineer",
    "software developer",
    "backend",
    "back-end",
    "frontend",
    "front-end",
    "full stack",
    "full-stack",
    "web development",
    "javascript",
    "typescript",
    "react",
    "python",
    "java",
    "c++",
    "sql",
    "database",
    "data analyst",
    "data analysis",
    "data science",
    "data engineering",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "computer vision",
    "natural language processing",
    "nlp",
    "algorithm",
    "algorithms",
    "cyber security",
    "cybersecurity",
    "information security",
    "operating systems",
    "distributed systems",
    "embedded software",
    "firmware",
)


def has_term(text: str, term: str) -> bool:
    """Match a whole word or phrase, allowing a plural 's' suffix."""
    pattern = rf"(?<!\w){re.escape(term)}s?(?!\w)"
    return re.search(pattern, text) is not None


def has_any_term(text: str, terms: tuple[str, ...]) -> bool:
    return any(has_term(text, term) for term in terms)


def normalize_location(location: str) -> str:
    """Normalize location text for reliable comparisons."""
    return (
        location.lower()
        .replace("’", "'")
        .replace("'", "")
        .strip()
    )


def get_job_locations(job: dict[str, Any]) -> list[str]:
    """Get all available location fields from a job."""
    locations = []

    for field in ("standardizedLocations", "location", "locations"):
        value = job.get(field)

        if isinstance(value, str):
            locations.append(value)

        elif isinstance(value, list):
            locations.extend(str(item) for item in value)

    return locations


def has_allowed_location(job: dict[str, Any]) -> bool:
    """Return True only if the job has an approved Israeli location."""

    for location in get_job_locations(job):
        normalized = normalize_location(location)

        is_israel = (
            "israel" in normalized
            or normalized.endswith(", il")
        )

        if not is_israel:
            continue

        if any(city in normalized for city in ALLOWED_CITIES):
            return True

    return False


def is_senior_position(job: dict[str, Any]) -> bool:
    """Check whether the job title indicates a senior position."""

    title = str(
        job.get("title") or job.get("name") or ""
    ).lower()

    return has_any_term(title, SENIOR_EXCLUSION_TERMS)


def is_candidate_for_details(position: dict[str, Any]) -> bool:
    """
    Preliminary filter:
    Only retrieve full details for jobs in approved cities
    that are not explicitly senior positions.
    """

    if not has_allowed_location(position):
        return False

    if is_senior_position(position):
        return False

    return True


def get_experience_level(job: dict[str, Any]) -> str:
    """
    Classify a job according to its experience requirements.

    Returns:
        high: No previous experience required.
        medium: Early-career position.
        low: No clear early-career indication.
    """

    title = str(job.get("title", "")).lower()
    description = str(job.get("description", "")).lower()

    combined = f"{title} {description}"

    if has_any_term(combined, NO_EXPERIENCE_TERMS):
        return "high"

    if has_any_term(combined, EARLY_CAREER_TERMS):
        return "medium"

    return "low"


def has_compatible_degree(job):
    """
    Check whether the required degree is compatible
    with a Computer Science graduate.
    """

    description = job.get("description", "").lower()

    # Focus on the mandatory requirements section.
    marker = "what we need to see:"
    if marker not in description:
        return True

    requirements = description.split(marker, 1)[1]

    # Exclude optional qualifications and advantages.
    optional_marker = "ways to stand out from the crowd:"
    requirements = requirements.split(optional_marker, 1)[0]

    degree_indicators = (
        "b.sc",
        "bsc",
        "bachelor",
        "b.eng",
        "beng",
        "degree in",
    )

    degree_fields = (
        "electrical engineering",
        "computer engineering",
        "computer science",
        "software engineering",
    )

    # If no degree requirement is specified, do not reject the job.
    if not any(term in requirements for term in degree_indicators):
        return True

    # If the job specifies a degree field, check whether CS is accepted.
    mentioned_fields = [
        field for field in degree_fields
        if field in requirements
    ]

    if not mentioned_fields:
        return True

    return (
        "computer science" in mentioned_fields
        or "software engineering" in mentioned_fields
    )




def is_relevant(job):
    title = job.get("title", "")
    description = job.get("description", "")

    # Check location.
    if not has_allowed_location(job):
        return False

    # Exclude senior positions.
    if is_senior_position(job):
        return False

    # Check experience level.
    if get_experience_level(job) == "low":
        return False

    # Check degree requirements.
    if not has_compatible_degree(job):
        return False

    # Check technical relevance.
    text = f"{title} {description}".lower()

    return has_any_term(text, RELEVANT_TECH_TERMS)


def calculate_relevance_score(job):
    """
    Calculate how well a job matches a Computer Science graduate.

    Higher score means a stronger match.
    """

    score = 0

    title = str(job.get("title", "")).lower()
    description = str(job.get("description", "")).lower()
    job_type = str(job.get("job_type", "")).lower()

    # 1. Early-career job category.
    if "intern" in job_type:
        score += 25
    elif "new college graduate" in job_type:
        score += 25

    # 2. Experience requirements.
    experience = get_experience_level(job)

    if experience == "high":
        score += 20
    elif experience == "medium":
        score += 15

    # 3. Degree compatibility.
    if has_compatible_degree(job):
        score += 20

    # 4. Relevant technologies and skills.
    relevant_skills = (
        "python",
        "java",
        "c++",
        "javascript",
        "typescript",
        "react",
        "sql",
        "machine learning",
        "artificial intelligence",
        "computer vision",
        "data science",
        "data analyst",
        "algorithms",
        "software development",
        "backend",
        "linux",
    )

    for skill in relevant_skills:
        if has_term(title, skill):
            score += 5
        elif has_term(description, skill):
            score += 2

    # 5. Prefer software and data-related job titles.
    preferred_titles = (
        "software engineer",
        "software developer",
        "data analyst",
        "data scientist",
        "machine learning",
        "computer vision",
        "python developer",
        "backend developer",
    )

    if any(term in title for term in preferred_titles):
        score += 15

    return score


def get_score_breakdown(job):
    """
    Explain how the job relevance score was calculated.
    """

    breakdown = []

    title = str(job.get("title", "")).lower()
    description = str(job.get("description", "")).lower()
    job_type = str(job.get("job_type", "")).lower()

    # 1. Early-career job category.
    if "intern" in job_type or "new college graduate" in job_type:
        breakdown.append(("Early-career job category", 25))

    # 2. Experience requirements.
    experience = get_experience_level(job)

    if experience == "high":
        breakdown.append(("No previous experience required", 20))
    elif experience == "medium":
        breakdown.append(("Early-career experience requirements", 15))

    # 3. Degree compatibility.
    if has_compatible_degree(job):
        breakdown.append(("Compatible Computer Science degree", 20))

    # 4. Relevant technologies and skills.
    relevant_skills = (
        "python",
        "java",
        "c++",
        "javascript",
        "typescript",
        "react",
        "sql",
        "machine learning",
        "artificial intelligence",
        "computer vision",
        "data science",
        "data analyst",
        "algorithms",
        "software development",
        "backend",
        "linux",
    )

    for skill in relevant_skills:
        if has_term(title, skill):
            breakdown.append((f"Skill: {skill}", 5))
        elif has_term(description, skill):
            breakdown.append((f"Skill: {skill}", 2))

    # 5. Preferred job titles.
    preferred_titles = (
        "software engineer",
        "software developer",
        "data analyst",
        "data scientist",
        "machine learning",
        "computer vision",
        "python developer",
        "backend developer",
    )

    if any(term in title for term in preferred_titles):
        breakdown.append(("Preferred technical job title", 15))

    return breakdown

