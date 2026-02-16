import os
import subprocess
from utils import load_example_pddl


def run_fastdownward_planning():
    """
    Run Fast Downward planner locally using environment variable FAST_DOWNWARD_PATH.
    Returns a dict with planning success flags, output and any error messages.
    """
    domain_file = load_example_pddl("file_generati/domain_generato.pddl")
    problem_file = load_example_pddl("file_generati/problem_generato.pddl")

    results = {
        "planning_success": False,
        "solution_found": False,
        "error_message": None,
        "planning_output": None
    }

    try:
        if domain_file is None:
            results["error_message"] = "Error loading domain file"
            return results

        if problem_file is None:
            results["error_message"] = "Error loading problem file"
            return results

        print("Starting Fast Downward locally...")

        # Read env var for local Fast Downward path
        fd_path = os.getenv('FAST_DOWNWARD_PATH')
        if fd_path:
            fd_path = os.path.expanduser(fd_path)

        # Check configuration
        if not fd_path:
            results["error_message"] = "FAST_DOWNWARD_PATH environment variable not configured."
            print("FAST_DOWNWARD_PATH not configured.")
            return results

        if not os.path.exists(fd_path):
            results["error_message"] = f"Fast Downward not found at: {fd_path}"
            print(f"Fast Downward not found at: {fd_path}")
            return results

        domain_path = "file_generati/domain_generato.pddl"
        problem_path = "file_generati/problem_generato.pddl"

        if not os.path.exists(domain_path):
            results["error_message"] = f"Domain file not found: {domain_path}"
            return results

        if not os.path.exists(problem_path):
            results["error_message"] = f"Problem file not found: {problem_path}"
            return results

        # Build command for Fast Downward (planning only)
        command = [
            "python", fd_path,
            domain_path, problem_path,
            "--search", "astar(blind())"
        ]

        # Execute Fast Downward locally
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300
        )

        output = result.stdout + result.stderr
        results["planning_output"] = output

        print(f"Fast Downward exit code: {result.returncode}")
        if output.strip():
            print("Fast Downward output:")
            print("-" * 50)
            print(output)
            print("-" * 50)

        if "Solution found" in output or "Plan found" in output:
            results["planning_success"] = True
            results["solution_found"] = True
            print("Plan found by Fast Downward")
        else:
            print("No plan found.")
            if result.returncode != 0:
                results["error_message"] = f"Fast Downward failed with exit code: {result.returncode}"

    except subprocess.TimeoutExpired:
        results["error_message"] = "Timeout: Fast Downward took too long"
        print("Timeout: Fast Downward took too long")

    except Exception as e:
        results["error_message"] = f"Error running Fast Downward: {str(e)}"
        print(f"Fast Downward planning error: {e}")

    return results


def get_fastdownward_solution():
    """
    Read the local 'sas_plan' file and extract the list of actions.
    Returns a dict containing the actions list and status flags.
    """
    results = {
        "solution_retrieved": False,
        "solution_path": None,
        "actions": [],
        "error_message": None
    }

    try:
        sas_plan_path = "sas_plan"

        if not os.path.exists(sas_plan_path):
            results["error_message"] = "sas_plan file not found"
            print("sas_plan file not found")
            return results

        with open(sas_plan_path, 'r', encoding='utf-8') as file:
            solution_content = file.read().strip()

        if solution_content:
            lines = solution_content.split('\n')
            actions = []

            for line in lines:
                line = line.strip()
                # Ignore empty lines, comments (;) and cost lines
                if line and not line.startswith(';') and not line.startswith('cost'):
                    actions.append(line)

            results["solution_retrieved"] = True
            results["solution_path"] = sas_plan_path
            results["actions"] = actions

        else:
            results["error_message"] = "sas_plan file is empty"
            print("sas_plan file is empty")

    except FileNotFoundError:
        results["error_message"] = "sas_plan file not found"
        print("sas_plan file not found")

    except Exception as e:
        results["error_message"] = f"Error retrieving solution: {str(e)}"
        print(f"Error retrieving solution: {e}")

    return results


def run_fastdownward_complete():
    print("Starting complete FastDownward process...")

    # Phase 1: Planning
    print("\n" + "=" * 60)
    print("PHASE 1: PLANNING")
    print("=" * 60)

    planning_results = run_fastdownward_planning()

    if not planning_results["planning_success"]:
        print(f"Planning failed: {planning_results['error_message']}")
        return {
            "overall_success": False,
            "planning_results": planning_results,
            "solution_results": None
        }

    # Phase 2: Retrieve solution
    print("\n" + "=" * 60)
    print("PHASE 2: RETRIEVE SOLUTION")
    print("=" * 60)

    solution_results = get_fastdownward_solution()

    if not solution_results["solution_retrieved"]:
        print(f"Solution retrieval failed: {solution_results['error_message']}")

    overall_success = planning_results["planning_success"] and solution_results["solution_retrieved"]

    final_results = {
        "overall_success": overall_success,
        "planning_results": planning_results,
        "solution_results": solution_results
    }

    return final_results


