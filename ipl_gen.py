import json
import sys
import csv
"""Coverts tournament data output by tournament_gen.py to
   IPL Readable JSON format
   
   author: vlee489 
"""


def generate_json(maps: dict, file_name: str):
    final_output = []
    for rounds in maps:
        cur_round = {
            "name": rounds["round_name"],
            "maps": []
            }
        for stages in rounds["stages"]:
            stage_split = stages.split(" on ")
            cur_round["maps"].append({
                "map": stage_split[1],
                "mode": stage_split[0]
            })
        final_output.append(cur_round)
    
    with open(file_name, "w+") as f:
        json.dump(final_output, f, indent=4)


def generate_discord(maps: dict, file_name: str):
    final_output = ""
    for rounds in maps:
        round_output = f"```\n{rounds['round_name']}\n```\n"
        for stages in rounds["stages"]:
            round_output = round_output + f"{stages}\n"
        final_output = f"{final_output}\n{round_output}"

    with open(file_name, "w+") as f:
        f.write(final_output)


if len(sys.argv) == 2:
    with open(sys.argv[1], encoding="utf-8") as input_file:
        data = json.load(input_file)
        basename = (sys.argv[1]).split('.')[0]
        print("Generating IPL Overlay JSON file")
        generate_json(data["rounds"], f"{basename}_IPL.json")
        print("Generating Discord Message")
        generate_discord(data["rounds"], f"{basename}_discord.md")
else:
    print('You have entered too many or too few arguments.')
    print('You must run this program as follows:')
    print('python ipl_gen.py <input_file.json>\n')
    print('If the JSON is not from tournament_gen.py, the program may exit unexpectedly.')
