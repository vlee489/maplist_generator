import random
from collections import defaultdict
import json
import sys
import os
import argparse
from mapmode_pool import MapMode, MapModePool, MapPoolConfig, RoundContext, \
	to_mapmode_list, get_map_pool_by_mode, read_map_pool_from_file, read_tournament_from_file
random.seed()

example_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples/")
ex_map_pool = os.path.join(example_dir, "example_map_pool.json")
ex_tournament = os.path.join(example_dir, "example_tournament.json")

parser = argparse.ArgumentParser(description='Create a maplist from a tournament configuration and map pool.')
parser.add_argument('-t', '--tournament_file', '--tournament_cfg', '--tournament', '--tournament_config', '--tourney', '--tourney_config', 
	default=ex_tournament, help='Generate a maplist using a custom json tournament config file.')

parser.add_argument('-m', '--map_pool_file', '--map_pool', '--map_pool_config', '--mappool_config', 
	default=ex_map_pool, help="Generate a maplist using a custom json map pool config file.")

parser.add_argument('-o', '--output_file', '--output' '--output_rounds',
	default=ex_map_pool, help="Outputs Tourney rounds and used map pool as a JSON to the specified file. Creates it if it does not exist.")

parsed_args = parser.parse_args()


def create_tournament(mapmode_list, tournament_dict):
	round_ctx = RoundContext()
	maplist = []
	rounds = []
	map_pool_config = MapPoolConfig()
	for k, v in tournament_dict.items():
		if k == "rounds":
			rounds = v
		else:
			map_pool_config.set_parameter(k, v)
	mapmode_pool = MapModePool(mapmode_list, map_pool_config)
	for rd in rounds:
		if rd.get("ignore_game_history"):
			round_ctx = RoundContext()
		num_games = 1 if rd.get('counterpicks') else rd.get('num_games') or 3

		for i in range(num_games):
			overrides = rd.get('game_overrides')
			limited_mapmode_pool = None
			map_quality_str = rd.get('map_quality') or "normal"
			map_quality = 7 if map_quality_str == "high" else 8 if map_quality_str == "very high" else 5
			if overrides:
				override = next((o for o in overrides if o.get('game_num') == i + 1), None)
				if override:
					limited_mapmode_pool = mapmode_pool.filter_include_mode(override.get('mode')) \
						if override.get('mode') else mapmode_pool
					limited_mapmode_pool = limited_mapmode_pool.filter_include_map(override.get('map')) \
						if override.get('map') else limited_mapmode_pool
			if limited_mapmode_pool:
				# print(f"Choices {len(filtered_pool.mapmode_list)}")
				# print(filtered_pool)
				chosen_mapmode = limited_mapmode_pool.random_choice(map_quality)
				round_ctx.append_game(chosen_mapmode)
			else:
				filtered_pool = mapmode_pool.filter_from_ctx(round_ctx)
				chosen_mapmode = filtered_pool.random_choice(map_quality)
				round_ctx.append_game(chosen_mapmode)
		round_final = round_ctx.current_round
		if rd.get('counterpicks'):
			round_final = round_final + ["Counterpick"] * ((rd.get('num_games') or 3) - 1)
		maplist.append(round_final)
		round_ctx.finalize_round()
	

	used_map_pool = get_map_pool_by_mode(mapmode_pool.filter_exclude_bad_mapmodes().mapmode_list)
	output_dict = {
		'map_pool': used_map_pool,
		'rounds': [
		{
			'round': i + 1,
			'num_games': len(mm_list),
			'stages': [str(mm) for mm in mm_list]
		}
		for i,mm_list in enumerate(maplist)]
	}
	
	return output_dict


def main():

	print(f"Using tournament file {parsed_args.tournament_file}")
	print(f"Using map pool file {parsed_args.map_pool_file}")

	mapmode_list = read_map_pool_from_file(parsed_args.map_pool_file)
	tournament_dict = read_tournament_from_file(parsed_args.tournament_file)

	output_json_dict = create_tournament(mapmode_list, tournament_dict)
	output_json_str = json.dumps(output_json_dict, indent=4)
	if parsed_args.output_file:
		print(parsed_args.output_file)
		with open(parsed_args.output_file, "w+") as f:
			f.write(output_json_str)
	print(output_json_str)

if __name__ == "__main__":
    main()