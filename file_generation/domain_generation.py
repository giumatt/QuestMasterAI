from utils import load_example_json
from utils import load_example_pddl
import json


def create_domain_pddl(llm):
    """
    Use the LLM to generate a domain.pddl file from the generated lore JSON and save it.
    """
    esempio_domain_pddl = load_example_pddl("file_esempio/domain.pddl")

    # Prompt for generating PDDL domain (kept as-is for the LLM)
    pddl_prompt = f"""Sei un esperto di pianificazione automatica e PDDL (Planning Domain Definition Language).

    Il tuo compito è convertire una lore in formato JSON in un file domain.pddl valido per Fast Downward.

    REQUISITI PER IL DOMAIN.PDDL:
    - Deve essere **pieno PDDL-STRIPS**, compatibile con Fast Downward (nessuna estensione numerica, temporale o fluents)
    - Includi predicati per rappresentare stati del mondo, posizioni, oggetti, condizioni
    - Definisci azioni con precondizioni ed effetti chiari
    - Ogni azione deve avere parametri tipizzati se necessario
    - Usa commenti per spiegare ogni sezione
    - Rispetta i vincoli di branching factor e depth constraints della lore
    - Rispondi **soltanto** con il codice PDDL valido, senza testo introduttivo o spiegazioni esterne

    ISTRUZIONI:
    - Analizza la lore JSON e identifica: stati, oggetti, personaggi, azioni possibili
    - Crea predicati che rappresentino lo stato del mondo narrativo
    - Definisci azioni che corrispondano alle scelte del giocatore
    - Rispondi SOLO con il codice PDDL valido, senza testo aggiuntivo
    - Ogni riga deve avere un commento che spiega cosa fa
    - Non usare accenti, scrivi sia commenti che istruzioni senza accenti o caratteri speciali

    ESEMPIO DI INPUT E OUTPUT:

    Input JSON della lore:
    {json.dumps(load_example_json("file_esempio/loreDiProva.json"), indent=2, ensure_ascii=False)}

    Output domain.pddl:
    {esempio_domain_pddl}

    LORE JSON ATTUALE DA CONVERTIRE:
    {json.dumps(load_example_json("file_generati/lore_generata_per_utente.json"), indent=2, ensure_ascii=False)}

    OUTPUT DOMAIN.PDDL:"""


    # Generate the domain.pddl using the LLM
    pddl_response = llm.invoke(pddl_prompt)

    pddl_text = pddl_response.content.strip()

    if "```" in pddl_text:
        start_idx = pddl_text.find("```")
        if start_idx != -1:
            first_end = pddl_text.find("\n", start_idx)
            if first_end != -1:
                last_start = pddl_text.rfind("```")
                if last_start != start_idx:
                    pddl_text = pddl_text[first_end+1:last_start].strip()
    try:
        pddl_output_filename = "file_generati/domain_generato.pddl"
        with open(pddl_output_filename, 'w', encoding='utf-8') as f:
            f.write(pddl_text)

        print(f"Domain.pddl generated and saved to: {pddl_output_filename}")

    except Exception as e:
        print(f"Error saving domain.pddl: {e}")
        print(f"Response received:\n{pddl_text}")



