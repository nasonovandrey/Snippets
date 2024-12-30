class BacktestGroup:
    """
    Manages a group of backtests, each configured differently.
    Handles concurrent execution and consolidated logging.

    Attributes:
    backtests (Dict[str, Backtest]): Backtest objects dictionary keyed by backtest_id.
    processes (Dict[str, multiprocessing.Process]): Process objects dictionary keyed by backtest_id.
    group_id (str): Unique identifier generated based on configurations and current timestamp.
    list_of_configurations (List[Configuration]): Configurations for each backtest.
    source_model_path (Path): Source path of the model for backtesting.
    logging_directory (Optional[str]): Logging directory. Actual directory for logs will be created inside it with group_id as name.
    """
    def __init__(
        self,
        list_of_configurations: List[Configuration],
        source_model_path: Path,
        logging_directory: Optional[Path],
    ) -> None:
        self.list_of_configurations = list_of_configurations
        self.source_model_path = source_model_path
        self.group_id = f"{hashlib.md5(''.join(config.to_hash() for config in list_of_configurations).encode()).hexdigest()}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.logging_directory = logging_directory.resolve() / self.group_id
        self.logging_directory.mkdir(parents=True)
        self.backtests = {}
        self.processes = {}
        for config in self.list_of_configurations:
            backtest = Backtest(config=config, source_model_path=self.source_model_path)
            backtest_id = backtest.backtest_id
            self.backtests[backtest_id] = backtest
            process = multiprocessing.Process(target=backtest.run, args=(self.logging_directory,))
            self.processes[backtest_id] = process

    async def run(self):
        """
        Starts all backtest processes concurrently.
        """
        for process in self.processes.values():
            process.start()

    def __repr__(self) -> str:
        """
        Returns a string representation of the BacktestGroup with all backtests.

        Returns:
        str: String representation of the BacktestGroup.
        """
        ret = ["BacktestGroup("]
        for backtest in self.backtests.values():
            ret.append(f"{backtest.__repr__()},")
        return "\n".join(ret) + ")"

    def stop_instance(self, backtest_id):
        """
        Terminates and joins a specific backtest process given its ID.

        Args:
        backtest_id (str): The ID of the backtest to terminate.
        """
        self.processes[backtest_id].terminate()
        self.processes[backtest_id].join()
    
    def stop_all(self):
        """
        Terminates and joins all backtest processes.
        """
        for process in self.processes.values():
            process.terminate()
        for process in self.processes.values():
            process.join()

    def get_parsers_dict(self) -> dict:
        """
        Retrieves the log parser objects from each backtest in the group, formatted as a dictionary.

        Returns:
        dict: Dictionary of log parser objects keyed by backtest_id.
        """
        parsers_dict = {backtest_id: backtest.get_parser() for backtest_id, backtest in self.backtests.items()}
        return parsers_dict

    def get_statistics_dict(self) -> dict:
        """
        Retrieves the statistics from each backtest in the group, formatted as a dictionary.

        Returns:
        dict: Dictionary of statistics objects keyed by backtest_id.
        """
        statistics_dict = {backtest_id: backtest.get_statistics() for backtest_id, backtest in self.backtests.items()}
        return statistics_dict

