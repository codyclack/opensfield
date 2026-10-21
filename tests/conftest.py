import os
import tempfile

# keep test jobs out of the real generation history (outputs/jobs.json)
os.environ.setdefault("OPENSFIELD_JOBS_FILE", os.path.join(tempfile.mkdtemp(prefix="osf_jobs_"), "jobs.json"))
