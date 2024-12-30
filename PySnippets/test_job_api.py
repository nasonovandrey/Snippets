import json
from requests.exceptions import HTTPError
import requests
import json

from pprint import pprint
from orion_py.nomad.config import NomadConfig

class JobApi:
    def __init__(self, config: NomadConfig):
        self._config = config

        self._headers = {}
        if self._config.nomad_token is not None:
            self._headers["X-Nomad-Token"] = self._config.nomad_token

        self._params = {}
        if self._config.nomad_namespace is not None:
            self._params["namespace"] = self._config.nomad_namespace

    def submit_job(self, job_json):
        last_exception = None

        params = {}
        params.update(self._params)

        for _ in range(self._config.api_retries):
            try:
                response = requests.post(f"{self._config.nomad_server}/v1/jobs",
                                         json=job_json, headers=self._headers, params=params)
                response.raise_for_status()
                return response.json()
            except HTTPError as e:
                pprint(f"Error submitting job, what = {str(e)}")
                last_exception = e
                pprint(json.dumps(job_json, indent=4))
        raise last_exception

with open("nomad.json", "w") as f:
    nomad_config = json.load(f)

with open("example_job.json", "w") as f:
    example_job = json.load(f)

job_api = JobApi(nomad_config)

