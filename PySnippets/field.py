class Hyperparameter:
    def __init__(self, path: List[str], get_values: Optional[Callable]):
        self.path = path
        if get_values:
            self.get_values = get_values


class Configuration:
    def set_by_path(self, path, value):
        pass
    def substitute(self, hyperparameter: List[Hyperparameter], values: Optional[List[Any]]=None):
        if not values:
            values = hyperparameter.get_values()
        configurations = [copy.deepcopy(self) for _ in range(len(values))] 
        for index, value in enumerate(values):
            configurations[index].set_by_path(hyperparameter.path, value)
        return configurations

class GenerateNewValues1:
    def __init__(self, runner):
        self.runner = runner
    def __call__(self):
        # some logic to process metrics on runner
class GenerateNewValues2:
    def __init__(self, runner):
        self.runner = runner
    def __call__(self):
        # some logic to process metrics on runner

# example usage
runner = BacktestRunner()
configuration = Configuration()
get_values1 = GenerateNewValues1(runner)
get_values1 = GenerateNewValues2(runner)
hyperparameter1 = Hyperparameter(path=["A", "B", "concept"], get_values=get_values)
hyperparameter2 = Hyperparameter(path=["A", "B", "concept2"], get_values=get_values)
for hyperparameter in hyperparameters:
    while True:
        configurations = configuration.substitute(hyperparameter)
        runner.run(configurations)
        if stop_condition:
            configuration = select_best(runner)

