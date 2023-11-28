import os
import random
import json
from itertools import islice
from typing import List, Dict, Any, Union

def shuffle_competitors(contestants: List[str], max_competitors: int) -> List[str]:
    random.shuffle(contestants)
    return contestants[:max_competitors]

def create_matchup_partners(competitors: List[str]) -> List[List[str]]:
    iter_competitors = iter(competitors)
    return [list(islice(iter_competitors, 2)) for item in range(int(len(competitors) / 2))]

def get_votes(competitor_group: List[List[str]]) -> List[str]:
    winners: List[str] = []
    for i, competitor in enumerate(competitor_group):
        print(f"Matchup {i} is {competitor[0]} vs {competitor[1]}")
        winner = input("Please vote for your favourite: ")        
        
        winners.append(winner)
    
    return winners

def pairs_dump_return_first_pair(competitor_pairs, update_round: int = None) -> Union[List[List[str]], int, int]: # returns a single competitor match up, the round number, and the number of players left in the round
    pairs = {}
    try: # very first run through 
        with open('pairs.json', 'r') as file:
            pairs = json.load(file)
    except FileNotFoundError:
        pass
    current_round = pairs['round'] if not update_round else update_round

    with open('pairs.json', 'w', encoding='utf-8') as file:
        if len(competitor_pairs) > 1:
            pair_info: Dict[str, Any] = {'pairs': competitor_pairs[1:], 'round': current_round}
            json.dump(pair_info, file, ensure_ascii=False, indent=4)
        else:
            json.dump({'pairs': [], 'round': current_round + 1}, file, ensure_ascii=False, indent=4)
    return [competitor_pairs[0]], current_round, len(competitor_pairs) - 1

def create_new_bracket() -> Union[List[List[str]], int, int]:
    # creates new bracket and returns a single match pair
    NUM_COMPETITORS = 64

    with open('Unused.txt', 'r') as file:
        unused = file.read().splitlines()

    competitors: List[str] = shuffle_competitors(unused, NUM_COMPETITORS)
    competitor_pairs: List[List[str]] = create_matchup_partners(competitors)

    # update Unused to remove those that have been used
    # https://www.askpython.com/python/list/difference-between-two-lists-unique-entries
    new_unused: List[str] = list(set(unused) - set(competitors))
    with open('Unused.txt', 'w') as file:
        for line in new_unused:
            file.write(f'{line}\n')

    return pairs_dump_return_first_pair(competitor_pairs, update_round=1)

def get_new_competitor_pair(winner: str) -> Union[List[List[str]], int, int]:
    # check if file exists to add / create file to add winner to
    if 'winner.json' in os.listdir('.'):
        with open('winners.json', 'r') as file:
            winners = json.load(file)
        winners['winners'].append(winner)
        # add winner to json file
        with open('winners.json', 'w', encoding='utf-8') as file:
            json.dump(winners, file, ensure_ascii=False, indent=4)
    else:
        with open('winners.json', 'w', encoding='utf-8') as file:
            json.dump({'winners': [winner]}, file, ensure_ascii=False, indent=4)

    # check for pairs.json and whether there is any content left inside
    if 'pairs.json' not in os.listdir('.'):
        print('file deleted unable to proceed')

    with open('pairs.json', 'r') as file:
        data = json.load(file)
    if not data['pairs']: # no pairs left
        with open('winners.json', 'r') as file:
            winners = json.load(file)
        os.remove('winners.json')
        return pairs_dump_return_first_pair(create_matchup_partners(winners['winners']))
    else: # there are pairs left -- grab pair and update list
        return pairs_dump_return_first_pair(data['pairs'])

def main():
    competitors: List[str] = create_new_bracket()

    match_round: int = 1
    matchups: List[List[str]] = []

    while len(competitors[0]) > 1:
        print(f"Now onto round {match_round}!!!!")

        winner = get_votes(competitors)
        competitors = get_new_competitor_pair(winner)

        match_round += 1

    print(f"We have a winner, {competitors[0][0]} congrats!!!")


if __name__ == '__main__':
    main()
