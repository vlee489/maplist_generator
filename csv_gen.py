import json
import sys
import csv
"""Coverts tournament data output by tournament_gen.py to
   EGTV Readable CSV Format
   
   author: NintenZone
"""

if len(sys.argv) == 2:
    print("Creating files...")
    print("Created discord_" + sys.argv[1].replace(".json", "") + ".txt")
    print("Created rounds.csv")
    print("Created mappool.csv")
    print("")

    with open(sys.argv[1]) as jsonInput:
        data = json.load(jsonInput)

    max_pool_maps = 0

    for keys in data["map_pool"].keys():
        if len(data["map_pool"][keys]) > max_pool_maps:
            max_pool_maps = len(data["map_pool"][keys])

    pool_header = ["Mode", "Count"]

    for i in range(1,max_pool_maps+1):
        pool_header.append("map" + str(i))

    with open("./output/mappool.csv", "w", newline="") as mappoolCSV:
        poolWriter = csv.writer(mappoolCSV, delimiter=",",
                               quotechar='"', quoting=csv.QUOTE_MINIMAL)
        poolWriter.writerow(pool_header)
        for keys in data["map_pool"].keys():
            next_row = [keys, len(data["map_pool"][keys])]
            for map in data["map_pool"][keys]:
                next_row.append(map)
            poolWriter.writerow(next_row)
        poolWriter.writerow(["Counterpick", "1", "Counterpick"])
        poolWriter.writerow(["Random", "1", "Random"])
    print("Completed mappool.csv")

    rounds_header =["nameFull", "nameShort", "isCounterpickable", "bestOf", "styleOfPlay"]

    max_round_maps = 0

    for rounds in data["rounds"]:
        if rounds["num_games"] > max_round_maps:
            max_round_maps = rounds["num_games"]

    for i in range(1, max_round_maps+1):
        rounds_header.append("mode" + str(i))
        rounds_header.append("mapName" + str(i))

    with open("./output/rounds.csv", "w", newline="") as roundsCSV:
        roundsWriter = csv.writer(roundsCSV, delimiter=",",
                                  quotechar='"', quoting=csv.QUOTE_MINIMAL)
        roundsWriter.writerow(rounds_header)
        for rounds in data["rounds"]:
            next_row = [rounds["round_name"], rounds["round_name"], 0, rounds["num_games"]]
            for stages in rounds["stages"]:
                map_mode = stages.split(" on ")
                next_row.append(map_mode[0])
                next_row.append(map_mode[1])
            roundsWriter.writerow(next_row)

    print("Completed rounds.csv")

    discord_txt = open("./output/discord_" + sys.argv[1].replace(".json", "") + ".txt", "w+")

    new_message = "=====BEGIN NEW MESSAGE====="

    discord_lines = ["__**MAP POOL**__", ""]
    for modes in data["map_pool"].keys():
        discord_lines.append("**" + modes + "**")
        for maps in data["map_pool"][keys]:
            discord_lines.append(maps)
        discord_lines.append("")
    discord_lines.append(new_message)

    for rounds in data["rounds"]:
        discord_lines.append("**" + rounds["round_name"] + "**")
        for maps in rounds["stages"]:
            discord_lines.append(maps)
        discord_lines.append("")

    length = 0

    for lines in discord_lines:
        if (length + len(lines)) > 2000:
            length = 0
            discord_txt.write("\n" + new_message + "\n")
        discord_txt.write(lines + "\n")
        length += len(lines)
    discord_txt.close()

    print("Completed discord_" + sys.argv[1].replace(".json", "") + ".txt")
    print("")
    print("Saved all files to the output directory successfully. The program will now exit.")

else:
    print('You have entered too many or too few arguments.')
    print('You must run this program as follows:')
    print('python csv_gen.py <input_file.json>')
    print('')
    print('If the JSON is not from tournament_gen.py, the program may exit unexpectedly.')
