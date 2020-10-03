import random
from collections import defaultdict
import json
import sys
import os
import argparse
from mapmode_pool import MapMode, MapModePool, MapPoolConfig, RoundContext, \
	to_mapmode_list, get_map_pool_by_mode, read_map_pool_from_file, read_tournament_from_file
import math 

"""Generates a Tournament Maplist based on a tournament configuration and a map pool.
   
   author: bjackson8bit
"""

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
	default=None, help="Outputs Tourney rounds and used map pool as a JSON to the specified file. Creates it if it does not exist.")

parsed_args = parser.parse_args()


def round_to_dict(rd_name, mapmode_list):
	return {
		'round_name': rd_name,
		'num_games': len(mapmode_list),
		'stages': [str(mm) for mm in mapmode_list]
	}


def generate_round(rd, mapmode_pool, round_ctx):
	if rd.get("ignore_game_history"):
		round_ctx = RoundContext()
	num_games = 1 if rd.get('counterpicks') else (rd.get('num_games') or 3)

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
			limited_mapmode_pool = limited_mapmode_pool.filter_from_ctx(round_ctx)
			chosen_mapmode = limited_mapmode_pool.random_choice(map_quality)
			round_ctx.append_game(chosen_mapmode)
		else:
			filtered_pool = mapmode_pool.filter_from_ctx(round_ctx)
			chosen_mapmode = filtered_pool.random_choice(map_quality)
			round_ctx.append_game(chosen_mapmode)
	round_final = round_ctx.current_round
	if rd.get('counterpicks'):
		round_final = round_final + ["Counterpick"] * ((rd.get('num_games') or 3) - 1)
	round_ctx.finalize_round()
	return round_final

def create_rounds_tournament(mapmode_list, tournament_dict):
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
		maplist.append(generate_round(rd, mapmode_pool, round_ctx))

	used_map_pool = get_map_pool_by_mode(mapmode_pool.filter_exclude_bad_mapmodes().mapmode_list)
	output_dict = {
		'tournament_type': 'rounds',
		'map_pool': used_map_pool,
		'rounds': [round_to_dict(f"Round {i + 1}", mm_list) 
		for i,mm_list in enumerate(maplist)]
	}
	
	return output_dict


# excludes grands
def get_number_winners_rounds(num_players):
	return math.ceil(math.log(num_players, 2))


# excludes grands
def get_number_losers_rounds(num_players):
	return (get_number_winners_rounds(num_players) - 1) * 2 - 1


def get_round_name(rd_num, num_rounds):
	if rd_num == num_rounds - 3:
		return "Quarterfinals"
	elif rd_num == num_rounds - 2:
		return "Semifinals"
	elif rd_num == num_rounds - 1:
		return "Finals"
	else:
		return f"Round {rd_num+1}"


def create_single_elim_tournament(mapmode_list, tournament_dict):
	num_players = 16
	round_ctx = RoundContext()
	round_cfg = {}
	map_pool_config = MapPoolConfig()
	for k, v in tournament_dict.items():
		if k == 'round_config':
			round_cfg = v
		elif k == 'num_players':
			num_players = v
		else:
			map_pool_config.set_parameter(k, v)
	mapmode_pool = MapModePool(mapmode_list, map_pool_config)

	output_rounds = []

	# Generate rounds
	num_winners_rounds = get_number_winners_rounds(num_players)
	for i in range(num_winners_rounds):
		if i == num_winners_rounds - 3 and 'quarterfinals' in round_cfg:
			rd = round_cfg.get('quarterfinals')
		elif i == num_winners_rounds - 2 and 'semifinals' in round_cfg:
			rd = round_cfg.get('semifinals')
		elif i == num_winners_rounds - 1 and 'finals' in round_cfg:
			rd = round_cfg.get('finals')
		else:
			rd = round_cfg.get('default')
		output_rounds.append(round_to_dict(get_round_name(i, num_winners_rounds), \
			generate_round(rd, mapmode_pool, round_ctx)))

	used_map_pool = get_map_pool_by_mode(mapmode_pool.filter_exclude_bad_mapmodes().mapmode_list)
	
	output_dict = {
		'tournament_type': 'single_elim',
		'num_players': num_players,
		'map_pool': used_map_pool,
		'rounds': output_rounds
	}
	
	return output_dict


