import multiprocessing
import random
import time


class Philosopher(multiprocessing.Process):
    def __init__(self, name, left_fork, right_fork):
        super().__init__()
        self.name = name
        self.left_fork = left_fork
        self.right_fork = right_fork

    def run(self):
        while True:
            self.think()
            self.eat()

    def think(self):
        print(f"{self.name} is thinking.")
        time.sleep(random.uniform(1, 3))

    def eat(self):
        print(f"{self.name} is trying to eat.")
        self.left_fork.acquire()
        self.right_fork.acquire()
        print(f"{self.name} is eating.")
        time.sleep(random.uniform(1, 3))
        self.right_fork.release()
        self.left_fork.release()

    def dining(self):
        print(f"{self.name} is eating.")
        time.sleep(random.uniform(1, 3))

def monitor_philosophers(philosophers):
    while True:
        for philosopher in philosophers:
            if philosopher.state == Philosopher.HUNGRY:
                philosopher.increment_hunger()
                if philosopher.is_starving():
                    philosopher.state = Philosopher.DEAD
                    print(f"{philosopher.name} died from hunger.")
        time.sleep(1)


if __name__ == "__main__":
    num_philosophers = 5
    dining_time = 2  # Time spent eating
    max_hunger = 5  # Maximum hunger counter before dying
    forks = [Fork() for _ in range(num_philosophers)]
    philosophers = [
        Philosopher(f"Philosopher {i}", forks[i], forks[(i + 1) % num_philosophers], dining_time, max_hunger)
        for i in range(num_philosophers)
    ]

    monitor_thread = threading.Thread(target=monitor_philosophers, args=(philosophers,))
    monitor_thread.start()

    for philosopher in philosophers:
        philosopher.start()

    for philosopher in philosophers:
        philosopher.join()

    monitor_thread.join()
