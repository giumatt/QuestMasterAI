// JavaScript per l'applicazione Flask QuestMasterAI

class QuestMasterApp {
    constructor() {
        this.currentState = 'creation';
        this.storyData = null;
        this.currentNode = 'start';
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupMessageInput();
    }

    bindEvents() {
        // Event listeners per i bottoni
        document.addEventListener('click', (e) => {
            if (e.target.matches('#generate-lore-btn') || e.target.matches('#send-button')) {
                this.generateLore();
            } else if (e.target.matches('#load-existing-story-btn')) {
                this.showExistingStoryModal();
            } else if (e.target.matches('#close-modal-btn') || e.target.matches('#cancel-modal-btn')) {
                this.closeExistingStoryModal();
            } else if (e.target.matches('#continue-existing-story-btn')) {
                this.loadExistingStory();
            } else if (e.target.matches('#approve-lore-btn')) {
                this.approveLore();
            } else if (e.target.matches('#validate-pddl-btn')) {
                this.validatePDDL();
            } else if (e.target.matches('#continue-validation-btn')) {
                this.continueFromValidation();
            } else if (e.target.matches('#approve-plan-btn')) {
                this.approvePlan();
            } else if (e.target.matches('#generate-story-btn')) {
                this.generateStory();
            } else if (e.target.matches('#start-game-btn')) {
                this.startGame();
            } else if (e.target.matches('.choice-button')) {
                this.makeChoice(e.target);
            } else if (e.target.matches('#reset-game-btn')) {
                this.resetGame();
            }
        });
        
        // Chiudi modal cliccando sull'overlay
        document.addEventListener('click', (e) => {
            if (e.target.matches('.modal-overlay')) {
                this.closeExistingStoryModal();
            }
        });
    }

