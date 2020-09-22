import random
from collections import defaultdict
import json
import sys
import os
import argparse
random.seed()

example_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples/")
ex_map_pool = os.path.join(example_dir, "example_map_pool.json")
ex_tournament = os.path.join(example_dir, "example_tournament.json")

parser = argparse.ArgumentParser(description='Create a maplist from a tournament configurationo and map pool.')
parser.add_argument('-t', '--tournament_file', '--tournament_cfg', '--tournament', '--tournament_config', '--tourney', '--tourney_config', 
	default=ex_tournament, help='Generate a maplist using a custom json tournament config file.')

parser.add_argument('-m', '--map_pool_file', '--map_pool', '--map_pool_config', '--mappool_config', 
	default=ex_map_pool, help="Generate a maplist using a custom json map pool config file.")

parser.add_argument('-o', '--output_rounds_file', '--output_rounds',
	default=ex_map_pool, help="Outputs Tourney rounds as a CSV to the specified file. Creates it if it does not exist.")

parsed_args = parser.parse_args()

#
class MapPoolConfig:
	def __init__(self, 
		exclude_map_score_threshold=5.5, 
		preferred_map_score_threshold=7, 
		max_non_preferred_maps_per_round=1,
		distinct_maps_in_consecutive_rounds=True,
		min_games_before_repeat_mode=2,
		decreased_past_mapmode_likelihood=True,
		max_maps_per_mode=10):
		self.exclude_map_score_threshold = exclude_map_score_threshold
		self.preferred_map_score_threshold = preferred_map_score_threshold
		self.max_non_preferred_maps_per_round = max_non_preferred_maps_per_round
		self.distinct_maps_in_consecutive_rounds = distinct_maps_in_consecutive_rounds
		self.min_games_before_repeat_mode = max(min_games_before_repeat_mode, 3)
		self.decreased_past_mapmode_likelihood = decreased_past_mapmode_likelihood
		self.max_maps_per_mode = max_maps_per_mode

	def set_parameter(self, param_name, value):
		if param_name == "exclude_map_score_threshold":
			self.exclude_map_score_threshold = value
		elif param_name == "preferred_map_score_threshold":
			self.preferred_map_score_threshold = value
		elif param_name == "max_non_preferred_maps_per_round":
			self.max_non_preferred_maps_per_round = value
		elif param_name == "distinct_maps_in_consecutive_rounds":
			self.distinct_maps_in_consecutive_rounds = value
		elif param_name == "min_games_before_repeat_mode":
			 self.min_games_before_repeat_mode = value
		elif param_name == "decreased_past_mapmode_likelihood":
			self.decreased_past_mapmode_likelihood = value
		elif param_name == "max_maps_per_mode":
			self.max_maps_per_mode == value


class MapMode:
	def __init__(self, mode_name, map_name, score=10):
		self.mode_name = mode_name
		self.map_name = map_name
		self.score = score

	def get_prob_weight(self, map_quality=5):
		expon = 2.5 + (map_quality - 5.0) / 2.0
		return (self.score / 10.0) ** expon

	def __str__(self):
		return f"{self.mode_name} on {self.map_name}"

	def __repr__(self):
		return f"{self.mode_name} on {self.map_name}"

class RoundContext:
	def __init__(self, past_rounds=[]):
		self.past_rounds = past_rounds
		self.current_round = []

	def append_game(self, new_game):
		self.current_round.append(new_game)
		
	def finalize_round(self):
		self.past_rounds.append(self.current_round)
		self.current_round = []

	def __str__(self):
		return str(self.past_rounds)
	
	def __repr__(self):
		return repr(self.past_rounds)


