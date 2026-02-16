from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import json
import sys
import random
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import base64
from io import BytesIO

parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from dotenv import load_dotenv
from file_generation.lore_generation import generate_lore
from langchain_google_genai import ChatGoogleGenerativeAI
from file_generation.domain_generation import create_domain_pddl
from file_generation.problem_generation import create_problem_pddl
from correction_and_validation.reflective_agent import run_correction_workflow, run_user_correction_pddl, update_lore_with_corrections
from correction_and_validation.pddl_validation import run_fastdownward_complete, validate_plan_with_val, get_validation_error_for_correction
from utils import print_lore, print_plan, load_example_json
from file_generation.story_generation import generate_story

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'questmaster-ai-secret-key-change-in-production')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'YOUR_API_KEY_HERE')

app.debug = True

class AppState:
    CREATION = "creation"
    LORE_REVIEW = "lore_review"
    VALIDATION = "validation"
    PLAN_REVIEW = "plan_review"
    STORY_GENERATION = "story_generation"
    GAMEPLAY = "gameplay"

def init_session():
    """Initialize the session with default values."""
    if 'app_state' not in session:
        session['app_state'] = AppState.CREATION
    if 'llm' not in session:
        session['llm'] = None
    if 'generated_lore' not in session:
        session['generated_lore'] = ""
    if 'validation_results' not in session:
        session['validation_results'] = None
    if 'current_plan' not in session:
        session['current_plan'] = []
    if 'story_generated' not in session:
        session['story_generated'] = False
    if 'current_node' not in session:
        session['current_node'] = 'start'
    if 'story_history' not in session:
        session['story_history'] = []
    if 'choices_made' not in session:
        session['choices_made'] = []
    if 'choice_order_seed' not in session:
        session['choice_order_seed'] = random.randint(1, 1000000)
    if 'original_user_input' not in session:
        session['original_user_input'] = ""

def check_existing_story():
    """Check if a generated story already exists on disk."""
    storia_path = "file_generati/storia_generata.json"
    lore_path = "file_generati/lore_generata_per_utente.json"
    return os.path.exists(storia_path) and os.path.exists(lore_path)

def load_formatted_lore():
    """Load and format the generated lore from the JSON file."""
    try:
        lore_path = "file_generati/lore_generata_per_utente.json"
        if os.path.exists(lore_path):
            with open(lore_path, 'r', encoding='utf-8') as f:
                lore_data = json.load(f)
                return lore_data.get('lore_document', {}).get('quest_description', {})
        return None
    except Exception as e:
        print(f"Error loading lore: {e}")
        return None

@app.route('/')
def index():
    """Main route - redirect based on application state."""
    init_session()
    return redirect(url_for('get_state_route', state=session['app_state']))

@app.route('/state/<state>')
def get_state_route(state):
    """Dynamic route that renders the template for the given application state."""
    init_session()
    
    if state == AppState.CREATION:
        # Check if a generated story already exists
        has_existing_story = check_existing_story()
        session_data = dict(session)
        session_data['has_existing_story'] = has_existing_story
        return render_template('creation.html', state=session_data, has_existing_story=has_existing_story)
    elif state == AppState.LORE_REVIEW:
        # Load and format the generated lore
        lore_data = load_formatted_lore()
        session_data = dict(session)
        session_data['formatted_lore'] = lore_data
        return render_template('lore_review.html', state=session_data)
    elif state == AppState.VALIDATION:
        return render_template('validation.html', state=session)
    elif state == AppState.PLAN_REVIEW:
        return render_template('plan_review.html', state=session)
    elif state == AppState.STORY_GENERATION:
        return render_template('story_generation.html', state=session)
    elif state == AppState.GAMEPLAY:
        return render_template('gameplay_new.html', state=session)
    else:
        return redirect(url_for('index'))