    setupMessageInput() {
        // Setup per l'input della fase di creazione
        const input = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-button');
        
        if (input && sendBtn) {
            // Auto-resize textarea
            input.addEventListener('input', () => {
                input.style.height = 'auto';
                input.style.height = input.scrollHeight + 'px';
                
                // Enable/disable send button
                sendBtn.disabled = !input.value.trim();
            });

            // Send on Enter (but not Shift+Enter)
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (input.value.trim()) {
                        this.generateLore();
                    }
                }
            });
        }
    }

    showLoading(message = 'Caricamento...') {
        const existingLoader = document.querySelector('.loading-overlay');
        if (existingLoader) {
            existingLoader.remove();
        }

        const loader = document.createElement('div');
        loader.className = 'loading-overlay';
        loader.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <p class="status-message status-loading">${message}</p>
            </div>
        `;
        loader.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        
        document.body.appendChild(loader);
    }

    hideLoading() {
        const loader = document.querySelector('.loading-overlay');
        if (loader) {
            loader.remove();
        }
    }

    showMessage(message, type = 'info') {
        const messageEl = document.createElement('div');
        messageEl.className = `status-message status-${type}`;
        messageEl.textContent = message;
        
        const container = document.querySelector('.creation-container, .validation-container, .story-container') || document.body;
        container.insertBefore(messageEl, container.firstChild);
        
        setTimeout(() => {
            messageEl.remove();
        }, 5000);
    }

    async showExistingStoryModal() {
        const modal = document.getElementById('existing-story-modal');
        const container = document.getElementById('story-preview-container');
        
        if (!modal || !container) return;
        
        // Mostra il modal
        modal.style.display = 'flex';
        
        // Carica i dettagli della storia
        try {
            const response = await fetch('/api/check_existing_story');
            const result = await response.json();
            
            if (result.success && result.has_story && result.story_preview) {
                const preview = result.story_preview;
                container.innerHTML = `
                    <div class="story-preview">
                        <h4>${preview.title}</h4>
                        
                        <div class="story-section">
                            <div class="story-label">Situazione Iniziale</div>
                            <p>${preview.initial_state}</p>
                        </div>
                        
                        <div class="story-section">
                            <div class="story-label">Inizio dell'avventura</div>
                            <p>${preview.description}</p>
                        </div>
                        
                        <div class="story-section">
                            <div class="story-label">Obiettivo</div>
                            <p>${preview.goal}</p>
                        </div>
                    </div>
                `;
            } else {
                container.innerHTML = '<p class="status-message status-error">Errore nel caricamento della storia</p>';
            }
        } catch (error) {
            container.innerHTML = `<p class="status-message status-error">Errore: ${error.message}</p>`;
        }
    }
    
    closeExistingStoryModal() {
        const modal = document.getElementById('existing-story-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    async loadExistingStory() {
        this.showLoading('Caricamento storia...');
        this.closeExistingStoryModal();
        
        try {
            const response = await fetch('/api/load_existing_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            this.hideLoading();
            
            if (result.success) {
                this.showMessage('Storia caricata con successo!', 'success');
                setTimeout(() => {
                    window.location.href = `/state/${result.next_state}`;
                }, 1000);
            } else {
                this.showMessage(`Errore: ${result.error}`, 'error');
            }
        } catch (error) {
            this.hideLoading();
            this.showMessage(`Errore: ${error.message}`, 'error');
        }
    }

    async generateLore() {
        const userInput = document.getElementById('message-input')?.value.trim() || 
                         document.getElementById('user-input')?.value.trim();

        if (!userInput) {
            this.showMessage('Inserisci una descrizione della tua avventura', 'error');
            return;
        }

        this.showLoading('Generando la lore della tua avventura...');

        try {
            const response = await fetch('/api/generate_lore', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_input: userInput
                })
            });

            const result = await response.json();
            this.hideLoading();

            if (result.success) {
                this.showMessage('Lore generata con successo!', 'success');
                setTimeout(() => {
                    window.location.href = `/state/${result.next_state}`;
                }, 1000);
            } else {
                this.showMessage(`Errore: ${result.error}`, 'error');
            }
        } catch (error) {
            this.hideLoading();
            this.showMessage(`Errore di connessione: ${error.message}`, 'error');
        }
    }

    async approveLore() {
        this.showLoading('Generando i file PDDL...');

        try {
            const response = await fetch('/api/approve_lore', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            const result = await response.json();
            this.hideLoading();

            if (result.success) {
                this.showMessage('File PDDL generati!', 'success');
                setTimeout(() => {
                    window.location.href = `/state/${result.next_state}`;
                }, 1000);
            } else {
                this.showMessage(`Errore: ${result.error}`, 'error');
            }
        } catch (error) {
            this.hideLoading();
            this.showMessage(`Errore: ${error.message}`, 'error');
        }
    }

    async validatePDDL() {
        this.showLoading('Validando i file PDDL...');

        try {
            // Mostra il container dei risultati
            const resultsContainer = document.getElementById('validation-results');
            const continueActions = document.getElementById('continue-actions');
            
            if (resultsContainer) {
                resultsContainer.style.display = 'block';
                resultsContainer.innerHTML = '<div class="progress-text">Validazione in corso...</div>';
            }

            const response = await fetch('/api/validate_pddl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            const result = await response.json();
            this.hideLoading();

            if (result.success) {
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="validation-item success">
                            <strong>✅ Validazione completata con successo!</strong>
                            <p>Tentativi necessari: ${result.results.attempts}</p>
                        </div>
                    `;
                }
                
                if (continueActions) {
                    continueActions.style.display = 'flex';
                }
                
                this.showMessage('Validazione completata!', 'success');
            } else {
                if (resultsContainer) {
                    let errorMessage = result.results ? result.results.error : result.error;
                    let suggestion = result.results ? result.results.suggestion : '';
                    
                    resultsContainer.innerHTML = `
                        <div class="validation-item error">
                            <strong>❌ Validazione fallita</strong>
                            <p>${errorMessage}</p>
                            ${suggestion ? `<p><strong>💡 Suggerimento:</strong> ${suggestion}</p>` : ''}
                            <p><em>Tentativi utilizzati: ${result.results ? result.results.attempts : 'N/A'}</em></p>
                        </div>
                    `;
                }
                
                this.showMessage('Validazione fallita. Controlla i suggerimenti.', 'error');
            }
        } catch (error) {
            this.hideLoading();
            
            const resultsContainer = document.getElementById('validation-results');
            if (resultsContainer) {
                resultsContainer.style.display = 'block';
                resultsContainer.innerHTML = `
                    <div class="validation-item error">
                        <strong>❌ Errore di connessione</strong>
                        <p>${error.message}</p>
                    </div>
                `;
            }
            
            this.showMessage(`Errore: ${error.message}`, 'error');
        }
    }

    async generateStory() {
        this.showLoading('Generando la storia interattiva...');

        try {
            const response = await fetch('/api/generate_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            const result = await response.json();
            this.hideLoading();

            if (result.success) {
                this.showMessage('Storia generata! Inizia la tua avventura!', 'success');
                setTimeout(() => {
                    window.location.href = `/state/${result.next_state}`;
                }, 1000);
            } else {
                this.showMessage(`Errore: ${result.error}`, 'error');
            }
        } catch (error) {
            this.hideLoading();
            this.showMessage(`Errore: ${error.message}`, 'error');
        }
    }

    async loadStory() {
        try {
            const response = await fetch('/api/game/load_story');
            const result = await response.json();

            if (result.success) {
                this.storyData = result.story;
                this.displayCurrentNode();
            } else {
                this.showMessage('Errore nel caricamento della storia', 'error');
            }
        } catch (error) {
            this.showMessage(`Errore: ${error.message}`, 'error');
        }
    }

    displayCurrentNode() {
        if (!this.storyData) return;

        const node = this.storyData.find(n => n.node_id === this.currentNode);
        if (!node) return;

        const storyContainer = document.getElementById('story-container');
        if (!storyContainer) return;

        let html = `<div class="story-text">${node.description}</div>`;

        if (node.choices && node.choices.length > 0) {
            html += '<div class="choices-container">';
            // Randomizza l'ordine delle scelte
            const randomizedChoices = this.shuffleArray([...node.choices]);
            randomizedChoices.forEach((choice, index) => {
                html += `
                    <button class="choice-button" 
                            data-next-node="${choice.next_node}" 
                            data-choice-text="${choice.text}">
                        ${this.getChoiceIcon(index)} ${choice.text}
                    </button>
                `;
            });
            html += '</div>';
        } else if (node.node_id === 'end') {
            html += `
                <div class="victory-container">
                    <h2 class="victory-title">🎉 AVVENTURA COMPLETATA! 🎉</h2>
                    <button id="reset-game-btn" class="btn-primary">Ricomincia Avventura</button>
                </div>
            `;
        }

        storyContainer.innerHTML = html;
    }

    getChoiceIcon(index) {
        const icons = ['⚔️', '🛡️', '🏺', '📜', '🗝️', '💎', '🌟', '🔮'];
        return icons[index % icons.length];
    }

    // Funzione per randomizzare l'ordine delle scelte
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    async makeChoice(button) {
        const nextNode = button.dataset.nextNode;
        const choiceText = button.dataset.choiceText;

        try {
            const response = await fetch('/api/game/make_choice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    next_node: nextNode,
                    choice_text: choiceText
                })
            });

            const result = await response.json();

            if (result.success) {
                this.currentNode = result.current_node;
                this.displayCurrentNode();
            } else {
                this.showMessage('Errore nella scelta', 'error');
            }
        } catch (error) {
            this.showMessage(`Errore: ${error.message}`, 'error');
        }
    }

    async continueFromValidation() {
        try {
            window.location.href = '/state/plan_review';
        } catch (error) {
            this.showMessage(`Errore: ${error.message}`, 'error');
        }
    }

    async approvePlan() {
        try {
            window.location.href = '/state/story_generation';
        } catch (error) {
            this.showMessage(`Errore: ${error.message}`, 'error');
        }
    }

    async startGame() {
        try {
            window.location.href = '/state/gameplay';
        } catch (error) {
            this.showMessage(`Errore: ${error.message}`, 'error');
        }
    }

    async resetGame() {
        try {
            const response = await fetch('/api/game/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (result.success) {
                this.currentNode = 'start';
                this.displayCurrentNode();
                this.showMessage('Gioco resettato!', 'success');
            } else {
                this.showMessage('Errore nel reset', 'error');
            }
        } catch (error) {
            this.showMessage(`Errore: ${error.message}`, 'error');
        }
    }
}

// Inizializza l'applicazione quando il DOM è carico
document.addEventListener('DOMContentLoaded', () => {
    window.questMasterApp = new QuestMasterApp();
    
    // Se siamo nella pagina di gameplay, carica la storia
    if (window.location.pathname.includes('gameplay')) {
        window.questMasterApp.loadStory();
    }
});