class MapModePool:
	def __init__(self, mapmode_list, map_pool_config=MapPoolConfig()):
		self.mapmode_list = mapmode_list
		self.map_pool_config = map_pool_config

	def __str__(self):
		return str(self.mapmode_list)

	def __repr__(self):
		return repr(self.mapmode_list)

	def filter_exclude_bad_mapmodes(self):
		return MapModePool([mapmode for mapmode in self.mapmode_list 
			if mapmode.score >= self.map_pool_config.exclude_map_score_threshold],
			self.map_pool_config)

	def filter_include_okay_mapmodes(self):
		return MapModePool([mapmode for mapmode in self.mapmode_list 
			if mapmode.score >= self.map_pool_config.exclude_map_score_threshold 
			and mapmode.score < self.map_pool_config.preferred_map_score_threshold],
			self.map_pool_config)

	def filter_include_good_mapmodes(self):
		return MapModePool([mapmode for mapmode in self.mapmode_list 
			if mapmode.score >= self.map_pool_config.preferred_map_score_threshold],
			self.map_pool_config)

	def filter_exclude_map(self, map_name):
		return MapModePool([mapmode for mapmode in self.mapmode_list 
			if mapmode.map_name != map_name],
			self.map_pool_config)

	def filter_exclude_mode(self, mode_name):
		return MapModePool([mapmode for mapmode in self.mapmode_list 
			if mapmode.mode_name != mode_name],
			self.map_pool_config)

	def filter_include_mode(self, mode_name):
		return MapModePool([mapmode for mapmode in self.mapmode_list 
			if mapmode.mode_name != mode_name],
			self.map_pool_config)

	def filter_limit_maps_per_mode_from_ctx(self, round_ctx):
		mode_to_used_mapmodes = defaultdict(list)
		mode_to_all_mapmodes = defaultdict(list)
		new_mapmode_list = []
		all_rds = round_ctx.past_rounds + [round_ctx.current_round]
		for mapmode in self.mapmode_list:
			mode_to_all_mapmodes[mapmode.mode_name].append(mapmode)
		for rd in all_rds:
			for mapmode in rd:
				if len(mode_to_used_mapmodes[mapmode.mode_name]) < self.map_pool_config.max_maps_per_mode:
					mode_to_used_mapmodes[mapmode.mode_name].append(mapmode)
		for mode in mode_to_all_mapmodes.keys():
			if len(mode_to_used_mapmodes[mode]) >= self.map_pool_config.max_maps_per_mode:
				new_mapmode_list += mode_to_used_mapmodes[mode]
			else:
				new_mapmode_list += mode_to_all_mapmodes[mode]
		
		# print(len(new_mapmode_list))
		return MapModePool(new_mapmode_list,
			self.map_pool_config)
		

	def filter_from_ctx(self, round_ctx):
		update_if_nonempty = lambda old, new: new if len(new.mapmode_list) > 0 else old
		curr_pool = self.filter_exclude_bad_mapmodes()

		ok_map_pool = self.filter_include_okay_mapmodes()
		ok_map_count = 0
		# Can't play map twice in same round
		for mapmode in round_ctx.current_round:
			curr_pool = update_if_nonempty(curr_pool, curr_pool.filter_exclude_map(mapmode.map_name))
			if mapmode in ok_map_pool.mapmode_list:
				ok_map_count += 1

		if ok_map_count >= self.map_pool_config.max_non_preferred_maps_per_round:
			curr_pool = update_if_nonempty(curr_pool, curr_pool.filter_include_good_mapmodes())

		# Can't play same maps as previous round
		if self.map_pool_config.distinct_maps_in_consecutive_rounds:
			if len(round_ctx.past_rounds) > 0:
				for mapmode in round_ctx.past_rounds[-1]:
					curr_pool = update_if_nonempty(curr_pool, curr_pool.filter_exclude_map(mapmode.map_name))

		if self.map_pool_config.min_games_before_repeat_mode > 0:
			for i in range(self.map_pool_config.min_games_before_repeat_mode):
				curr_round = round_ctx.current_round[::-1] if len(round_ctx.current_round) > 0 else []
				last_round = round_ctx.past_rounds[-1][::-1] if len(round_ctx.past_rounds) > 0 else []
				most_recent_modes = curr_round + last_round
				if i < len(most_recent_modes):
					mode_name = most_recent_modes[i].mode_name
					curr_pool = update_if_nonempty(curr_pool, curr_pool.filter_exclude_mode(mode_name))

		curr_pool = update_if_nonempty(curr_pool, curr_pool.filter_limit_maps_per_mode_from_ctx(round_ctx))

		if self.map_pool_config.decreased_past_mapmode_likelihood:
			for i, mapmode in enumerate(curr_pool.mapmode_list):
				for rds_ago, rd in enumerate(round_ctx.past_rounds[::-1]):
					if mapmode in rd and rds_ago < 4:
						new_score = mapmode.score * (1.0 - 1.0 / (1.75 * (rds_ago + 1.0) * (rds_ago + 1.0)))
						curr_pool.mapmode_list[i].score = new_score

		return curr_pool
		
					

	# map quality from 0 to 10. Higher map quality more heavily weights higher scored maps
	def random_choice(self, map_quality=5):
		# print(self.mapmode_list)
		# print([mapmode.get_prob_weight(map_quality) for mapmode in self.mapmode_list])
		chosen_mapmode = random.choices(self.mapmode_list, 
			weights=[mapmode.get_prob_weight(map_quality) for mapmode in self.mapmode_list], 
			k=1)[0]
		return chosen_mapmode


def map_pool_dict_to_mapmode_list(map_pool_dict):
	mapmode_list = []
	modes = map_pool_dict.get("modes") or []
	maps = map_pool_dict.get("maps") or {}
	for mode in modes:
		mapmodes = maps.get(mode) or []
		for mapmode in mapmodes:
			score = mapmode.get("score") or 7
			map_name = mapmode.get("map_name") or "Final Destination"
			mapmode_list.append(MapMode(mode_name=mode, map_name=map_name, score=score))
	return mapmode_list


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
		for i in range(rd.get('num_games') or 3):
			overrides = rd.get('mapmode_overrides')
			override_mapmode = None
			if overrides:
				override_mapmode = next((MapMode(mode_name=override.get('mode'), 
				map_name=override.get('map'))
				for override in overrides if override.get('game_num') == i + 1), None)
			if override_mapmode:
				round_ctx.append_game(override_mapmode)
			else:
				map_quality_str = rd.get('map_quality') or "normal"
				map_quality = 7 if map_quality_str == "high" else 8 if map_quality_str == "very high" else 5
				filtered_pool = mapmode_pool.filter_from_ctx(round_ctx)
				# print(f"Choices {len(filtered_pool.mapmode_list)}")
				# print(filtered_pool)
				chosen_mapmode = filtered_pool.random_choice(map_quality)
				round_ctx.append_game(chosen_mapmode)
		maplist.append(round_ctx.current_round)
		round_ctx.finalize_round()
	return maplist

def main():

	print(f"Using tournament file {parsed_args.tournament_file}")
	print(f"Using map pool file {parsed_args.map_pool_file}")
	with open(parsed_args.map_pool_file) as f:
		mapmode_list = map_pool_dict_to_mapmode_list(json.loads(f.read()))
	with open(parsed_args.tournament_file) as f:
		tournament_dict = json.loads(f.read())

	maplist = create_tournament(mapmode_list, tournament_dict)

	if parsed_args.output_rounds_file:
		with open(parsed_args.output_rounds_file, "w+") as f:
			csv_data = '\n'.join(','.join([str(game) for game in rnd]) for rnd in maplist)
			f.write(csv_data)
	print(maplist)

if __name__ == "__main__":
    main()