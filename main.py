import requests
from threading import Thread
from dataclasses import dataclass
from time import perf_counter, sleep
from typing import Any, Callable, List


def get_function_time(function: Callable, 
                      args: tuple = None,
                      kwargs: dict = None) -> dict:
    t_start = perf_counter()

    if not args:
        args = ()
    if not kwargs:
        kwargs = {}
    
    f_return = function(*args, **kwargs)

    t_stop = perf_counter()
    r = {'time': t_stop - t_start, 'value': f_return}
    return r


def store_value(function: Callable, 
                var: list,
                args: tuple = None,
                kwargs: dict = None,
                return_append: Any = None):
    if not args:
        args = ()
    if not kwargs:
        kwargs = {}

    f_return = function(*args, **kwargs)
    
    if return_append:
        var.append((f_return, return_append,))
        return f_return

    var.append(f_return)
    return f_return


def run_list() -> None:
    x = [i for i in range(1000000)]


@dataclass
class ThreadCompetitor:
    id: int
    name: str
    username: str
    thread: Thread = None
    time: float = 0.0

    @staticmethod
    def order_by_time(var: list) -> list:
        return sorted(var, key=lambda x: x.time)

    def new_thread(self, var_to_store: list) -> None:
        self.thread = Thread(target=store_value,
                             kwargs={
                                 'function': get_function_time,
                                 'var': var_to_store,
                                 'kwargs': {'function': run_list},
                                 'return_append': self
                             })


def execute_race(competitors: List[ThreadCompetitor]) -> List[dict]:
    final_results = []

    while True:
        threads_results = []
        
        for comp in competitors:
            comp.new_thread(threads_results)

        for comp in competitors:
            comp.thread.start()

        for comp in competitors:
            comp.thread.join()

        for result, thread_object in threads_results:
            thread_object.time = result.get('time')

        ordered_comp = ThreadCompetitor.order_by_time(competitors)

        time_counts = [x.time for x in competitors]
        time_min = min(time_counts)
        time_min_count = time_counts.count(time_min)

        race_results = {
            'status': 'win',
            'positions': ordered_comp.copy()
        }

        if time_min_count > 1:
            race_results.update({'status': 'draw'})
            competitors = ordered_comp[:time_min_count]
        
        del ordered_comp
        final_results.append(race_results)

        if race_results.get('status') == 'win':
            break
    
    return final_results.copy()


def print_header(title: str):
    length = 40
    print('{:=^{}}'.format(f' {title} ', length))


def main():
    N_COMPETITORS = 6
    START_BALANCE = 20.0
    MINIMUM_BET = 2.0
    BET_MULTIPLIER = 2.0
    balance = START_BALANCE

    competitors = []

    for i in range(N_COMPETITORS):
        response = requests.get('https://api.namefake.com/').json()
        name = response.get('name')
        username = response.get('username')

        new_comp = ThreadCompetitor(id=i,
                                    name=name,
                                    username=username)
        competitors.append(new_comp)

    name_max = max([len(x.name) for x in competitors])
    username_max = max([len(x.username) for x in competitors])

    while True:
        print()
        print_header('COMPETITORS')
        for comp in competitors:
            print('{:<3} {:<{}}  @{:<{}}'.format(comp.id, 
                                                 comp.name, 
                                                 name_max, 
                                                 comp.username,
                                                 username_max))

        print()
        sleep(1)
        print_header('STATUS')
        print(f'Balance: {balance:.2f}\n')

        while True:
            bet_amount = float(
                input(f'Bet amount (minimum = {MINIMUM_BET:.2f}): ')
            )

            if (bet_amount > balance
                    or bet_amount < MINIMUM_BET):
                print('\nBet amount is not valid\n')
                continue
            break
            
        while True:
            chosen_comp = int(input('Winner ID: '))

            if chosen_comp not in range(len(competitors)):
                print('\nID is not valid\n')
                continue

            chosen_comp = competitors[chosen_comp]
            break
        
        sleep(1)
        print()
        print_header('RACING')
        results = execute_race(competitors)

        for result in results:
            for i, competitor in enumerate(result.get('positions')):
                sleep(0.3)
                f_variables = [
                    i,
                    competitor.id,
                    competitor.name,
                    name_max,
                    competitor.username,
                    username_max,
                    competitor.time
                ]
                print('{:<2} » {:<3} {:<{}} @{:<{}} » {}'.format(*f_variables),
                      flush=True)

            sleep(0.8)

            if result.get('status') == 'draw':
                print('\nThere was a draw...\n', flush=True)
                continue
            
            winner = result.get('positions')[0]
            print(f'\nThe winner is {winner.name} @{winner.username}!',
                  flush=True)

        sleep(1)
        print()
        print_header('RESULTS')

        if winner == chosen_comp:
            balance += bet_amount*BET_MULTIPLIER
            print(f'You\'ve earned {bet_amount*BET_MULTIPLIER}')

        else:
            balance -= bet_amount
            print(f'You\'ve lost {bet_amount}')

        if balance < MINIMUM_BET:
            break
        
        print()
        sleep(1)
        print_header('STATUS')
        print(f'Balance: {balance:.2f}\n')

        play_again = input('\nPlay again? (Y/n): ')

        if play_again.lower() in 'no':
            break
    
    sleep(1)
    print()
    print_header('GAME END')
    print(f'You finished the game with {balance:.2f}')


if __name__ == '__main__':
    main()