@app.route('/api/generate_lore', methods=['POST'])
def api_generate_lore():
    """API endpoint to generate lore from user input using the configured LLM."""
    try:
        data = request.get_json()
        user_input = data.get('user_input', '')
        
        if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
            return jsonify({'success': False, 'error': 'API Key not configured'})

        if not user_input.strip():
            return jsonify({'success': False, 'error': 'Adventure description required'})
        
        # Configure LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )
        session['llm_configured'] = True
        session['original_user_input'] = user_input
        
        # Generates lore
        generated_lore = generate_lore(user_input, llm)
        session['generated_lore'] = generated_lore
        session['app_state'] = AppState.LORE_REVIEW
        
        return jsonify({
            'success': True, 
            'lore': generated_lore,
            'next_state': AppState.LORE_REVIEW
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/approve_lore', methods=['POST'])
def api_approve_lore():
    """API endpoint to approve generated lore and trigger PDDL generation."""
    try:
        # Generates domain and problem PDDL
        if 'llm_configured' not in session:
            return jsonify({'success': False, 'error': 'Session not configured'})
            
        # Configure LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )
        
        lore_content = session.get('generated_lore', '')
        
        # Generates domain PDDL
        create_domain_pddl(llm)
        
        # Generates problem PDDL
        create_problem_pddl(llm)
        
        session['app_state'] = AppState.VALIDATION
        
        return jsonify({
            'success': True,
            'next_state': AppState.VALIDATION
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/validate_pddl', methods=['POST'])
def api_validate_pddl():
    """API endpoint to run full PDDL validation (FastDownward + VAL)."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )
        
        # Run complete validation
        validation_results = validate_pddl_complete(llm)
        session['validation_results'] = validation_results
        
        if validation_results['success']:
            session['current_plan'] = validation_results["pddl_output"]["solution_results"]["actions"]
            session['app_state'] = AppState.PLAN_REVIEW
        
        return jsonify({
            'success': validation_results['success'],
            'results': validation_results,
            'next_state': AppState.PLAN_REVIEW if validation_results['success'] else AppState.VALIDATION
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate_story', methods=['POST'])
def api_generate_story():
    """API endpoint to generate the final interactive story JSON."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )
        
        # Generates story
        generate_story(llm)
        session['story_generated'] = True
        session['app_state'] = AppState.GAMEPLAY
        session['current_node'] = 'start'
        session['story_history'] = []
        session['choices_made'] = []
        session.modified = True
        
        return jsonify({
            'success': True,
            'next_state': AppState.GAMEPLAY
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/game/load_story')
def api_load_story():
    """API endpoint to load the generated story for gameplay."""
    try:
        story_file = Path("file_generati/storia_generata.json")
        if not story_file.exists():
            return jsonify({'success': False, 'error': 'Story file not found'})
            
        with open(story_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
            
        return jsonify({'success': True, 'story': story_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/game/make_choice', methods=['POST'])
def api_make_choice():
    """API endpoint to record a player's choice and return the next node data."""
    try:
        init_session()
        data = request.get_json()
        next_node = data.get('next_node')
        choice_text = data.get('choice_text')
        
        # Save the current node to history before updating
        history = session.get('story_history', [])
        current = session.get('current_node', 'start')
        history.append(current)
        session['story_history'] = history
        
        # Update choices made
        choices = session.get('choices_made', [])
        choices.append({
            'choice': choice_text,
            'timestamp': datetime.now().isoformat()
        })
        session['choices_made'] = choices
        
        # Update the current node
        session['current_node'] = next_node
        session.modified = True

        # Load the corresponding node_data from file to return to the client
        try:
            story_path = "file_generati/storia_generata.json"
            if os.path.exists(story_path):
                with open(story_path, 'r', encoding='utf-8') as f:
                    story_data = json.load(f)
                story_dict = {node['node_id']: node for node in story_data}
                node_data = story_dict.get(next_node)
            else:
                node_data = None
        except Exception:
            node_data = None

        return jsonify({
            'success': True,
            'current_node': next_node,
            'node_data': node_data,
            'choice_order_seed': session.get('choice_order_seed')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/game/undo', methods=['POST'])
def api_undo_choice():
    """API endpoint to undo the last player choice and restore previous node."""
    try:
        init_session()
        # Retrieve history
        history = session.get('story_history', [])
        
        if not history:
            return jsonify({'success': False, 'error': 'You are at the start, cannot undo.'})
            
        # Pop the last visited node
        previous_node = history.pop()
        
        session['story_history'] = history
        
        choices = session.get('choices_made', [])
        if choices:
            choices.pop()
            session['choices_made'] = choices

        session['current_node'] = previous_node
        session.modified = True

        # Also provide node_data to avoid client cache dependencies
        try:
            story_path = "file_generati/storia_generata.json"
            if os.path.exists(story_path):
                with open(story_path, 'r', encoding='utf-8') as f:
                    story_data = json.load(f)
                story_dict = {node['node_id']: node for node in story_data}
                node_data = story_dict.get(previous_node)
            else:
                node_data = None
        except Exception:
            node_data = None

        return jsonify({
            'success': True,
            'current_node': previous_node,
            'node_data': node_data,
            'choice_order_seed': session.get('choice_order_seed')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/game/reset', methods=['POST'])
def api_game_reset():
    """API endpoint to fully reset the game state for the current session."""
    try:
        init_session()
        session['current_node'] = 'start'
        session['story_history'] = []
        session['choices_made'] = []
        session['choice_order_seed'] = random.randint(1, 1000000)
        session.modified = True

        try:
            story_path = "file_generati/storia_generata.json"
            if os.path.exists(story_path):
                with open(story_path, 'r', encoding='utf-8') as f:
                    story_data = json.load(f)
                story_dict = {node['node_id']: node for node in story_data}
                start_data = story_dict.get('start')
            else:
                start_data = None
        except Exception:
            start_data = None

        return jsonify({
            'success': True,
            'current_node': 'start',
            'node_data': start_data,
            'choice_order_seed': session.get('choice_order_seed')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error resetting: {str(e)}"
        })

def validate_pddl_complete(llm, max_attempts=5):  # Limit attempts to avoid infinite loops
    """Run full PDDL validation with FastDownward and VAL, applying automated corrections."""
    attempt = 0
    
    while attempt < max_attempts:
        print(f"\nAttempting validation {attempt + 1}/{max_attempts}")
        
        # STEP 1: FastDownward validation
        pddl_validation_output = run_fastdownward_complete()
        
        # If FastDownward fails, analyze the error type
        if not pddl_validation_output["overall_success"]:
            planning_output = pddl_validation_output["planning_results"]["planning_output"]
            
            if ("No relaxed solution" in planning_output or 
                "Completely explored state space -- no solution" in planning_output or
                "Search stopped without finding a solution" in planning_output):
                
                print("FUNDAMENTAL ERROR: The PDDL problem has no reachable solutions")
                print("Regenerating domain and problem PDDL files...")
                
                try:
                    create_domain_pddl(llm)
                    create_problem_pddl(llm)
                    print("PDDL files regenerated")
                except Exception as e:
                    print(f"Error during regeneration: {e}")
                    
            else:
                print("Correcting PDDL for FastDownward...")
                run_correction_workflow(planning_output, llm)
                
            attempt += 1
            continue
        
        # STEP 2: VAL validation
        validation_results = validate_plan_with_val()
        
        # If VAL succeeds, we are done
        if validation_results["validation_successful"] and validation_results["plan_valid"]:
            print(f"\nVALIDATION COMPLETE: SUCCESS! (Attempts: {attempt + 1}/{max_attempts})")
            return {
                "success": True,
                "pddl_output": pddl_validation_output,
                "val_results": validation_results,
                "attempts": attempt + 1
            }
        
        # If VAL fails, correct and restart
        print("Correcting PDDL for VAL and restarting from FastDownward...")
        
        error_message = get_validation_error_for_correction(validation_results)
        print(f"Validation error: {error_message}")
        run_correction_workflow(error_message, llm)
        
        attempt += 1
    
    # Attempts exhausted
    print(f"\nVALIDATION FAILED: exhausted all {max_attempts} attempts")
    print("Suggestion: Try simplifying the lore description or making it more specific")
    return {
        "success": False,
        "error": f"Maximum attempts reached ({max_attempts}). The generated PDDL files may have fundamental design issues.",
        "attempts": max_attempts,
        "suggestion": "Try simplifying the adventure description or make it more specific"
    }

@app.route('/api/game/load', methods=['GET'])
def api_load_game():
    """API endpoint to load the generated story for the game client."""
    try:
        init_session()

        story_path = "file_generati/storia_generata.json"
        if os.path.exists(story_path):
            with open(story_path, 'r', encoding='utf-8') as f:
                story_data = json.load(f)

            story_dict = {node['node_id']: node for node in story_data}

            current_node = session.get('current_node', 'start')
            node_data = story_dict.get(current_node)

            return jsonify({
                'success': True,
                'story': story_dict,
                'current_node': current_node,
                'node_data': node_data,
                'choice_order_seed': session.get('choice_order_seed')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Story not found. Generate a story first.'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error loading: {str(e)}"
        })

@app.route('/api/game/choice', methods=['POST'])
def api_game_choice():
    """API endpoint to process player choices and return the next node."""
    try:
        data = request.json
        choice = data.get('choice', '')
        current_node = session.get('current_node', 'start')
        story_data = session.get('story_data', {})
        
        if not story_data or current_node not in story_data:
            return jsonify({
                'success': False,
                'error': 'Invalid game state'
            })
        
        node_data = story_data[current_node]
        next_nodes = node_data.get('next_nodes', [])
        
        if next_nodes:
            next_node = next_nodes[0]
            session['current_node'] = next_node
            
            return jsonify({
                'success': True,
                'next_node': next_node,
                'node_data': story_data.get(next_node, {})
            })
        else:
            return jsonify({
                'success': True,
                'next_node': current_node,
                'message': 'You have completed the adventure!'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error processing: {str(e)}"
        })

@app.route('/api/check_existing_story', methods=['GET'])
def api_check_existing_story():
    """API endpoint to check if a generated story exists and return a preview."""
    try:
        has_story = check_existing_story()
        story_preview = None
        
        if has_story:
            lore_path = "file_generati/lore_generata_per_utente.json"
            storia_path = "file_generati/storia_generata.json"
            
            with open(lore_path, 'r', encoding='utf-8') as f:
                lore_data = json.load(f)
                quest_desc = lore_data.get('lore_document', {}).get('quest_description', {})
            
            with open(storia_path, 'r', encoding='utf-8') as f:
                storia_data = json.load(f)
                start_node = next((node for node in storia_data if node.get('node_id') == 'start'), None)
            
            story_preview = {
                'title': quest_desc.get('title', 'Existing Adventure'),
                'description': start_node.get('description', 'No description available') if start_node else 'No description available',
                'initial_state': quest_desc.get('initial_state', ''),
                'goal': quest_desc.get('goal', '')
            }
        
        return jsonify({
            'success': True,
            'has_story': has_story,
            'story_preview': story_preview
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/load_existing_story', methods=['POST'])
def api_load_existing_story():
    """API endpoint to load and continue with an existing generated story."""
    try:
        lore_path = "file_generati/lore_generata_per_utente.json"
        storia_path = "file_generati/storia_generata.json"
        
        if not os.path.exists(lore_path) or not os.path.exists(storia_path):
            return jsonify({
                'success': False,
                'error': 'Story files not found'
            })
        
        with open(lore_path, 'r', encoding='utf-8') as f:
            lore_data = json.load(f)
            session['generated_lore'] = json.dumps(lore_data)
        
        with open(storia_path, 'r', encoding='utf-8') as f:
            storia_data = json.load(f)

        session['llm_configured'] = True
        session['story_generated'] = True
        session['current_node'] = 'start'
        session['story_history'] = []
        session['app_state'] = AppState.GAMEPLAY
        
        return jsonify({
            'success': True,
            'next_state': AppState.GAMEPLAY
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)