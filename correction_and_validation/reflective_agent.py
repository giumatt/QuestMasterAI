from utils import load_example_pddl, load_example_json
import json


def correct_pddl(pddl_problem, llm):
    """
    Use the provided LLM to generate a corrected PDDL (domain or problem) based on the
    reported PDDL problem and current files. Returns (corrected_pddl, is_domain, is_problem).
    """
    # Load necessary files
    lore = load_example_json("file_generati/lore_generata_per_utente.json")
    domain = load_example_pddl("file_generati/domain_generato.pddl")
    problem = load_example_pddl("file_generati/problem_generato.pddl")

    # Build the prompt for the LLM
    prompt = f"""Sei un esperto di pianificazione automatica e PDDL (Planning Domain Definition Language).

    Il tuo compito è risolvere gli errori ottenuti in seguito alla valutazione di file di tipo domain.pddl e problem.pddl con Fast Downward o VAL.
    Gli errori possono riguardare la sintassi, la struttura, la logica del PDDL o ancora l'assenza di un percorso valido da input ad output.

    Gli errori possono riguardare molti aspetti, tra cui:
    - oggetti o predicati non definiti
    - mismatch di tipi
    - errori di sintassi (parentesi, variabili…)
    - incoerenze logiche tra domain e problem
    - mancanza di percorso valido

    ------------------ESEMPIO ERRORE------------------
    Di seguito un esempio di errore FASTDOWNWARD e relativa correzione:
    
    CODICE PDDL ERRATO:
    (:action muovi-personaggio
    :parameters (?p - personaggio ?from ?to - luogo)
    :precondition (and (at ?p ?from) (path ?from ?to))
    :effect (and (at ?p ?to) (not (at ?p ?from)))
    )

    ERRORE FASTDOWNWARD:
    Undefined predicate
    Got: path

    PROBLEMA:
    Il predicato "path" è utilizzato nell'azione ma non è stato 
    definito nella sezione :predicates del domain file.

    SOLUZIONE:
    Aggiungere la definizione del predicato nella sezione :predicates:

    (:predicates
        (at ?p - personaggio ?l - luogo)
        (path ?from ?to - luogo)
        ; altri predicati...
    )

    Oppure, se il predicato non serve, rimuoverlo dalla precondizione:
    (:action muovi-personaggio
    :parameters (?p - personaggio ?from ?to - luogo)
    :precondition (at ?p ?from)
    :effect (and (at ?p ?to) (not (at ?p ?from)))
    )
    ------------------FINE ESEMPIO ERRORE------------------

    Devi correggere il seguente errore: {pddl_problem} associato a questi file di lore, domain e problem PDDL:
    
    LORE:
    {lore}

    domain.pddl:
    {domain}

    problem.pddl:
    {problem}

    OUTPUT:
    Rispondi specificando chiaramente se stai correggendo il DOMAIN o il PROBLEM, seguito dal codice PDDL corretto.
    Usa il formato:
    CORREZIONE: [DOMAIN/PROBLEM]
    ```
    [codice PDDL corretto]
    ```"""

    # Invoke the LLM to obtain the correction
    llm_response = llm.invoke(prompt)
    response_text = llm_response.content.strip()

    is_domain_correction = False
    is_problem_correction = False
    
    # First check keywords
    if "CORREZIONE: DOMAIN" in response_text.upper():
        is_domain_correction = True
    elif "CORREZIONE: PROBLEM" in response_text.upper():
        is_problem_correction = True
    else:
        # Fallback
        first_lines = '\n'.join(response_text.split('\n')[:3]).upper()
        if "DOMAIN" in first_lines:
            is_domain_correction = True
        elif "PROBLEM" in first_lines:
            is_problem_correction = True
        else:
            # Last fallback
            if "```" in response_text:
                start_idx = response_text.find("```")
                if start_idx != -1:
                    first_end = response_text.find("\n", start_idx)
                    if first_end != -1:
                        last_start = response_text.rfind("```")
                        if last_start != start_idx:
                            code_block = response_text[first_end+1:last_start].strip()
                            # Check the code if it's a domain or a problem
                            if "(define (domain" in code_block:
                                is_domain_correction = True
                            elif "(define (problem" in code_block:
                                is_problem_correction = True
    
    # Extract PDDL from the response
    corrected_pddl = response_text
    if "```" in corrected_pddl:
        parts = corrected_pddl.split("```")
        if len(parts) >= 3:
            code_block = parts[1]
            lines = code_block.split('\n')
            if lines and ('pddl' in lines[0].lower() or lines[0].strip() == ''):
                corrected_pddl = '\n'.join(lines[1:]).strip()
            else:
                corrected_pddl = code_block.strip()
        else:
            corrected_pddl = corrected_pddl.replace("```", "").strip()
    
    # Further cleanup of possible residues
    corrected_pddl = corrected_pddl.replace("correzione: problem", "").replace("CORREZIONE: PROBLEM", "").strip()
    
    # If it is not possible to determine the type automatically, ask the user
    if not is_domain_correction and not is_problem_correction:

        # Prepare the message for the user (ask whether the correction targets domain or problem)
        query_message = f"""Cannot automatically determine whether this is a DOMAIN or PROBLEM correction.

        LLM response:
        {"-" * 50}
        {response_text}
        {"-" * 50}

        Is this a DOMAIN or PROBLEM correction? (D/P):"""

        # Interrupt execution and ask for human input (Human-in-the-loop)
        user_input = input(query_message).strip().upper()
        while True:
            if user_input in ['D', 'DOMAIN']:
                is_domain_correction = True
                is_problem_correction = False
                break
            elif user_input in ['P', 'PROBLEM']:
                is_domain_correction = False
                is_problem_correction = True
                break
            else:
                print("Invalid choice. Enter 'D' for Domain or 'P' for Problem.")
                user_input = input("(D/P): ").strip().upper()

    # Determine output filename
    if is_domain_correction:
        output_filename = "file_generati/domain_generato.pddl"
        file_type = "Domain"
    else:
        output_filename = "file_generati/problem_generato.pddl"
        file_type = "Problem"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(corrected_pddl)
        
        print(f"{file_type}.pddl corrected and saved to: {output_filename}")

    except Exception as e:
        error_message = f"Error saving corrected file: {e}"
        print(error_message)
        print(f"Response received:\n{response_text}")
    
    return corrected_pddl, is_domain_correction, is_problem_correction