class JobManager:
    def __init__(self, config: NomadConfig):
        self._config = config
        self._alloc_client = api.AllocClient(config)
        self._slack_bot = SlackCommandListener(config.slack_bot_token, config.slack_channel_id)
        self._job_client = api.BacktestJobClient(config, self._alloc_client, self._slack_bot)
        self._node_api = api.NodeApi(config)
        self._optimization_results_api = api.OptimizationResultsApi(config.clickhouse_config)
        # self._all_jobs = []
        # self._thread_pool = ThreadPool(self._config.upload_pool_size)
        # atexit.register(self.shutdown)

        if len(config.servers) > 0:
            self._verify_servers_list()

    def cache_artifact(self, tag, path):
        minio_upload_config = self._config.minio_config
        minio_path = f"cache/{tag}/art.tar.gz"

        self._job_client.add_cached_artifact(tag, minio_path)

        minio_client = minio.MinioClient(minio_upload_config)
        if minio_client.exists(minio_path):
            print(f"Skipping upload artifacts, file already exists, tag = {tag}")
            return

        temp_name = next(tempfile._get_candidate_names())
        temp_name = f"/tmp/{getpass.getuser()}/artifacts/{temp_name}.tar.gz"
        res = utils.make_tarfile_from_filelist(temp_name, [path])

        minio_client.upload(minio_path=minio_path, local_path=Path(temp_name))

        print(f"Successfully uploaded artifacts tag {tag}")

        Path(temp_name).unlink(missing_ok=True)

    def _verify_servers_list(self):
        nodes = self._node_api.get_nodes()
        
        for server in self._config.servers:
            if server not in nodes:
                raise RuntimeError(f"Server {server} unrecognized, verify that server present in cluster")

            status = nodes[server]["Status"]
            if status != "ready":
                raise RuntimeError(f"Server {server} status check failed: server status {status}")

    def get_total_cores(self):
        if len(self._config.servers) == 0:
            raise RuntimeError("Use this method only with server list specified")
        nodes = self._node_api.get_nodes()

        total_cores = 0
        for server in self._config.servers:
            total_cores += int(nodes[server]["Cores"])

        return total_cores

    # def prepare(self, arts_list):
    #     return self._upload_model_artifacts(arts_list)

    def add_jobs_to_poll_thread(self, jobs):
        self._job_client.add_jobs_to_poll_thread(jobs)

    async def _run_poll_loop(self, restart_policy=None):
        await self._job_client._run_poll_loop(restart_policy)

    async def start(self, poll_loop=False, restart_policy=None):
        tasks = []
        # start slack bot first
        tasks.append(self._slack_bot.start(poll_loop=False))

        if poll_loop:
            tasks.append(self._run_poll_loop(restart_policy))

        await asyncio.gather(*tasks)

    def stop(self, job_id):
        return self._job_client.delete_job(job_id)

    def submit_backtests(self, configs, tags_entries, run_uuids):
        jobs = []
        for config, tags, run_uuid in zip(configs, tags_entries, run_uuids):
            job = self.submit_backtest(config, tags, run_uuid)

            jobs.append(job)

        return jobs

    def submit_backtest(self, backtest_config, tags, run_uuid):
        return self._job_client.submit_backtest(backtest_config, tags, run_uuid)

    def get_allocation_id(self, job_id):
        return self._job_client.get_allocation_id(job_id)

    def get_job_status(self, job_id):
        return self._job_client.get_job_status(job_id)

    def is_finished_job(self, job_status):
        return self._job_client.is_finished_job(job_status)

    def is_pending_job(self, job_status):
        return self._job_client.is_pending_job(job_status)

    def is_success_job(self, job_id):
        return self._job_client.is_success_job(job_id)

    def wait_for_job_list_with_restart(self, job_list, restart_policy=None):
        return self._job_client.wait_for_job_list_with_restart(job_list, restart_policy)

    def get_backtest_result(self, run_uuid):
        return self._optimization_results_api.get_backtest_result(run_uuid)

    def get_job_logs(self, job_id, log_type="stderr"):
        return self._job_client.get_job_logs(job_id, log_type)

    def get_running_jobs(self):
        job_ids = self._job_client.get_jobs_by_prefix(self._config.unique_prefix)
        res = {}
        for job_id in job_ids:
            try:
                status = self._job_client.get_job_status(job_id)
                if self._job_client.is_finished_job(status):
                    continue
                # alloc_id = self._job_client.get_allocation_id(job_id)
                # node = self._alloc_client.get_allocation_node(alloc_id)
                res[job_id] = {
                    "status": status
                    # "Node": node,
                }
            except Exception as _:
                print(f"Skipping job {job_id}")
        return res

    def get_job_json(self, job_id):
        job_json = self._job_client.get_job_json(job_id)

        return job_json

    # creates internal job object from job json
    def get_job_object(self, job_id):
        job_json = self.get_job_json(job_id)

        base_job = BaseJob(job_id, job_json)

        run_uuid = job_id.split("/")[-1]

        env = job_json['TaskGroups'][0]['Tasks'][0]['Env']

        # it is ok to create job object without config for most purposes
        backtest_config = None
        if 'CONFIG' in env:
            backtest_config = json.loads(env['CONFIG'])
        else:
            # we need to find config in artifacts
            arts_info = json.loads(env['NOMAD_META_EXTRA_ARTIFACTS'])
            for key, info in arts_info.items():
                if 'stream_backtester_config' not in key:
                    continue

                temp_name = next(tempfile._get_candidate_names())
                temp_name = Path(f"/tmp/{temp_name}")

                p = subprocess.run(f"go-getter \"{info['getter']}\" {temp_name}", shell=True, check=True)

                with open(temp_name / 'config.json', 'r') as f:
                    backtest_config = json.load(f)

                shutil.rmtree(temp_name)

                break

        tags = json.loads(job_json['TaskGroups'][0]['Tasks'][0]['Env']['TAGS'])

        job = BacktestJob(base_job=base_job, arts_uuid=None, run_uuid=run_uuid, backtest_config=backtest_config, tags=tags)

        return job

