# QuestMasterAI

QuestMasterAI is an automated interactive narrative adventure generation system powered by Artificial Intelligence and automated planning (PDDL). Starting from a simple textual description provided by the user, the system generates a complete lore, translates it into a formal planning problem, validates it, and produces a playable interactive story accessible via browser.

---

## Main Features

- **AI-Powered Lore Generation** — From a natural language input, an LLM (Google Gemini) generates the quest lore in a structured JSON format
- **RAG (Retrieval-Augmented Generation)** — Ability to enrich generation with reference PDF documents through FAISS and embeddings
- **Prompt Injection Protection** — Automatic detection of suspicious patterns in user input
- **Automatic PDDL Generation** — Creation of Domain and Problem PDDL files consistent with the generated lore
- **Automated Validation and Correction** — Validation pipeline using [Fast Downward](https://www.fast-downward.org/) and [VAL](https://github.com/KCL-Planning/VAL), with a reflective agent for automatic error correction
- **Human-in-the-Loop** — Users can review and modify both the lore and the generated plan before story creation
- **Interactive Story Generation** — Production of a branching story in JSON format with correct paths and failure paths
- **Web Interface (Flask)** — Full web application for adventure creation and gameplay

---

## Project Architecture

```
QuestMasterAI/
├── main.py                          # CLI entry point
├── run_flask.py                     # Flask web application entry point
├── utils.py                         # Utility functions (file loading, lore/plan printing)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
│
├── file_generation/                 # Generation modules
│   ├── lore_generation.py           # Lore generation (with RAG)
│   ├── domain_generation.py         # PDDL Domain generation
│   ├── problem_generation.py        # PDDL Problem generation
│   └── story_generation.py          # Interactive story generation
│
├── correction_and_validation/       # PDDL validation and correction
│   ├── pddl_validation.py           # Validation with Fast Downward + VAL
│   └── reflective_agent.py          # Reflective agent for automatic correction
│
├── flask_app/                       # Web Application
│   ├── app.py                       # Flask server with REST API
│   ├── static/                      # Static files (CSS, JS)
│   └── templates/                   # HTML templates
│
├── file_esempio/                    # Example files
│   ├── domain.pddl                  # Example PDDL domain
│   ├── problem.pddl                 # Example PDDL problem
│   ├── loreDiProva.json             # Example lore JSON
│   ├── lore_storia_esempio.json     # Example lore for story generation
│   ├── json_storia_esempio.json     # Example generated interactive story
│   ├── piano_sas_example.txt        # Example SAS plan
│   └── documento_aiuto_RAG.pdf      # PDF document for the RAG system
│
└── LICENSE                          # MIT License
```

---

## Generation Pipeline

```
User Input --> Lore Generation (LLM + RAG) --> Lore Review (HITL)
                                                      |
                                                      v
                                          PDDL Domain Generation
                                          PDDL Problem Generation
                                                      |
                                                      v
                                      +--- Fast Downward Validation <--+
                                      |              |                  |
                                      |         (failure)               |
                                      |              v                  |
                                      |     Reflective Agent -----------+
                                      |       (correction)
                                      |
                                      +--> VAL Validation
                                                  |
                                             (success)
                                                  v
                                        Plan Review (HITL)
                                                  |
                                                  v
                                      Interactive Story Generation
                                                  |
                                                  v
                                              Gameplay
```

---

## Installation

### Prerequisites

- **Python 3.10+**
- **Google API Key** (for Google Gemini)
- **Fast Downward** (PDDL planner) — [Installation guide](https://www.fast-downward.org/ObtainingAndRunningFastDownward)
- **VAL** (PDDL validator) — [Repository](https://github.com/KCL-Planning/VAL)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/giumatt/QuestMasterAI.git
   cd QuestMasterAI
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   # or
   venv\Scripts\activate      # Windows

   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and fill in:
   - `GOOGLE_API_KEY` — your Google API key
   - `FAST_DOWNWARD_PATH` — path to the Fast Downward executable
   - `PDDL_DOMAIN_PATH` / `PDDL_PROBLEM_PATH` — paths for generated PDDL files
   - `VAL_PATH` — path to the VAL validator
   - `RAG_FILE` — path to the PDF for the RAG system (optional)

---

## Usage

### CLI Mode

```bash
python main.py
```

The CLI mode guides the user through all steps:
1. Enter the adventure description
2. Review and edit the generated lore
3. Automatic PDDL file generation and validation
4. Review the generated plan with the option to request corrections
5. Final interactive story generation

### Web Mode (Flask)

```bash
python run_flask.py
```

Open your browser at `http://localhost:5000` to access the web interface, which provides:
- **Creation** — Enter the adventure description
- **Lore Review** — View and approve the generated lore
- **Validation** — Automatic PDDL validation
- **Plan Review** — Inspect the generated plan
- **Gameplay** — Explore the interactive story directly in the browser with undo, reset, and node navigation

---

## Technologies Used

| Technology | Purpose |
|---|---|
| **Python** | Primary language |
| **LangChain** | LLM orchestration and RAG |
| **Google Gemini** | LLM model for generation |
| **FAISS** | Vector store for semantic search (RAG) |
| **PDDL** | Automated planning language |
| **Fast Downward** | PDDL planner |
| **VAL** | PDDL plan validator |
| **Flask** | Web framework for the interface |
| **HTML/CSS/JS** | Web application frontend |

---

## REST API (Flask)

| Endpoint | Method | Description |
|---|---|---|
| `/api/generate_lore` | `POST` | Generate lore from user input |
| `/api/approve_lore` | `POST` | Approve the lore and generate PDDL files |
| `/api/validate_pddl` | `POST` | Run full validation (Fast Downward + VAL) |
| `/api/generate_story` | `POST` | Generate the final interactive story |
| `/api/game/load` | `GET` | Load the story for gameplay |
| `/api/game/make_choice` | `POST` | Record a player choice |
| `/api/game/undo` | `POST` | Undo the last choice |
| `/api/game/reset` | `POST` | Reset the game from the beginning |
| `/api/check_existing_story` | `GET` | Check if a previously generated story exists |
| `/api/load_existing_story` | `POST` | Load an existing story for gameplay |

---

## License

This project is released under the [LICENSE](https://github.com/giumatt/QuestMasterAI/blob/main/LICENSE).
