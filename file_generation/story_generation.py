from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
import os
import json
from utils import load_example_json, load_example_pddl

def generate_story(llm):
    example_story_json = load_example_json("file_esempio/json_storia_esempio.json")

    lore_example_story_json = load_example_json("file_esempio/lore_storia_esempio.json")
    
    with open("file_esempio/piano_sas_example.txt", 'r') as f:
        piano_esempio = f.read()
    
    lore_da_usare=load_example_json("file_generati/lore_generata_per_utente.json")

    with open('sas_plan', 'r') as f:
        piano_da_usare = f.read()
        
    # Custom prompt
    prompt = f"""Sei un assistente esperto in progettazione di storie interattive guidate da pianificazione automatica (AI Planning) e narrazione ramificata.
    Ti fornisco i seguenti file:

    1. Il contenuto JSON con la lore e le regole narrative, che include:
    - Titolo e background della storia
    - Obiettivi, ostacoli e contesto
    - Il numero minimo e massimo di azioni per completare la storia (depth_constraints)
    - Il numero minimo e massimo di scelte per nodo (branching_factor)

    2. Un piano PDDL corretto generato a partire da un domain e problem PDDL associati alla lore
    
    Obiettivo:
    Genera un **file JSON** che rappresenti una storia interattiva ramificata coerente con:
    - La **lore** fornita
    - Il **piano corretto** (che rappresenta la sequenza esatta di azioni da seguire)
    
    Requisiti
    1. **Struttura del JSON**:
    - Ogni nodo deve contenere:
        - `node_id`: identificatore univoco
        - `description`: testo immersivo e coerente con il mondo della storia
        - `choices`: tante quanto serve per rispettare branching_factor della lore
    - Solo una scelta è corretta (`is_correct: true`) e segue il piano
    - Le scelte errate portano a 1 nodo intermedio e poi a un nodo `game_over`
    - PER OGNI SCELTA IN "choices" il rispettivo "next_node" deve essere creato ed esistere con la sua funzionalita (nodo di fallimento o meno che sia) 

    2. **Percorsi Sbagliati**:
    - Ogni scelta errata deve sfociare in un ramo di fallimento con 2 nodi intermedi. 

    3. **Scelte**:
    - Ogni nodo deve avere tra tante opzioni coerente con `min_actions_per_state` e `max_actions_per_state` della lore

    4. **Numero di passi**:
    - Il percorso corretto (il piano) deve avere un numero di passi coerente con `depth_constraints` della lore

    5. **Narrativa**:
    - Ogni `description` deve usare toni coerenti con la storia

    Assicurati che il risultato sia coerente, ben scritto e pronto per essere utilizzato in un'applicazione web interattiva.

    -----ESEMPIO-----
    LORE DI INPUT: {lore_example_story_json}
    PIANO DI INPUT: {piano_esempio}
    OUTPUT: {example_story_json}
    ----FINE ESEMPIO----

    genera per questi:
    Lore: {lore_da_usare}
    piano: {piano_da_usare}
    output: 
    """

    # Generate the story via LLM
    try:
        response = llm.invoke(prompt)
    except Exception as e:
        print(f"Error generating story: {e}")

    response_text = response.content.strip()

    # Prova a estrarre il JSON dalla risposta
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.rfind("```")
        json_text = response_text[json_start:json_end].strip()
    elif response_text.startswith("{"):
        json_text = response_text
    else:
        # Cerca il primo { e l'ultimo }
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx != -1 and end_idx != 0:
            json_text = response_text[start_idx:end_idx]
        else:
            json_text = response_text

    try:
        lore_data = json.loads(json_text)
        output_filename = "file_generati/storia_generata.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(lore_data, f, indent=2, ensure_ascii=False)

        print(f"Story generated and saved to: {output_filename}")

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response received:\n{response_text}")