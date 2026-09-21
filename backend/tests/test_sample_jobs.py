from pathlib import Path

from app.services.sample_jobs import load_sample_jobs


def test_sample_jobs_are_valid_unique_and_explicitly_synthetic():
    directory = Path(__file__).resolve().parents[2] / "sample_jobs"
    jobs = load_sample_jobs(directory)

    assert len(jobs) == 3
    assert len({job.source_job_id for job in jobs}) == 3
    assert all(job.source == "sample" for job in jobs)
    assert all(job.raw_data["intentionally_synthetic"] is True for job in jobs)


def test_sample_clients_distinguish_fact_inference_and_unknown():
    directory = Path(__file__).resolve().parents[2] / "sample_jobs"
    jobs = load_sample_jobs(directory)
    fact_types = {fact.type.value for job in jobs for fact in job.client.facts}

    assert fact_types == {"FACT", "INFERENCE", "UNKNOWN"}