def run_correction_workflow(pddl_problem, llm):
    """
    Run the correction workflow using correct_pddl and return a structured result.
    """
    try:
        corrected_pddl, is_domain, is_problem = correct_pddl(pddl_problem, llm)

        return {
            "success": True,
            "corrected_pddl": corrected_pddl,
            "is_domain_correction": is_domain,
            "is_problem_correction": is_problem
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "corrected_pddl": None,
            "is_domain_correction": False,
            "is_problem_correction": False
        }

def update_lore_with_corrections(richieste_utente, llm):
    """
    Send user requests to the LLM to update the generated lore JSON, save it locally.
    """
    lore = {json.dumps(load_example_json("file_generati/lore_generata_per_utente.json"), indent=2, ensure_ascii=False)}

    prompt = f"""Sei un esperto game designer specializzato nella creazione di avventure narrative interattive per il sistema QuestMaster.

    Il tuo compito è correggere una lore dettagliata in formato JSON, a partire dalle modifiche richieste dell'utente.

    ISTRUZIONI:
    - Devi limitarti a correggere la lore esistente con le modifiche richieste, senza modificarne la struttura, quindi il formato JSON deve rimanere identico.
    - Rispondi SOLO con il JSON valido
    - Non aggiungere testo prima o dopo il JSON
    - Assicurati che la struttura sia identica all'esempio fornito

    LORE DA MODIFICARE:
    {lore}
    MODIFICHE RICHIESTE DALL'UTENTE:
    {richieste_utente}
    """

    response = llm.invoke(prompt)

    response_text = response.content.strip()

    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.rfind("```")
        json_text = response_text[json_start:json_end].strip()
    elif response_text.startswith("{"):
        json_text = response_text
    else:
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx != -1 and end_idx != 0:
            json_text = response_text[start_idx:end_idx]
        else:
            json_text = response_text

    try:
        lore_data = json.loads(json_text)

        output_filename = "file_generati/lore_generata_per_utente.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(lore_data, f, indent=2, ensure_ascii=False)

        print(f"Lore saved to: {output_filename}")

        if "quest_description" in lore_data:
            print(f"\nTitle: {lore_data['quest_description'].get('title', 'N/A')}")
            print(f"Description: {lore_data['quest_description'].get('description', 'N/A')[:150]}...")

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response received:\n{response_text}")


