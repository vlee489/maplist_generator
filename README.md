# README

## Map Pool File

Map pools are specified in json files like the following example. Each mapmode should be scored from 0-10 by how frequent the user wants it to appear. A higher score represents more frequent use.

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

## Tournament Config File

When generating a tournament, a minimum score can be specified to filter maps from the map pool without removing those maps from this configuration file.

### Configurations

- rounds
  - Required: **Y**
  - A list of rounds, each represented by a json struct.
  - **round** config
    - map_quality
      - Required: **N**
      - Default: **normal**
      - Possible values: "normal", "high", "very high"
      - Higher map quality causes higher scored maps to be weighted more and picked more frequently.
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
    - counterpicks
      - Required: **N**
      - Default: **false**
      - When *true*, the first map of the round will be randomly generated and the rest of the games in the round will be output as *"Counterpick"*
      -
- exclude_map_score_threshold
  - Required: **N**
  - Default: **6**
  - Maps with scores less than *this* will not be included in the tournament map pool.
- max_non_preferred_maps_per_round
  - Optional: **Y**
  - Default: **1**
  - Maps with high scores will be considered 'preferred'. Other maps (with lower scores) can only appear *this* many times in a single round.
- preferred_map_score_threshold
  - Optional: **Y**
  - Default: **7**
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

```json
{
    "exclude_map_score_threshold": 5,
    "max_non_preferred_maps_per_round": 1,
    "preferred_map_score_threshold": 7,
    "distinct_maps_in_consecutive_rounds": true,
    "min_games_before_repeat_mode": 2,
    "decreased_past_mapmode_likelihood": true,
    "max_maps_per_mode": 10,
    "rounds": [
        {
            "game_overrides": [
                {
                    "map": "MakoMart",
                    "mode": "Splat Zones",
                    "game_num": 1
                }
            ],
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
    ]
}
```

./maplist_gen.py

./tournament_gen.py
