import os
import json
import shutil
import argparse
import datetime
from dataclasses import dataclass, asdict
from dacite import from_dict
@dataclass
class Asset:
    m_FileID: int
    m_PathID: int

@dataclass
class OneLiner:
    characterProgressTokens: list[Asset]
    worldProgressTokens: list[Asset]
    priority: int
    text: list[Asset]

@dataclass
class DialogueCycle:
    relationshipRequirement: int
    text: Asset
    oneLiners: list[OneLiner]

@dataclass
class NPCDialogueCyclesWithText:
    npc_name: str
    married_cycles: list[str]
    dating_cycles: list[str]
    general_cycles: list[str] # note these are used for dating too if you finish the dating cycles
    one_liners: list[list[str]] # one liners have requirements that I'm not extracting yet, but the progress tokens + priority should tell you when they get used


@dataclass
class NPCDialogueCycles:
    npc_name: str
    married_cycles: list[DialogueCycle]
    dating_cycles: list[DialogueCycle]
    general_cycles: list[DialogueCycle] # note these are used for dating too if you finish the dating cycles
    one_liners: list[OneLiner] # one liners have requirements that I'm not extracting yet, but the progress tokens + priority should tell you when they get used
    
    def process_assets(self, assets: dict[int, str]) -> NPCDialogueCyclesWithText:
        married_cycles_text = []
        for cycle in self.married_cycles:
            text = assets.get(cycle.text.m_PathID, "")
            married_cycles_text.append(text)
        date_cycles_text = []
        for cycle in self.dating_cycles:
            text = assets.get(cycle.text.m_PathID, "")
            date_cycles_text.append(text)
        general_cycles_text = []
        for cycle in self.general_cycles:
            text = assets.get(cycle.text.m_PathID, "")
            general_cycles_text.append(text)
        oneliner_text = []
        for liner in self.one_liners:
            lines = []
            for t in liner.text:
                text = assets.get(t.m_PathID, "")
                lines.append(text)
            oneliner_text.append(lines)
        return NPCDialogueCyclesWithText(
            npc_name=self.npc_name,
            married_cycles=married_cycles_text,
            dating_cycles=date_cycles_text,
            general_cycles=general_cycles_text,
            one_liners=oneliner_text
        )

def generate(extracted_folder : str, destination_folder : str, npc: str):
    npc_cycles: dict[str, NPCDialogueCycles] = {}
    npc_text: dict[str, dict[int, str]] = {}
    npc = npc.lower()
    for file in os.listdir(extracted_folder):
        file_path = os.path.join(extracted_folder, file)

        if npc != "" and not file.startswith(npc):
            continue
        if file.endswith(".json"):
            npcai = {}
            with open(file_path, "r") as f:
                npcai = json.load(f)
            npc_name = npcai["_npcName"].lower()
            dialogue_cycles = [from_dict(DialogueCycle, x) for x in npcai["_dialogueCycles"]]
            dating_cycles =[from_dict(DialogueCycle, x) for x in npcai["_datingCycles"]]
            married_cycles = [from_dict(DialogueCycle, x) for x in npcai["_marriedCycles"]]
            one_liners = [from_dict(OneLiner, x) for x in npcai["_oneLiners"]]
            data = NPCDialogueCycles(
                npc_name=npc_name,
                married_cycles=married_cycles,
                dating_cycles=dating_cycles,
                general_cycles=dialogue_cycles,
                one_liners=one_liners
            )
            npc_cycles[npc_name] = data
        elif file.endswith(".txt"):
            parts = file.split("_")
            npc_name = parts[0]
            path_id = int(parts[1])
            with open(file_path, "rt", encoding="utf-8") as f:
                contents = f.read()
                if npc_name not in npc_text:
                    npc_text[npc_name] = {}
                npc_text[npc_name][path_id] = contents
    
    for (npc_name, data) in npc_cycles.items():
        # find the text files
        print(f"Processing {npc_name}")
        assets = npc_text.get(npc_name, None)
        if assets is None:
            continue
        x = data.process_assets(assets=assets)
        file_path = os.path.join(destination_folder, f"{npc_name}_cycles.json")
        with open(file_path, "w") as f:
            f.write(json.dumps(asdict(x)))


# generate jsons for each npc for passing to the ai
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
    generate(extracted_folder=args.input, destination_folder=folder, npc=args.npc)