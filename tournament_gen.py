import random
from collections import defaultdict
import json
import sys
import os
import argparse
from mapmode_pool import MapMode, MapModePool, MapPoolConfig, RoundContext, \
	to_mapmode_list, get_map_pool_by_mode, read_map_pool_from_file, read_tournament_from_file
import math 

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
			# print(f"Choices {len(filtered_pool.mapmode_list)}")
			# print(filtered_pool)
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
		'map_pool': used_map_pool,
		'rounds': [
		{
			'round_name': f"Round {i + 1}",
			'num_games': len(mm_list),
			'stages': [str(mm) for mm in mm_list]
		}
		for i,mm_list in enumerate(maplist)]
	}
	
	return output_dict


# excludes grands
def get_number_winners_rounds(num_players):
	return math.ceil(math.log(num_players, 2))


# excludes grands
def get_number_losers_rounds(num_players):
	return (get_number_winners_rounds(num_players) - 1) * 2


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
	print(round_cfg)

	round_ctx_copy = round_ctx.clone()
	# Generate wr1
	winners_rounds.append(generate_round(round_cfg.get('default'), mapmode_pool, round_ctx))

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
	num_winners_rounds = get_number_winners_rounds(num_players)
	if round_cfg.get('share_rounds_w_l'):
		for i in range(num_winners_rounds - 1):
			winners_rounds.append(losers_rounds[2*(i + 1) - 2])
	else:
		for i in range(num_winners_rounds - 1):
			if i + 1 == num_winners_rounds - 3 and 'w_quarterfinals' in round_cfg:
				rd = round_cfg.get('w_quarterfinals')
			elif i + 1 == num_winners_rounds - 2 and 'w_semifinals' in round_cfg:
				rd = round_cfg.get('w_semifinals')
			elif i + 1 == num_winners_rounds - 1 and 'w_finals' in round_cfg:
				rd = round_cfg.get('w_finals')
			else:
				rd = round_cfg.get('default')
			winners_rounds.append(generate_round(rd, mapmode_pool, round_ctx_copy))
	gf_rd = round_cfg.get('grand_finals') if 'grand_finals' in round_cfg else round_cfg.get('default')
	winners_rounds.append(generate_round(gf_rd, mapmode_pool, round_ctx_copy))
	print(losers_rounds)
	print(winners_rounds)
	used_map_pool = get_map_pool_by_mode(mapmode_pool.filter_exclude_bad_mapmodes().mapmode_list)
	
	output_rounds = []
	for i in range(num_winners_rounds + 1):
		if i == num_winners_rounds - 3:
			rd_name = "Winners Quarterfinals"
		elif i == num_winners_rounds - 2:
			rd_name = "Winners Semifinals"
		elif i == num_winners_rounds - 1:
			rd_name = "Winners Finals"
		elif i == num_winners_rounds:
			rd_name = "Grand Finals"
		else:
			rd_name = f"Winners Round {i+1}"
		output_rounds.append(
			{
				'round_name': rd_name,
				'num_games': len(winners_rounds[i]),
				'stages': [str(mm) for mm in winners_rounds[i]]
			})
	for i in range(num_losers_rounds):
		if i == num_losers_rounds - 2:
			rd_name = "Losers Semifinals"
		elif i == num_losers_rounds - 1:
			rd_name = "Losers Finals"
		else:
			rd_name = f"Losers Round {i+1}"
		output_rounds.append(
			{
				'round_name': rd_name,
				'num_games': len(losers_rounds[i]),
				'stages': [str(mm) for mm in losers_rounds[i]]
			})
	
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
	cfg = tournament_dict.get('tournament_config')
	if tournament_dict.get('tournament_type') == 'rounds':
		return create_rounds_tournament(mapmode_list, cfg)
	elif tournament_dict.get('tournament_type') in ['double elim', 'double_elim', 'double elimination', 'double_elimination']:
		return create_double_elim_tournament(mapmode_list, cfg)

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