# Valida il piano generato (sas_plan) utilizzando il validatore VAL.
def validate_plan_with_val():
    """
    Validate the generated plan using the VAL validator binary specified by VAL_PATH.
    Returns a dict with validation status, output and parsed details.
    """
    results = {
        "validation_successful": False,
        "plan_valid": False,
        "validation_output": "",
        "error_message": None,
        "validation_details": {}
    }

    try:
        val_path = os.getenv('VAL_PATH')
        if val_path:
            val_path = os.path.expanduser(val_path)

        if not val_path:
            results["error_message"] = "VAL_PATH environment variable not configured."
            print("VAL_PATH not configured. Ensure VAL_PATH is set.")
            return results

        if not os.path.exists(val_path):
            results["error_message"] = f"VAL binary not found at: {val_path}"
            print(f"VAL binary not found at: {val_path}")
            return results

        domain_path = "file_generati/domain_generato.pddl"
        problem_path = "file_generati/problem_generato.pddl"
        sas_plan_path = "sas_plan"

        required_files = [domain_path, problem_path, sas_plan_path]

        for file_path in required_files:
            if not os.path.exists(file_path):
                results["error_message"] = f"Missing file: {file_path}"
                print(f"Missing file: {file_path}")
                return results

        print("Running VAL validation...")

        # Command: validate <domain> <problem> <plan>
        command = [val_path, domain_path, problem_path, sas_plan_path]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60
        )

        validation_output = result.stdout + result.stderr
        results["validation_output"] = validation_output

        print("VAL output:")
        print(validation_output)
        print("-" * 50)

        if result.returncode == 0:
            results["validation_successful"] = True

            if "Plan valid" in validation_output or "Plan is valid" in validation_output or "Plan Valid" in validation_output:
                results["plan_valid"] = True
                print("Plan validated successfully")
            elif "Plan invalid" in validation_output or "Plan is invalid" in validation_output or "Plan Invalid" in validation_output:
                results["plan_valid"] = False
                print("Plan is invalid")
            else:
                if "Error" in validation_output or "error" in validation_output or "ERROR" in validation_output or "Bad" in validation_output:
                    results["plan_valid"] = False
                    print("Errors detected during validation")
                else:
                    results["plan_valid"] = True
                    print("Plan appears valid (no errors detected)")
        else:
            results["validation_successful"] = False
            results["error_message"] = f"VAL returned error code: {result.returncode}"
            print(f"Error running VAL: {result.returncode}")

        results["validation_details"] = parse_val_output(validation_output)

    except subprocess.TimeoutExpired:
        results["error_message"] = "Timeout during VAL validation"
        print("Timeout during validation")

    except Exception as e:
        results["error_message"] = f"Error during validation: {str(e)}"
        print(f"Error during validation: {e}")

    return results

# Analizza l'output di VAL per estrarre informazioni dettagliate; riceve come parametro l'output completo di VAL.
def parse_val_output(output):
    """
    Parse VAL output to extract goals achieved, precondition failures, warnings and execution trace.
    Returns a details dict.
    """
    details = {
        "goals_achieved": [],
        "preconditions_satisfied": True,
        "execution_errors": [],
        "warnings": [],
        "plan_execution_trace": []
    }

    lines = output.split('\n')

    for line in lines:
        line = line.strip()

        if "Goal" in line and ("achieved" in line or "satisfied" in line):
            details["goals_achieved"].append(line)

        if "Precondition" in line and ("not satisfied" in line or "false" in line or "failed" in line):
            details["preconditions_satisfied"] = False
            details["execution_errors"].append(line)

        if any(keyword in line for keyword in ["Error:", "ERROR:", "Failed:", "Invalid:", "Cannot"]):
            details["execution_errors"].append(line)

        if "Warning:" in line or "WARNING:" in line:
            details["warnings"].append(line)

        if line.startswith("Checking action") or line.startswith("Action:"):
            details["plan_execution_trace"].append(line)

    return details

def get_validation_error_for_correction(validation_results):
    """
    Build and return a human-readable validation error string suitable for PDDL correction flows.
    """
    if validation_results["validation_successful"]:
        return "No validation errors. Plan is valid."

    if not validation_results["validation_successful"]:
        error_message = "VAL VALIDATION ERRORS:\n"

        if "validation_output" in validation_results and validation_results["validation_output"]:
            error_message += f"VAL Output:\n{validation_results['validation_output']}\n\n"

        if "error_message" in validation_results and validation_results["error_message"]:
            error_message += f"Error: {validation_results['error_message']}\n"

        if "validation_details" in validation_results:
            details = validation_results["validation_details"]
            if details.get("execution_errors"):
                error_message += "\nExecution errors:\n"
                for error in details["execution_errors"]:
                    error_message += f"- {error}\n"

            if details.get("warnings"):
                error_message += "\nWarnings:\n"
                for warning in details["warnings"]:
                    error_message += f"- {warning}\n"

        return error_message

    if validation_results.get("plan_valid"):
        return None

    error_message = "VAL VALIDATION ERRORS:\n"

    if "validation_output" in validation_results and validation_results["validation_output"]:
        error_message += f"VAL Output:\n{validation_results['validation_output']}\n"

    error_message += "\nDETAILS:\n"

    if "validation_details" in validation_results:
        details = validation_results["validation_details"]
        if details.get("execution_errors"):
            error_message += "Execution errors:\n"
            for error in details["execution_errors"]:
                error_message += f"- {error}\n"

        if details.get("warnings"):
            error_message += "Warnings:\n"
            for warning in details["warnings"]:
                error_message += f"- {warning}\n"

    return error_message