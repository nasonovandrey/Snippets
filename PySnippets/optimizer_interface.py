class Optimizer:
    def __init__(self, hyperparameters: List[Field], configuration: Configuration):
        self.hyperparameters = hyperparameters
        self.configuration = configuration
        self.runner = BacktestRunner()

    @abstractmethod
    def generate_initial_hyperparameters(self):
        """
        Generate initial set of hyperparameters.
        A better solution might be to add an initial value or a 
        strategy to generate it into a Field class.
        """
        pass

    @abstractmethod
    def collect_results(self):
        """
        Monitors backtests until they are ready (perhaps we
        consider them ready when only a portion of the started
        backtests are finished). Holds the execution until then.
        Applies metric extraction to backtest results and parsers.
        Should be decomposed into two function, but the 
        exact decomposition will be clear later.
        Also, here we should identify performance metric with the
        corresponding backtest.
        """
        pass

    @abstractmethod
    def generate_next_hyperparameters(self, results):
        pass

    @abstractmethod
    def stop_condition(self):
        pass

    def optimize(self):
        init_hyperparameters = self.generate_initial_hyperparameters()
        configurations = substitute(self.configuration, init_hyperparameters)
        self.running_backtests = list()
        for configuration in configurations:
            self.backtests.append(self.runner.create(configuration))
        while not self.stop_condition():
            for run_id in self.running_backtests:
                if runner.get_status(run_id) == "created":
                    runner.run(run_id)
            runner.run(self.running_backtests)
            results = self.collect_results(self.running_backtests)
            next_hyperparameters = generate_next_hyperparameters(results)
            configurations = substitute(self.configuration, next_hyperparameters)
            for configuration in configurations:
                self.backtests.append(self.runner.create(configuration))


        




