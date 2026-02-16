import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))
from file_generation.lore_generation import generate_lore
import os ,json
from langchain_google_genai import ChatGoogleGenerativeAI
from file_generation.domain_generation import create_domain_pddl
from file_generation.problem_generation import create_problem_pddl
from correction_and_validation.reflective_agent import run_correction_workflow,run_user_correction_pddl,update_lore_with_corrections
from correction_and_validation.pddl_validation import run_fastdownward_complete
from dotenv import load_dotenv
from utils import print_lore, print_plan
from file_generation.story_generation import generate_story
import subprocess
from correction_and_validation.pddl_validation import validate_plan_with_val, get_validation_error_for_correction

load_dotenv()  # For the API key


def main():
    """
    Generate lore and run the full pipeline: domain/problem generation, PDDL validation,
    human-in-the-loop corrections, and final story generation.
    """
    API_KEY=os.getenv("API_KEY")

    # Configure API key
    os.environ["GOOGLE_API_KEY"] = API_KEY

    # Initialize the Gemini model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.6
    )

    user_input= input("Enter your request to generate the lore: ")
    
    
    # create and save the lore
    generate_lore(user_input,llm)

    # ask the user if they want to edit the generated lore
    print("Here is the generated lore:")
    print_lore() #in utils
    
    # Human-in-the-loop edits for lore
    while True:
        scelta_modifica = input("\n\nDo you want to edit the lore? (Y/N): ").strip().upper()
        if scelta_modifica in ('N', 'NO'):
            break
        elif scelta_modifica in ('S', 'Y', 'SI', 'YES'):
            user_input = input("Enter your request to modify the lore: ")
            update_lore_with_corrections(user_input, llm)
            print("Here is the updated lore:")
            print_lore()
            continue
        else:
            print("Invalid choice, please try again.")

    # create domain and problem PDDL from the generated lore
    create_domain_pddl(llm)
    create_problem_pddl(llm)

    # FULL VALIDATION (FastDownward + VAL)
    validation_final_results = validate_pddl_complete(llm)
    
    if not validation_final_results["success"]:
        print(f"Error: {validation_final_results['error']}")
        return validation_final_results
    
    # Extract final results
    pddl_validation_output = validation_final_results["pddl_output"]
    
    # Human-in-the-loop (HITL) for plan validation
    plan_accepted = False
    
    while not plan_accepted:
        # Show the plan to the user and ask for approval
        plan_accepted = human_plan_validation(pddl_validation_output["solution_results"]["actions"])
        if plan_accepted:
            break

        # Option to allow the user to suggest corrections
        user_correction = input("Describe the problem or desired correction: ")
        print("Applying suggested corrections...")
        run_user_correction_pddl(user_correction, llm) 

        validation_final_results = validate_pddl_complete(llm)
        
        if not validation_final_results["success"]:
            print("Try again with different corrections...")
            continue
        
        pddl_validation_output = validation_final_results["pddl_output"]
        
    print("Generating the story...")
    generate_story(llm)

def validate_pddl_complete(llm, max_attempts=100):
    """
    Run full PDDL validation loop using FastDownward and VAL, with automatic corrections.

    Returns a dict with success status, outputs and attempt count.
    """
    attempt = 0
    
    while attempt < max_attempts:
        print(f"\nAttempting validation {attempt + 1}/{max_attempts}")
        
        # STEP 1: FastDownward validation
        pddl_validation_output = run_fastdownward_complete()
        
        if not pddl_validation_output["overall_success"]:
            print("Correcting PDDL for FastDownward...")
            run_correction_workflow(pddl_validation_output["planning_results"]["planning_output"], llm)
            attempt += 1
            continue
        
        # STEP 2: VAL validation
        validation_results = validate_plan_with_val()
        
        if validation_results["validation_successful"] and validation_results["plan_valid"]:
            print(f"\nVALIDATION COMPLETE: SUCCESS! (Attempts: {attempt + 1}/{max_attempts})")
            return {
                "success": True,
                "pddl_output": pddl_validation_output,
                "val_results": validation_results,
                "attempts": attempt + 1
            }
        
        # If VAL fails, correct and restart from FastDownward
        print("Correcting PDDL for VAL and restarting from FastDownward...")
        
        error_message = get_validation_error_for_correction(validation_results)
        print(f"Validation error: {error_message}")
        run_correction_workflow(error_message, llm)
        
        attempt += 1
    
    # Max attempts exhausted
    print(f"\nVALIDATION FAILED: exhausted all {max_attempts} attempts")
    return {
        "success": False,
        "error": "Numero massimo di tentativi raggiunto",
        "attempts": max_attempts
    }


def human_plan_validation(actions_list):
    """
    Display a generated plan to the user and request acceptance. Returns True if accepted.
    """
    print("\nPLAN GENERATED:")
    print("-" * 50)
    
    if actions_list and len(actions_list) > 0:
        print(f"Numero totale di azioni: {len(actions_list)}")
        print("\nSequenza delle azioni:")
        for i, action in enumerate(actions_list, 1):
            print(f"  {i:2d}. {action}")
        
        # Show statistics
        print(f"\nPlan statistics:")
        print(f"   - Length: {len(actions_list)} actions")
        
    else:
        print(" No action(s) found in the plan!")
        return False
    
    print("-" * 50)

    while True:
        scelta = input("\nIs the generated plan satisfactory? (Y/N): ").strip().upper()

        if scelta == 'Y' or scelta == 'S':
            print("Plan accepted by user!")
            return True
        elif scelta == 'N':
            print("Plan will be regenerated with your corrections...")
            return False
        else:
            print("Invalid choice, enter 'Y' or 'N'.")

if __name__ == "__main__":
    main()

          