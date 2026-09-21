import json
from pathlib import Path

from app.schemas.jobs import SampleJob


class DuplicateSampleJobError(ValueError):
    pass


def load_sample_jobs(directory: Path) -> list[SampleJob]:
    jobs: list[SampleJob] = []
    seen: set[tuple[str, str]] = set()
    for path in sorted(directory.glob("job_*.json")):
        job = SampleJob.model_validate(json.loads(path.read_text(encoding="utf-8")))
        identity = (job.source, job.source_job_id)
        if identity in seen:
            raise DuplicateSampleJobError(f"Duplicate sample job: {identity}")
        seen.add(identity)
        jobs.append(job)
    return jobs
