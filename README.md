# README

## Requirements

This code runs using Python 3. Please install the latest version (or any version >= 3.6) to run this application.

https://www.python.org/downloads/

If you receive syntax errors when you run this program, you may have to use **python3** in the command name instead of **python** to specify the version of python.

## Usage

This code can be referenced as a library elsewhere, or it can be run on the command line manually to create output.

## Create a Tournament

```bash
python tournament_gen.py [-h] [-t TOURNAMENT_FILE] [-m MAP_POOL_FILE] [-o OUTPUT_FILE]
```

Use ```python tournament_gen.py -h``` for help with the command.

If TOURNAMENT_FILE or MAP_POOL_FILE are not provided, they will default to *./example/example_tournament.json* and *./example/example_map_pool.json* respectively

Try cd-ing to the project root directory (same level as the code) and running the following commands. This will create a tournament using the Saturday Morning Coffee maplist. Check out the output file to see what a generated tourney looks like!

```bash
python tournament_gen.py -t ./examples/example_tournament.json -m ./smc/smc_map_pool.json -o rounds_tourney_output.json
python tournament_gen.py -t ./examples/single_elim_tournament.json -m ./smc/smc_map_pool.json -o single_elim_tourney_output.json
python tournament_gen.py -t ./examples/double_elim_tournament.json -m ./smc/smc_map_pool.json -o double_elim_tourney_output.json
```

## Create a Scrimmage (List of Mapmodes, no Rounds)

```bash
python maplist_gen.py [-h] [-m MAP_POOL_FILE] [-g NUM_GAMES] [-q MAP_QUALITY] [-o OUTPUT_FILE]
```

Use ```python maplist_gen.py -h``` for help with the command.

If MAP_POOL_FILE is not provided, it will default to *./example/example_map_pool.json

Try cd-ing to the project root directory and running the following command. This will create a list of map-mode combinations perfect for scrims or single round events.

```bash
python maplist_gen.py -g 15 -m ./smc/smc_map_pool.json -o test_scrim.txt
```

## Map Pool Config File

Map pools are specified in json files like the following example. Each mapmode should be scored from 0-10 by how frequent the user wants it to appear. A higher score represents more frequent use.

**Note:** The method for getting probability of picking the map isn't directly proportional to the score. In other words,a map with score 10 won't show up twice as much as one with score 5, but something closer to 4x as often.

For best use of the scoring system, please rate maps that you'd be fine seeing in tourney at least a 5 or 6 and maps that are highly popular scores of 8 or more. Maps with lower scores will appear significantly less frequently.

