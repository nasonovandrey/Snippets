
class Field:
    def __init__(self, field: str):
        pass
    def initial_values(self) -> List[Any]:
        pass

@dataclass
class HyperparameterSet:
    fields: List[Field]
    finished: bool

def Optimizer:
    def __init__(self, hyperparameter_sets: List[Set[Field]], configuration: Configuration):
        self.hyperparameter_sets = [
                HyperparameterSet(fields=hyperset, finished=False, best_values=None)
                for hyperset in hyperparameter_sets)]
        self.configuration = configuration
        self.runner = BacktestRunner()
    
    def optimize(self):
        for iteration in len(self.hyperparameter_sets):
            for hyperset in self.hyperparameter_sets:
                if not hyperset.finished: # Only non-finished values are generated
                    for field in hyperset.fields:
                        values_to_substitute[field] = field.initial_values()
            configurations = substitute(values_to_substitute, self.configuration)
            for configuration in configurations:
                self.backtests.append(self.runner.create(configuration))
            while True:
                for run_id in self.backtests:
                    if runner.get_status(run_id) == "created":
                        runner.run(run_id)
                    results = self.collect_results(self.running_backtests)
                    next_hyperparameters = self.generate_next_hyperparameters(results)
                    if self.stop_condition:
                        self.configuration = self.select_best(self.backtests) # Update configuration with the best configuration
                        self.hyperparameter_sets[iteration].finished = True
                        break

    @abstractmethod
    def generate_next_hyperparameters():
        pass
    @abstractmethod
    def select_best():
        pass
    @abstractmethod
    def collect_results():
        pass
    @abstractmethod
    def stop_condition():
        pass


                        

