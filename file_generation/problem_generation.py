from utils import load_example_json
from utils import load_example_pddl
import json


def create_problem_pddl(llm):

    lore_esempio_json = load_example_json("file_esempio/loreDiProva.json")
    user_lore_json = load_example_json("file_generati/lore_generata_per_utente.json")

    # Prompt for generating the PDDL problem (kept as-is for the LLM)
    problem_prompt = f"""Sei un esperto di pianificazione automatica e PDDL (Planning Domain Definition Language).

    Il tuo compito è creare un file problem.pddl che sia compatibile col domain.pddl generato e che rappresenti lo scenario specifico della lore.

    REQUISITI PER IL PROBLEM.PDDL:
    - Deve essere pieno PDDL‑STRIPS, compatibile con Fast Downward (solo costrutti booleani, no numerici, no durative)
    - Deve essere compatibile con Fast Downward
    - Deve usare gli stessi predicati e oggetti definiti nel domain
    - Definisci gli objects specifici per questa istanza del problema
    - Imposta lo stato iniziale (:init) basato sulla lore
    - Definisci il goal basato sull'obiettivo della quest
    - Usa la sintassi PDDL standard: (define (problem nome-problema) ...)
    - Includi: problem name, domain reference, objects, init, goal
    - Ogni riga deve avere un commento che spiega cosa fa
    - Non usare accenti, scrivi sia commenti che istruzioni senza accenti o caratteri speciali


    ESEMPIO DI INPUT E OUTPUT:

    Input JSON della lore:
    {json.dumps(lore_esempio_json, indent=2, ensure_ascii=False)}

    Domain.pddl di riferimento:
    {load_example_pddl("file_esempio/domain.pddl")}

    Output problem.pddl di esempio:
    {load_example_pddl("file_esempio/problem.pddl")}

    LORE JSON ATTUALE DA CONVERTIRE:
    {json.dumps(user_lore_json, indent=2, ensure_ascii=False)}

    DOMAIN.PDDL GENERATO:
    {load_example_pddl("file_generati/domain_generato.pddl")}

    OUTPUT PROBLEM.PDDL:"""


    # Generate the problem.pddl
    problem_response = llm.invoke(problem_prompt)

    problem_text = problem_response.content.strip()

    if "```" in problem_text:
        start_idx = problem_text.find("```")
        if start_idx != -1:
            first_end = problem_text.find("\n", start_idx)
            if first_end != -1:
                last_start = problem_text.rfind("```")
                if last_start != start_idx:
                    problem_text = problem_text[first_end+1:last_start].strip()

    try:
        problem_output_filename = "file_generati/problem_generato.pddl"
        with open(problem_output_filename, 'w', encoding='utf-8') as f:
            f.write(problem_text)

        print(f"Problem.pddl generated and saved to: {problem_output_filename}")

    except Exception as e:
        print(f"Error saving problem.pddl: {e}")
        print(f"Response received:\n{problem_text}")