- **Examples**
  - [Saturday Morning Coffee Map Pool Config](https://github.com/bjackson8bit/maplist_generator/blob/master/smc/smc_map_pool.json)
  - [Example Config (All mapmodes)](https://github.com/bjackson8bit/maplist_generator/blob/master/examples/example_map_pool.json)

The tournament configuration has a score cutoff threshold if you'd like to exclude all maps in a map pool below a certain score. Details can be found in the **Tournament Config File** section.

```json
{
    "modes": [
        "Splat Zones",
        "Tower Control",
        "Rainmaker"
    ],
    "maps": {
        "Splat Zones": [
            {
                "map_name": "Ancho-V Games",
                "score": 8
            },
            {
                "map_name": "Blackbelly Skatepark",
                "score": 6.5
            }
        ],
        "Tower Control": [
            {
                "map_name": "Ancho-V Games",
                "score": 9
            },
            {
                "map_name": "Moray Towers",
                "score": 1
            }
        ],
        "Rainmaker": [
            {
                "map_name": "Blackbelly Skatepark",
                "score": 9
            },
            {
                "map_name": "Humpback Pump Track",
                "score": 9
            }
        ]
    }
}
```

If you're interested, the formula for the weight assigned to a map based on its score is here.

```python
# From MapMode in mapmode_pool.py
# Pretty arbitrary formula but the exponent is to exaggerate the
# difference in scores.
# Higher map quality raises the exponent, shrinking lower scores much more than higher ones.
def get_prob_weight(self, map_quality=5):
    expon = 2.5 + (map_quality - 5.0) / 2.0
    return (self.score / 10.0) ** expon
```

## Tournament Config File

When generating a tournament, a minimum score can be specified to filter maps from the map pool without removing those maps from this configuration file.

## Configurations

- tournament_type
  - Required: **Y**
  - The tournament type. Current options: **rounds**, **single_elim**, **double_elim**

### *rounds* tournament

- tournament_config
  - Ex. [Basic Rounds Tournament](https://github.com/bjackson8bit/maplist_generator/blob/master/examples/basic_tournament.json)
  - rounds
    - Required: If using **rounds** tournament type.
    - A list of rounds, each represented by a json struct. See configuration below.

### *single_elim* tournament

- tournament_config
  - Ex. [Single Elimination Tournament](https://github.com/bjackson8bit/maplist_generator/blob/master/examples/single_elim_tournament.json)
  - num_players
    - Required: **Y**
    - The number of players entered in the tournament.
  - round_config
    - default
      - Required: **Y**
      - The round config used for all sets in the tournament, unless overridden with the below options.
    - quarterfinals
      - Required: **N**
      - The round config for Quarterfinals. Uses the **default** round config if not present.
    - semifinals
      - Required: **N**
      - The round config for Semifinals. Uses the **default** round config if not present.
    - finals
      - Required: **N**
      - The round config for Finals. Uses the **default** round config if not present.

### *double_elim* tournament

- tournament_config
  - Ex. [Double Elimination Tournament](https://github.com/bjackson8bit/maplist_generator/blob/master/examples/double_elim_tournament.json)
  - num_players
    - Required: **Y**
    - The number of players entered in the double elimination tournament.

  - round_config
    - share_rounds_w_l
      - Required: **N**
      - Default: **true**
      - If **true**, some rounds and their maps will be reused between losers and winners. No entrant in the bracket will encounter both duplicate sets.
      - Teams dropping into losers will have just played the same set as their next opponent in losers.
      - Ex. [Double Elimination Tournament (Shared Rounds)](https://github.com/bjackson8bit/maplist_generator/blob/master/examples/double_elim_share_maps_tournament.json)
    - default
      - Required: **Y**
      - The round config used for all sets in the tournament, unless overridden with the below options.
    - w_quarterfinals
      - Required: **N**
      - The round config for Winners Quarterfinals. Uses the **default** round config if not present.
    - w_semifinals
      - Required: **N**
      - The round config for Winners Semifinals. Uses the **default** round config if not present.
    - w_finals
      - Required: **N**
      - The round config for Winners Finals. Uses the **default** round config if not present.
    - l_semifinals
      - Required: **N**
      - The round config for Losers Semifinals. Uses the **default** round config if not present.
    - l_finals
      - Required: **N**
      - The round config for Losers Finals. Uses the **default** round config if not present.
    - grand_finals
      - Required: **N**
      - The round config for Grand Finals. Uses the **default** round config if not present.
    - grand_finals_reset
      - Required: **N**
      - The round config for Grand Finals Set 2. Uses the **default** round config if not present.

### **round** config

- num_games
  - The number of games in the round.
  - Ex. [basic_tournament.json](https://github.com/bjackson8bit/maplist_generator/blob/master/examples/basic_tournament.json)
- map_quality
  - Required: **N**
  - Default: **normal**
  - Possible values: "normal", "high", "very high"
  - Higher map quality causes higher scored maps to be weighted more and picked more frequently.
  - Ex. [high_map_quality_tournament.json](https://github.com/bjackson8bit/maplist_generator/blob/master/examples/high_map_quality_tournament.json)
- game_overrides
  - Required: **N**
  - A list of game overrides, each represented by a json struct. This will force the specified game to use the map/mode listed.
  - **override** config
    - game_num
      - Required: **Y**
      - The game number to override. Starts at 1.
    - mode
      - Required: **Y**
      - The desired mode to use in the override.
    - map
      - Required: **N**
      - The desired map to use in the override.
      - If this field is absent, it will randomly select a map from the pool of the given mode.
  - Ex. [override_tournament.json](https://github.com/bjackson8bit/maplist_generator/blob/master/examples/override_tournament.json)
- counterpicks
  - Required: **N**
  - Default: **false**
  - When *true*, the first map of the round will be randomly generated and the rest of the games in the round will be output as *"Counterpick"*
  - Ex. [counterpick_tournament.json](https://github.com/bjackson8bit/maplist_generator/blob/master/examples/counterpick_tournament.json)

### Map Generation Configurations

Map generation configs go directly under the **tournament_config** attribute.

- exclude_map_score_threshold
  - Required: **N**
  - Default: **6**
  - Maps with scores less than *this* will not be included in the tournament map pool.
- max_non_preferred_maps_per_round
  - Optional: **Y**
  - Default: **2**
  - Maps with high scores will be considered 'preferred'. Other maps (with lower scores) can only appear *this* many times in a single round.
- preferred_map_score_threshold
  - Optional: **Y**
  - Default: **8**
  - Maps with score equal to *this* or larger will be considered preferred.
- distinct_maps_in_consecutive_rounds
  - Optional: **Y**
  - Default: **true**
  - If enabled, maps (regardless of mode) will not be reused in consecutive rounds. Maps will not be repeated in the same round regardless of this configuration.
- min_games_before_repeat_mode
  - Optional: **Y**
  - Default: **2**
  - The number of games before allowing a repeat mode.
  - Ex. Game 1 is Splat Zones, and *this* = 2. Games 2 and 3 cannot be Splat Zones.
- decreased_past_mapmode_likelihood
  - Optional: **Y**
  - Default: **true**
  - If enabled, mapmodes already used in the tournament will have a lower chance of appearing again later.
- max_maps_per_mode
  - Optional: **Y**
  - Default: **10**
  - If enabled, uses up to *this* many maps from each mode in the tournament. 
  - Ex. 11 Splat Zones maps are in the map pool. Only up to 10 distinct maps will be used for this tournament (chosen randomly).

### Example Tournament

This config will create a tournament with three Bo3 rounds, a Bo5 round with high quality maps, and then a counterpick Bo5 round with game 1 being a very high quality random Splat Zones map.

The default generation configurations are included at the bottom for convenience.

```json
{
    "rounds": [
        {
            "num_games": 3
        },
        {
            "num_games": 3
        },
        {
            "num_games": 3
        },
        {
            "map_quality": "high",
            "num_games": 5
        },
        {
            "counterpicks": true,
            "game_overrides": [
                {
                    "mode": "Splat Zones",
                    "game_num": 1
                }
            ],
            "map_quality": "very high",
            "num_games": 5
        }
    ],
    "exclude_map_score_threshold": 5,
    "max_non_preferred_maps_per_round": 2,
    "preferred_map_score_threshold": 7,
    "distinct_maps_in_consecutive_rounds": true,
    "min_games_before_repeat_mode": 2,
    "decreased_past_mapmode_likelihood": true,
    "max_maps_per_mode": 10
}
```

### CSV/Discord Message Output

To output the .csv files required for the EGtv Graphics Package, along with a Discord message, follow these instructions.

1) Follow the instructions above to output a .json from the maplist generator.
2) Make and save any desired changes to the .json file.
3) Run the following command:
```python csv_gen.py <name of .json file>```
4) 2 .csv files and 1 .txt file will be generated and saved to /output.
