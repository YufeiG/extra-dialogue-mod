
using BepInEx;
using HarmonyLib;
using Wish;
using UnityEngine;
using System;
using System.Collections.Generic;
using BepInEx.Configuration;



namespace extradialogue
{

    [Serializable]
    public class ExtraDialogueData {
        public string npc_name;
        public string[] general_cycles;
        public string[] dating_cycles;
        public string[] married_cycles;

    }


    [BepInPlugin("org.mox.plugins.extradialogue", "Extra Dialogue", "1.0.0")]
    public class Plugin : BaseUnityPlugin
    {
        private Harmony m_harmony = new Harmony("org.mox.plugins.extradialogue");
        private static Dictionary<string, ExtraDialogueData> ExtraDialogues = new Dictionary<string, ExtraDialogueData>();
	    private static ConfigEntry<bool> _isDebugging;
	    private static ConfigEntry<bool> _showOneCycleADay;
	    private static HashSet<string> _createdTextAssets = new HashSet<string>();

        private void Awake()
        {
            _isDebugging = this.Config.Bind<bool>("General", "IsDebugging", true, "For debugging");
            _showOneCycleADay = this.Config.Bind<bool>("General", "ShowOneCycleADay", false, "Set to true to show one cycle a day, like the included cycles in the game");

            // Plugin startup logic
            Logger.LogInfo($"Plugin extradialogue is loaded!");


            string folderPath = "BepInEx/plugins/dialogue";
            string searchPattern = "*.json";
            string[] files = System.IO.Directory.GetFiles(folderPath, searchPattern, System.IO.SearchOption.AllDirectories);

            foreach (string file in files) {
                string jsonString = System.IO.File.ReadAllText(file);
                ExtraDialogueData data = JsonUtility.FromJson<ExtraDialogueData>(jsonString);
                System.Diagnostics.Trace.Assert(!string.IsNullOrEmpty(data.npc_name));
                ExtraDialogues[data.npc_name] = data;
                Logger.LogInfo($"Read json for {data.npc_name}");
            }

            this.m_harmony.PatchAll();
	    }

        [HarmonyPatch(typeof(NPCAI), "GenerateCycle")]
        class HarmonyPatch_NPCAI_GenerateCycle {
            private static void Postfix(ref NPCAI __instance, ref bool ___hasCycle, ref TextAsset ____currentCycle) {
                if (string.IsNullOrEmpty(__instance.NPCName)) {
                    return;
                }
                Console.WriteLine($"GenerateCycle {__instance.NPCName} {___hasCycle}");


                if (___hasCycle) {
                    // don't override existing cycle
                    return;
                }
                                    
                if (ExtraDialogues.ContainsKey(__instance.NPCName)) {
                    if(_showOneCycleADay.Value && (SingletonBehaviour<GameSave>.Instance.GetProgressIntCharacter("UsedDialogueCycle" + __instance.NPCName) > DayCycle.Day)) {
                        // already seen a cycle today
                        return;
                    }
                    ExtraDialogueData data = ExtraDialogues[__instance.NPCName];
                    string[] cyclesArray = {};
                    
                    if (__instance.IsMarriedToPlayer() && data.married_cycles != null) {
                        cyclesArray = data.married_cycles;
                    }else if (__instance.IsDatingPlayer() && data.dating_cycles != null) {
                        cyclesArray = data.dating_cycles;
                    } else if (data.general_cycles != null) {
                        cyclesArray = data.general_cycles;
                    }

                    // we have overrides
                    for (int i = 0; i < cyclesArray.Length; i++) {
                        TextAsset chosenCycle = new TextAsset(text: cyclesArray[i]);
                        if (_isDebugging.Value) {
                            // doesn't matter if seen before. used for debugging
                            ____currentCycle = chosenCycle;
                            return; 
                        }
                        var hash =  Hash128.Compute(cyclesArray[i]);
                        string key = __instance.NPCName + hash.ToString();
                        if(!SingletonBehaviour<GameSave>.Instance.GetProgressBoolCharacter(key)) {
                            // not seen yet
                            ____currentCycle = chosenCycle;
                            _createdTextAssets.Add(chosenCycle.name);
                            return;
                        }
                    }
                }
            }
        }


    }
}
