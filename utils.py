import json


def load_example_json(filename):
    """
    Load and return JSON from the given filename. Returns None on error.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File {filename} not found in current folder")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None


def load_example_pddl(filename):
    """
    Load and return the contents of a PDDL file as text. Returns None on error.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {filename} not found in current folder")
        return None
    except Exception as e:
        print(f"Error loading PDDL file: {e}")
        return None


def print_lore():
    """
    Load generated lore JSON and print a human-readable summary to the console.
    Also return a compact Markdown narrative string.
    """
    lore_data = load_example_json("file_generati/lore_generata_per_utente.json")
    if not lore_data:
        print("No lore data available")
        return ""

    # Extract sections
    quest = lore_data["lore_document"]["quest_description"]
    branching = lore_data["lore_document"]["branching_factor"]
    depth = lore_data["lore_document"]["depth_constraints"]

    # Compose compact markdown narrative
    narrative = f"""
### Title of the Quest:
**{quest["title"]}**

### World Background:
{quest["world_background"]}

### Initial Situation:
{quest["initial_state"]}

### Quest Goal:
**{quest["goal"]}**

### Obstacles along the way:"""

    for obstacle in quest.get("obstacles", []):
        narrative += f"\n- {obstacle}"

    narrative += f"""

### Contextual Information:
*{quest.get("contextual_information", '')}*

### Narrative Structure:
- **Actions per State:** Min: {branching["min_actions_per_state"]} | Max: {branching["max_actions_per_state"]}
- **Steps to Goal:** Min: {depth["min_steps_to_goal"]} | Max: {depth["max_steps_to_goal"]}"""

    # Final console print in readable format
    console_story = f"""
{'='*80}
                    GENERATED LORE
{'='*80}

TITLE: {quest["title"]}

WORLD:
{quest["world_background"]}

INITIAL SITUATION:
{quest["initial_state"]}

GOAL:
{quest["goal"]}

OBSTACLES:"""

    for i, obstacle in enumerate(quest.get("obstacles", []), 1):
        console_story += f"\n   {i}. {obstacle}"

    console_story += f"""

CONTEXT:
{quest.get("contextual_information", '')}

NARRATIVE PARAMETERS:
   - Actions per state: {branching["min_actions_per_state"]}-{branching["max_actions_per_state"]}
   - Steps to goal: {depth["min_steps_to_goal"]}-{depth["max_steps_to_goal"]}

{'='*80}
"""

    print(console_story)
    return narrative


def print_plan():
    """
    Print the contents of the local 'sas_plan' file and return it as a string.
    """
    try:
        with open("sas_plan", 'r', encoding='utf-8') as f:
            solution = f.read()
            print(solution)
            return solution
    except FileNotFoundError:
        print("sas_plan file not found.")
    except Exception as e:
        print(f"Error loading plan: {e}")