def create_double_elim_tournament(mapmode_list, tournament_dict):
	num_players = 16
	round_ctx = RoundContext()
	winners_rounds = []
	losers_rounds = []
	round_cfg = {}
	map_pool_config = MapPoolConfig()
	for k, v in tournament_dict.items():
		if k == 'round_config':
			round_cfg = v
		elif k == 'num_players':
			num_players = v
		else:
			map_pool_config.set_parameter(k, v)
	mapmode_pool = MapModePool(mapmode_list, map_pool_config)

	# Generate wr1
	winners_rounds.append(generate_round(round_cfg.get('default'), mapmode_pool, round_ctx))
	
	round_ctx_copy = round_ctx.clone()

	# Generate losers rounds
	num_losers_rounds = get_number_losers_rounds(num_players)
	for rd_num in range(num_losers_rounds):
		if rd_num == num_losers_rounds - 2 and 'l_semifinals' in round_cfg:
			rd = round_cfg.get('l_semifinals')
		elif rd_num == num_losers_rounds - 1 and 'l_finals' in round_cfg:
			rd = round_cfg.get('l_finals')
		else:
			rd = round_cfg.get('default')
		losers_rounds.append(generate_round(rd, mapmode_pool, round_ctx))

	# Generate winners rounds
	num_winners_rounds = get_number_winners_rounds(num_players)
	# If 'share_rounds_w_l' setting is on, winners sets are copies of some losers rounds.
	if round_cfg.get('share_rounds_w_l'):
		for rd_num in range(1, num_winners_rounds):
			if rd_num == 1:
				winners_rounds.append(losers_rounds[0])
			else:
				winners_rounds.append(losers_rounds[2*(rd_num - 1) - 1])
	# If off, generate rounds as normal
	else:
		for rd_num in range(1, num_winners_rounds):
			if rd_num == num_winners_rounds - 3 and 'w_quarterfinals' in round_cfg:
				rd = round_cfg.get('w_quarterfinals')
			elif rd_num == num_winners_rounds - 2 and 'w_semifinals' in round_cfg:
				rd = round_cfg.get('w_semifinals')
			elif rd_num == num_winners_rounds - 1 and 'w_finals' in round_cfg:
				rd = round_cfg.get('w_finals')
			else:
				rd = round_cfg.get('default')
			winners_rounds.append(generate_round(rd, mapmode_pool, round_ctx_copy))
	
	gf_rd = generate_round(round_cfg.get('grand_finals') if 'grand_finals' in round_cfg 
														else round_cfg.get('default'), mapmode_pool, round_ctx_copy)
	gf_reset_rd = generate_round(round_cfg.get('grand_finals_reset') if 'grand_finals_reset' in round_cfg 
														else round_cfg.get('default'), mapmode_pool, round_ctx_copy)

	used_map_pool = get_map_pool_by_mode(mapmode_pool.filter_exclude_bad_mapmodes().mapmode_list)
	
	output_rounds = []
	for i in range(num_winners_rounds):
		output_rounds.append(round_to_dict(f"Winners {get_round_name(i, num_winners_rounds)}", winners_rounds[i]))

	for i in range(num_losers_rounds):
		output_rounds.append(round_to_dict(f"Losers {get_round_name(i, num_losers_rounds)}", losers_rounds[i]))

	output_rounds.append(round_to_dict("Grand Finals", gf_rd))
	output_rounds.append(round_to_dict("Grand Finals Set 2 (If needed)", gf_reset_rd))

	output_dict = {
		'tournament_type': 'double_elim',
		'num_players': num_players,
		'map_pool': used_map_pool,
		'rounds': output_rounds
	}
	
	return output_dict


def create_tournament(mapmode_list, tournament_dict):
	if 'tournament_type' not in tournament_dict:
		raise RuntimeError('Key tournament_type not present in input file')
	elif 'tournament_config' not in tournament_dict:
		raise RuntimeError('Key tournament_config not present in input file')

	tournament_cfg = tournament_dict.get('tournament_config')
	tournament_type = tournament_dict.get('tournament_type')
	
	if tournament_type == 'rounds':
		return create_rounds_tournament(mapmode_list, tournament_cfg)
	elif tournament_type in ['double elim', 'double_elim', 'double elimination', 'double_elimination']:
		return create_double_elim_tournament(mapmode_list, tournament_cfg)
	elif tournament_type in ['bracket', 'single elim', 'single_elim', 'single elimination', 'single_elimination']:
		return create_single_elim_tournament(mapmode_list, tournament_cfg)

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