def run_user_correction_pddl(user_corrections, llm):
    """
    Regenerate both domain and problem PDDL using the LLM based on user corrections.
    Saves files and returns the new contents on success.
    """
    try:
        lore = load_example_json("file_generati/lore_generata_per_utente.json")
        domain = load_example_pddl("file_generati/domain_generato.pddl")
        problem = load_example_pddl("file_generati/problem_generato.pddl")

        solution = ""
        try:
            with open("sas_plan", 'r', encoding='utf-8') as f:
                solution = f.read().strip()
        except FileNotFoundError:
            solution = "Solution not available"

        unified_prompt = f"""Sei un esperto di pianificazione automatica e PDDL (Planning Domain Definition Language).

        L'utente ha visto il piano generato (ovvero, la SOLUZIONE ATTUALE) e ha suggerito le seguenti correzioni/modifiche:
        "{user_corrections}"

        SOLUZIONE ATTUALE:
        {solution}

        LORE:
        {lore}

        domain.pddl ATTUALE:
        {domain}

        problem.pddl ATTUALE:
        {problem}

        Il tuo compito è rigenerare completamente ENTRAMBI i file domain.pddl e problem.pddl tenendo conto dei suggerimenti dell'utente.

        ISTRUZIONI:
        1. Analizza i suggerimenti dell'utente relativi al piano
        2. Rigenera il domain.pddl dalla lore incorporando le modifiche necessarie
        3. Rigenera il problem.pddl dalla lore incorporando le modifiche necessarie
        4. Assicurati che le azioni siano coerenti con i feedback dell'utente
        5. Assicurati che stati iniziali e goal siano coerenti con i feedback dell'utente
        6. Mantieni la coerenza tra domain e problem
        7. Mantieni la coerenza con la lore fornita

        OUTPUT:
        Fornisci il codice PDDL completo nel seguente formato:

        ===DOMAIN===
        [inserisci qui il codice PDDL del domain completo]

        ===PROBLEM===
        [inserisci qui il codice PDDL del problem completo]

        Non aggiungere commenti aggiuntivi, solo il codice PDDL pulito.
        """

        unified_response = llm.invoke(unified_prompt)
        response_content = unified_response.content.strip()

        def extract_pddl_from_markdown(content):
            """Extract PDDL content from markdown code blocks (```pddl or ```)."""
            if "```pddl" in content:
                parts = content.split("```pddl")
                if len(parts) >= 2:
                    pddl_content = parts[1].split("```")[0].strip()
                    return pddl_content
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 3:
                    return parts[1].strip()
            return content.strip()

        if "===DOMAIN===" in response_content and "===PROBLEM===" in response_content:
            domain_start = response_content.find("===DOMAIN===")
            problem_start = response_content.find("===PROBLEM===")

            if domain_start != -1 and problem_start != -1 and domain_start < problem_start:
                domain_section = response_content[domain_start + len("===DOMAIN==="):problem_start].strip()
                problem_section = response_content[problem_start + len("===PROBLEM==="):].strip()

                domain_content = extract_pddl_from_markdown(domain_section)
                problem_content = extract_pddl_from_markdown(problem_section)

                if not domain_content or not problem_content:
                    raise ValueError("Extracted PDDL content is empty")
            else:
                raise ValueError("Invalid response format: ===DOMAIN=== and ===PROBLEM=== not found in correct order")
        else:
            raise ValueError("Invalid response format: missing ===DOMAIN=== and ===PROBLEM=== separators")

        domain_filename = "file_generati/domain_generato.pddl"
        with open(domain_filename, 'w', encoding='utf-8') as f:
            f.write(domain_content)
        print(f"Domain regenerated and saved to: {domain_filename}")

        problem_filename = "file_generati/problem_generato.pddl"
        with open(problem_filename, 'w', encoding='utf-8') as f:
            f.write(problem_content)
        print(f"Problem regenerated and saved to: {problem_filename}")

        return {
            "domain_content": domain_content,
            "problem_content": problem_content,
            "success": True
        }

    except Exception as e:
        print(f"Error regenerating based on user suggestions: {e}")
        return {
            "domain_content": None,
            "problem_content": None,
            "success": False,
            "error": str(e)
        }

def run_user_correction_workflow(user_corrections, llm):
    """
    Wrapper to run user correction workflow and return a normalized result dict.
    """
    try:
        result = run_user_correction_pddl(user_corrections, llm)

        if result["success"]:
            return {
                "success": True,
                "domain_content": result["domain_content"],
                "problem_content": result["problem_content"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "domain_content": None,
                "problem_content": None
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "domain_content": None,
            "problem_content": None
        }