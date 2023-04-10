import openai
import argparse
import os
import shutil
import datetime
import json

def generate_dialogue(formatted_dialogue_folder : str, destination_folder : str, npc: str):
    npc = npc.lower()
    
    for file in os.listdir(formatted_dialogue_folder):
        if npc != "" and not file.startswith(npc):
            continue
        file_path = os.path.join(formatted_dialogue_folder, file)
		
        content = None
        with open(file_path, "r") as f:
            content = json.load(f)
        if content is None:
            print(f"Could not read {file_path}")
            continue
        print(f"Prompt for {file}")
        response = openai.ChatCompletion.create(
			model="gpt-3.5-turbo",
			messages=[
					{"role": "system", "content": "You are a helpful assistant."},
				]
		)
        print(response)
        result = response['choices'][0]['message']['content']
        result_path = os.path.join(destination_folder, file)
        with open(result_path, "w") as f:
            f.write(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    date_time = datetime.datetime.now().strftime("%m%d%Y-%H%M%S")
    parser.add_argument("-o", "--output", type=str, default=f"generate-{date_time}", help="Output directory. If this folder already exists, it will be deleted!")
    parser.add_argument("-i", "--input", type=str, help="Extracted folder with all dialogue and npcai json")
    parser.add_argument("-n", "--npc", type=str, default="", help="If provided, only extract for the given npc. Else extract all npcs.")

    args = parser.parse_args()
    
    folder = args.output
    if os.path.exists(folder):
        print(f"Folder {folder} already exists, deleting...")
        shutil.rmtree(folder)
    os.mkdir(folder)
    generate_dialogue(formatted_dialogue_folder=args.input, destination_folder=folder, npc=args.npc)