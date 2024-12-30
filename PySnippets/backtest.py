class BacktestGroup:
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
            backtest = Backtest(
                config=config,
                source_model_path=self.source_model_path,
                logging_directory=self.logging_directory,
            )
            backtest_id = backtest.backtest_id
            self.backtests[backtest_id] = backtest
            process = multiprocessing.Process(target=backtest.run)
            self.processes[backtest_id] = process

    def start(self) -> None:
        for process in self.processes.values():
            process.start()

    def wait(self) -> None:
        for process in self.processes.values():
            process.join()

    def run(self) -> None:
        self.start()
        self.wait()

    def wait_on_id(self, backtest_id: str) -> None:
        self.processes[backtest_id].join()

    def __repr__(self) -> str:
        ret = ["BacktestGroup("]
        for backtest_id, backtest in self.backtests.items():
            process = self.processes[backtest_id]
            process_status = "Alive" if process.is_alive() else "Terminated"
            ret.append(
                f"{backtest.__repr__()} - Process Status: {get_process_status(process)},"
            )
        return "\n".join(ret) + ")"

    def stop_instance(self, backtest_id: str) -> None:
        self.processes[backtest_id].terminate()
        self.processes[backtest_id].join()

    def get_process_status(self, backtest_id: str) -> str:
        return get_process_status(self.processes.get(backtest_id))

    def stop_all(self) -> None:
        for process in self.processes.values():
            process.terminate()
        for process in self.processes.values():
            process.join()

    @property
    def parsers(self) -> dict:
        parsers_dict = {
            backtest_id: backtest.parser
            for backtest_id, backtest in self.backtests.items()
        }
        return parsers_dict

    @property
    def statistics(self) -> dict:
        statistics_dict = {
            backtest_id: backtest.statistics
            for backtest_id, backtest in self.backtests.items()
        }
        return statistics_dict

