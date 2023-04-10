import os
import UnityPy
import json
import shutil
import argparse
import datetime

def unpack_all_assets(source_folder : str, destination_folder : str, npc: str):
    # iterate over all files in source folder
    typetree = {}
    npc = npc.lower()

    # typetrees extracted using https://github.com/K0lb3/UnityPy/blob/master/examples/MonoBehaviourFromAssembly/monobehaviour_from_assembly.py
    with open("sunhaven_core_typetrees.json", "r") as f:
        typetree = json.loads(f.read())
    assert "NPCAI" in typetree

    for root, dirs, files in os.walk(source_folder):
        for file_name in files:
            if not file_name.endswith("assets") or file_name == "resources.assets":
                continue
            # generate file_path
            file_path = os.path.join(root, file_name)
            # load that file via UnityPy.load
            env = UnityPy.load(file_path)
            # alternative way which keeps the original path
            for obj in env.objects:
                if obj.type.name not in ["MonoBehaviour", "TextAsset"]:
                    continue
                data = obj.read()
                if data is None:
                    continue

                if obj.type.name == "TextAsset":
                    n = data.name.lower()
                    if "one liner" in n or "cycle" in n: 
                        parts = n.split()
                        npc_name = parts[0].lower()
                        if npc_name.endswith("'s"):
                            npc_name = npc_name[:-2]
                        print(f"Found dialogue file for {npc_name}")
                        if npc == "" or npc == npc_name:
                            text_asset_name = data.m_Name or "unknown"
                            if obj.file_id:
                                filename = f"{npc_name}_{obj.file_id}_{obj.path_id}_{text_asset_name}.txt"
                            else:
                                filename = f"{npc_name}_{obj.path_id}_{text_asset_name}.txt"

                            print(f"Saving dialogue file {filename}")
                            with open(os.path.join(destination_folder, filename), "wb") as f:
                                f.write(bytes(data.script))
                elif obj.type.name == "MonoBehaviour":
                    if not data.m_Script:
                        continue
                    script = data.m_Script.read()
                    if "NPCAI" != script.m_ClassName:
                        continue
                    nodes = typetree[script.m_ClassName]
                    tree = obj.read_typetree(nodes)
                    npc_name = tree.get("_npcName", "").lower()
                    print(f"Found NPCAI file for {npc_name}")

                    if len(npc_name) == 0:
                        print(f"NPCAI has no npc name. {tree}")
                        continue
                    if npc == "" or npc == npc_name:
                        file_name = f"{npc_name}.json"
                        print(f"Saving NPCAI file {file_name}")

                        with open(os.path.join(destination_folder, file_name), "w") as f:
                            json.dump(tree, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    date_time = datetime.datetime.now().strftime("%m%d%Y-%H%M%S")
    parser.add_argument("-o", "--output", type=str, default=f"extract-{date_time}", help="Output directory. If this folder already exists, it will be deleted!")
    parser.add_argument("-i", "--input", type=str, help="'Sun Haven_Data' directory, so the script can access the assets")
    parser.add_argument("-n", "--npc", type=str, default="", help="If provided, only extract for the given npc. Else extract all npcs.")

    args = parser.parse_args()
    
    folder = args.output
    if os.path.exists(folder):
        print(f"Folder {folder} already exists, deleting...")
        shutil.rmtree(folder)
    os.mkdir(folder)
    unpack_all_assets(source_folder=args.input, destination_folder=folder, npc=args.npc)