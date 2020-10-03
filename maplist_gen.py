import random
from collections import defaultdict
import json
import sys
import os
import argparse
from mapmode_pool import MapMode, MapModePool, MapPoolConfig, RoundContext, \
	to_mapmode_list, get_map_pool_by_mode, read_map_pool_from_file, read_tournament_from_file

"""Generates a Maplist based on a scored map pool.
   
   author: bjackson8bit
"""

random.seed()


def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue

def check_quality_score(value):
    ivalue = int(value)
    if ivalue <= 0 or ivalue >= 10:
        raise argparse.ArgumentTypeError("%s is an invalid map quality int value" % value)
    return ivalue


example_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples/")
ex_map_pool = os.path.join(example_dir, "example_map_pool.json")
ex_tournament = os.path.join(example_dir, "example_tournament.json")

parser = argparse.ArgumentParser(description='Create a continuous map list from a map pool.')

parser.add_argument('-m', '--map_pool_file', '--map_pool', '--map_pool_config', '--mappool_config', 
	default=ex_map_pool, help="Generate a maplist using a custom json map pool config file.")

parser.add_argument('-g', '--num_games', '--games' , type=check_positive,
	default=7, help="Number of games to be generated.")

parser.add_argument('-q', '--map_quality', '--quality', type=check_quality_score,
	default=5, help="Map quality, a number between 0 - 10. Higher number means higher scored maps appear more often. Default 5.")

parser.add_argument('-o', '--output_file', '--output',
	default=None, help="Outputs maplist as a JSON to the specified file. Creates it if it does not exist.")

parsed_args = parser.parse_args()


def create_continuous_maplist(mapmode_list, num_games, map_quality=5):
	distinct_modes = len(get_map_pool_by_mode(mapmode_list).keys())
	map_pool_config = MapPoolConfig(exclude_map_score_threshold=5.5, 
		preferred_map_score_threshold=7, 
		max_non_preferred_maps_per_round=10,
		distinct_maps_in_consecutive_rounds=True,
		min_games_before_repeat_mode=distinct_modes - 1,
		decreased_past_mapmode_likelihood=True,
		max_maps_per_mode=10)
	round_ctx = RoundContext()
	mapmode_pool = MapModePool(mapmode_list, map_pool_config)
	for i in range(num_games):
		filtered_pool = mapmode_pool.filter_from_ctx(round_ctx)
		chosen_mapmode = filtered_pool.random_choice(map_quality)
		round_ctx.append_game(chosen_mapmode)
	round_final = round_ctx.current_round

	return [str(mapmode) for mapmode in round_final]


def main():

	print(f"Using map pool file {parsed_args.map_pool_file}")

	mapmode_list = read_map_pool_from_file(parsed_args.map_pool_file)

	maplist = create_continuous_maplist(mapmode_list, parsed_args.num_games, parsed_args.map_quality)
	maplist_str = '\n'.join(maplist)
	if parsed_args.output_file:
		print(parsed_args.output_file)
		with open(parsed_args.output_file, "w+") as f:
			f.write(maplist_str)
	print(maplist_str)

if __name__ == "__main__":
    main()