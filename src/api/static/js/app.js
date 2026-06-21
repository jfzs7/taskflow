/* ==========================================================================
   app.js - Logika kliencka aplikacji TaskFlow.
   Zaimplementowano obsługę żądań asynchronicznych (fetch API) do backendu
   FastAPI, dynamiczne renderowanie zadań, filtrowanie, sortowanie,
   obsługę okna modalnego oraz komunikaty powiadomień Toast.
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // --- Konfiguracja i Stan Aplikacji ---
    const API_URL = '/api/v1/tasks';
    let currentTasks = [];

    // --- Elementy DOM ---
    const listTodo = document.getElementById('list-todo');
    const listInProgress = document.getElementById('list-progress');
    const listDone = document.getElementById('list-done');
    
    const countTodo = document.getElementById('count-todo');
    const countInProgress = document.getElementById('count-progress');
    const countDone = document.getElementById('count-done');
    
    const statTodo = document.getElementById('stat-todo-count');
    const statProgress = document.getElementById('stat-progress-count');
    const statDone = document.getElementById('stat-done-count');
    const statTotal = document.getElementById('stat-total-count');
    
    const apiStatusDot = document.getElementById('api-status-dot');
    const apiStatusText = document.getElementById('api-status-text');
    
    // Elementy Modala
    const modal = document.getElementById('task-modal');
    const modalTitle = document.getElementById('modal-title');
    const taskForm = document.getElementById('task-form');
    const taskIdInput = document.getElementById('task-id');
    const taskTitleInput = document.getElementById('task-title');
    const taskDescInput = document.getElementById('task-description');
    const taskPrioritySelect = document.getElementById('task-priority');
    const taskStatusSelect = document.getElementById('task-status');
    const statusGroup = document.getElementById('status-group');
    
    // Przyciski i Filtry
    const btnNewTask = document.getElementById('btn-new-task');
    const btnCancel = document.getElementById('btn-cancel');
    const modalClose = document.getElementById('modal-close');
    const filterPriority = document.getElementById('filter-priority');
    const sortSelect = document.getElementById('sort-select');
    const searchInput = document.getElementById('search-input');

    // --- Obsługa Powiadomień Toast ---
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let icon = 'fa-circle-check';
        if (type === 'error') icon = 'fa-circle-exclamation';
        if (type === 'info') icon = 'fa-circle-info';
        
        toast.innerHTML = `
            <i class="fa-solid ${icon}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Animacja pojawienia
        setTimeout(() => toast.classList.add('active'), 10);
        
        // Usunięcie po 3 sekundach
        setTimeout(() => {
            toast.classList.remove('active');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // --- Sprawdzanie Stanu API (Health Check) ---
    async function checkApiHealth() {
        try {
            const res = await fetch('/health');
            const data = await res.json();
            if (data.status === 'healthy') {
                apiStatusDot.className = 'status-dot healthy';
                apiStatusText.textContent = 'API Online';
            } else {
                apiStatusDot.className = 'status-dot unhealthy';
                apiStatusText.textContent = 'API Error';
            }
        } catch (err) {
            apiStatusDot.className = 'status-dot unhealthy';
            apiStatusText.textContent = 'API Offline';
        }
    }

    // --- Pobieranie Zadań z API ---
    async function fetchTasks() {
        try {
            // Pobieramy do 100 zadań
            const res = await fetch(`${API_URL}/?per_page=100`);
            if (!res.ok) throw new Error('Błąd pobierania danych');
            
            const data = await res.json();
            currentTasks = data.tasks;
            renderBoard();
            updateStats();
        } catch (err) {
            console.error(err);
            showToast('Nie udało się pobrać zadań z serwera.', 'error');
        }
    }

    // --- Statystyki ---
    function updateStats() {
        const todo = currentTasks.filter(t => t.status === 'todo').length;
        const progress = currentTasks.filter(t => t.status === 'in_progress').length;
        const done = currentTasks.filter(t => t.status === 'done').length;
        const total = currentTasks.length;
        
        // Liczniki w kolumnach
        countTodo.textContent = todo;
        countInProgress.textContent = progress;
        countDone.textContent = done;
        
        // Karty statystyk
        statTodo.textContent = todo;
        statProgress.textContent = progress;
        statDone.textContent = done;
        statTotal.textContent = total;
    }

    // --- Filtrowanie i Sortowanie Zadań ---
    function getFilteredAndSortedTasks() {
        let tasks = [...currentTasks];
        
        // 1. Wyszukiwanie (tekst)
        const searchQuery = searchInput.value.toLowerCase().trim();
        if (searchQuery) {
            tasks = tasks.filter(t => 
                t.title.toLowerCase().includes(searchQuery) || 
                t.description.toLowerCase().includes(searchQuery)
            );
        }
        
        // 2. Filtrowanie priorytetu
        const priorityVal = filterPriority.value;
        if (priorityVal) {
            tasks = tasks.filter(t => t.priority === priorityVal);
        }
        
        // 3. Sortowanie
        const [sortField, sortOrder] = sortSelect.value.split('-');
        tasks.sort((a, b) => {
            let valA, valB;
            
            if (sortField === 'priority') {
                const priorityWeight = { 'low': 1, 'medium': 2, 'high': 3, 'critical': 4 };
                valA = priorityWeight[a.priority] || 0;
                valB = priorityWeight[b.priority] || 0;
            } else {
                valA = a[sortField];
                valB = b[sortField];
            }
            
            if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
            if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
            return 0;
        });
        
        return tasks;
    }

    // --- Renderowanie Kart Zadań ---
    function renderBoard() {
        // Czyszczenie kolumn
        listTodo.innerHTML = '';
        listInProgress.innerHTML = '';
        listDone.innerHTML = '';
        
        const filteredTasks = getFilteredAndSortedTasks();
        
        const columns = {
            'todo': listTodo,
            'in_progress': listInProgress,
            'done': listDone
        };
        
        filteredTasks.forEach(task => {
            const col = columns[task.status];
            if (col) {
                const card = createTaskCard(task);
                col.appendChild(card);
            }
        });
        
        // Puste stany
        Object.keys(columns).forEach(status => {
            const col = columns[status];
            if (col.children.length === 0) {
                col.innerHTML = '<div class="empty-state">Brak zadań w tej kolumnie</div>';
            }
        });
    }

    function createTaskCard(task) {
        const card = document.createElement('div');
        card.className = `task-card priority-${task.priority}`;
        card.setAttribute('draggable', 'true');
        card.setAttribute('data-id', task.id);
        
        const priorityLabel = {
            'low': 'Niski',
            'medium': 'Średni',
            'high': 'Wysoki',
            'critical': 'Krytyczny'
        };
        
        card.innerHTML = `
            <div class="task-card-header">
                <span class="task-card-title">${escapeHTML(task.title)}</span>
                <span class="priority-tag ${task.priority}">${priorityLabel[task.priority]}</span>
            </div>
            <div class="task-card-body">${escapeHTML(task.description || 'Brak opisu.')}</div>
            <div class="task-card-footer">
                <span>ID: #${task.id}</span>
                <div class="task-actions">
                    <button class="btn-icon edit-btn" title="Edytuj"><i class="fa-solid fa-pen-to-square"></i></button>
                    <button class="btn-icon delete-btn delete" title="Usuń"><i class="fa-solid fa-trash"></i></button>
                </div>
            </div>
        `;
        
        // --- Zdarzenia dla przycisków wewnątrz karty ---
        card.querySelector('.edit-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            openEditModal(task);
        });
        
        card.querySelector('.delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteTask(task.id);
        });
        
        // --- Wsparcie dla Drag and Drop ---
        card.addEventListener('dragstart', (e) => {
            card.classList.add('dragging');
            e.dataTransfer.setData('text/plain', task.id);
        });
        
        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
        });
        
        return card;
    }

    // --- Bezpieczne parsowanie HTML ---
    function escapeHTML(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // --- Obsługa Zdarzeń Drag and Drop na Kolumnach ---
    const columns = document.querySelectorAll('.task-list');
    columns.forEach(col => {
        col.addEventListener('dragover', (e) => {
            e.preventDefault();
            const draggingCard = document.querySelector('.dragging');
            if (draggingCard) {
                col.appendChild(draggingCard);
            }
        });
        
        col.addEventListener('drop', async (e) => {
            e.preventDefault();
            const taskId = e.dataTransfer.getData('text/plain');
            const targetStatus = col.id.replace('list-', '').replace('progress', 'in_progress');
            
            const task = currentTasks.find(t => t.id == taskId);
            if (task && task.status !== targetStatus) {
                await updateTaskStatus(taskId, targetStatus);
            }
        });
    });

    // --- Aktualizacja Statusu (Drag and Drop / Szybka zmiana) ---
    async function updateTaskStatus(id, newStatus) {
        try {
            const res = await fetch(`${API_URL}/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });
            
            if (!res.ok) throw new Error('Błąd aktualizacji statusu');
            
            const updated = await res.json();
            
            // Aktualizacja stanu lokalnego
            const index = currentTasks.findIndex(t => t.id == id);
            if (index !== -1) {
                currentTasks[index] = updated;
            }
            
            updateStats();
            renderBoard();
            showToast('Zmieniono status zadania.', 'info');
        } catch (err) {
            console.error(err);
            showToast('Nie udało się zmienić statusu.', 'error');
            fetchTasks(); // Przywrócenie stanu z serwera w razie błędu
        }
    }

    // --- Okno Modalne ---
    function openCreateModal() {
        modalTitle.textContent = 'Dodaj nowe zadanie';
        taskIdInput.value = '';
        taskTitleInput.value = '';
        taskDescInput.value = '';
        taskPrioritySelect.value = 'medium';
        statusGroup.style.display = 'none';
        
        modal.classList.add('active');
    }

    function openEditModal(task) {
        modalTitle.textContent = 'Edytuj zadanie';
        taskIdInput.value = task.id;
        taskTitleInput.value = task.title;
        taskDescInput.value = task.description || '';
        taskPrioritySelect.value = task.priority;
        taskStatusSelect.value = task.status;
        statusGroup.style.display = 'block';
        
        modal.classList.add('active');
    }

    function closeModal() {
        modal.classList.remove('active');
        taskForm.reset();
    }

    // --- Zapisywanie Zadania (Dodawanie / Edycja) ---
    taskForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const id = taskIdInput.value;
        const payload = {
            title: taskTitleInput.value.trim(),
            description: taskDescInput.value.trim(),
            priority: taskPrioritySelect.value
        };
        
        if (id) {
            payload.status = taskStatusSelect.value;
        }

        try {
            let res;
            if (id) {
                // Edycja (PATCH)
                res = await fetch(`${API_URL}/${id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } else {
                // Nowe zadanie (POST)
                res = await fetch(`${API_URL}/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            if (!res.ok) throw new Error('Nie udało się zapisać zadania');

            showToast(id ? 'Zaktualizowano zadanie pomyślnie!' : 'Dodano nowe zadanie pomyślnie!');
            closeModal();
            fetchTasks();
        } catch (err) {
            console.error(err);
            showToast('Błąd podczas zapisywania zadania.', 'error');
        }
    });

    // --- Usuwanie Zadania ---
    async function deleteTask(id) {
        if (!confirm('Czy na pewno chcesz usunąć to zadanie?')) return;
        
        try {
            const res = await fetch(`${API_URL}/${id}`, {
                method: 'DELETE'
            });
            
            if (!res.ok) throw new Error('Błąd usuwania zadania');
            
            showToast('Zadanie zostało usunięte (zarchiwizowane).');
            fetchTasks();
        } catch (err) {
            console.error(err);
            showToast('Nie udało się usunąć zadania.', 'error');
        }
    }

    // --- Obsługa Zdarzeń Kontrolek ---
    btnNewTask.addEventListener('click', openCreateModal);
    btnCancel.addEventListener('click', closeModal);
    modalClose.addEventListener('click', closeModal);
    
    // Kliknięcie poza okno zamyka modal
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    
    // Zdarzenia filtrów
    filterPriority.addEventListener('change', renderBoard);
    sortSelect.addEventListener('change', renderBoard);
    searchInput.addEventListener('input', renderBoard);

    // --- Inicjalizacja Aplikacji ---
    checkApiHealth();
    fetchTasks();
    
    // Cykliczny health check co 30 sekund
    setInterval(checkApiHealth, 30000);
});
