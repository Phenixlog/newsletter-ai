document.addEventListener('DOMContentLoaded', () => {
    const archiveList = document.getElementById('archive-list');
    const viewer = document.getElementById('newsletter-viewer');
    const runBtn = document.getElementById('run-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const logo = document.querySelector('.logo');
    const toast = document.getElementById('toast');

    let currentId = null;

    // --- Navigation ---

    function goHome() {
        currentId = null;
        updateActiveState();
        viewer.classList.add('empty');
        viewer.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 80px; margin-bottom: 20px; filter: drop-shadow(0 0 10px rgba(124, 58, 237, 0.5));">🚀</div>
                <h3>Bienvenue dans le cockpit</h3>
                <p>Choisissez une archive à gauche ou lancez une nouvelle veille pour commencer.</p>
            </div>
        `;
        document.getElementById('main-title').textContent = "Sélectionnez une newsletter";
        document.getElementById('date-range').textContent = "---";
        document.getElementById('week-badge').textContent = "Semaine -";
    }

    // --- API Calls ---

    async function fetchArchives() {
        try {
            const response = await fetch('/api/news');
            const data = await response.json();
            renderArchiveList(data.files);
        } catch (err) {
            showToast("Erreur lors de la récupération des archives");
        }
    }

    async function loadNewsletter(id) {
        try {
            const response = await fetch(`/api/news/${id}`);
            const data = await response.json();
            renderNewsletter(data);
            currentId = id;
            updateActiveState();
        } catch (err) {
            showToast("Erreur lors du chargement du contenu");
        }
    }

    async function triggerRun() {
        try {
            runBtn.disabled = true;
            runBtn.innerHTML = '<span class="icon">⌛</span> En cours...';

            const response = await fetch('/api/run', { method: 'POST' });
            const data = await response.json();

            showToast("Veille lancée ! Vérifez vos emails dans ~2 min.");

            setTimeout(() => {
                fetchArchives();
                runBtn.disabled = false;
                runBtn.innerHTML = '<span class="icon">🚀</span> Lancer une Veille';
            }, 10000);
        } catch (err) {
            showToast("Erreur lors du lancement");
            runBtn.disabled = false;
        }
    }

    // --- Rendering ---

    function renderArchiveList(items) {
        if (!items || items.length === 0) {
            archiveList.innerHTML = '<li class="empty">Aucune archive</li>';
            return;
        }

        archiveList.innerHTML = items.map(item => `
            <li class="archive-item" data-id="${item.id}">
                📅 ${item.display_date}
            </li>
        `).join('');

        document.querySelectorAll('.archive-item').forEach(el => {
            el.addEventListener('click', () => loadNewsletter(el.dataset.id));
        });
    }

    function renderNewsletter(data) {
        viewer.classList.remove('empty');

        document.getElementById('week-badge').textContent = `Semaine ${data.week_number}`;
        document.getElementById('main-title').textContent = data.highlight.name;
        document.getElementById('date-range').textContent = `Période : ${data.date_start} au ${data.date_end}`;

        viewer.innerHTML = `
            <div class="newsletter-card highlight">
                <span class="section-label">🔥 Game Changer</span>
                <h3 class="highlight-title"><a href="${data.highlight.url}" target="_blank" class="news-link">${data.highlight.name} ↗</a></h3>
                <p class="desc">${data.highlight.description}</p>
                <div class="so-what">
                    <strong>Impact Business :</strong> ${data.highlight.so_what}
                </div>
            </div>

            <div class="news-grid">
                <div class="sub-card">
                    <span class="section-label">🇫🇷 Focus France</span>
                    ${data.france_news.map(n => `
                        <div class="news-item">
                            <h4><a href="${n.url}" target="_blank" class="news-link">${n.name} ↗</a></h4>
                            <p class="desc-small">${n.description}</p>
                            <div class="action-tip">🎯 ${n.application}</div>
                        </div>
                        <hr style="margin: 15px 0; opacity: 0.1">
                    `).join('')}
                </div>

                <div class="sub-card">
                    <span class="section-label">🌍 Radar International</span>
                    ${data.international_news.map(n => `
                        <div class="news-item">
                            <h4><a href="${n.url}" target="_blank" class="news-link">${n.name} ↗</a></h4>
                            <p class="desc-small">${n.description}</p>
                        </div>
                        <hr style="margin: 15px 0; opacity: 0.1">
                    `).join('')}
                </div>
            </div>

            <div class="newsletter-card tool" style="margin-top: 24px;">
                <span class="section-label">🛠️ Outil de la semaine</span>
                <h3><a href="${data.tool_of_the_week.url}" target="_blank" class="news-link">${data.tool_of_the_week.name} ↗</a></h3>
                <p class="desc">${data.tool_of_the_week.description}</p>
                <div class="action-tip">💡 Cas d'usage : ${data.tool_of_the_week.application}</div>
            </div>

            <div class="takeaway-box">
                " ${data.take_away} "
            </div>
        `;
    }

    // --- Utilities ---

    function showToast(msg) {
        toast.textContent = msg;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 3000);
    }

    function updateActiveState() {
        document.querySelectorAll('.archive-item').forEach(item => {
            item.classList.toggle('active', item.dataset.id == currentId);
        });
    }

    // --- Event Listeners ---

    runBtn.addEventListener('click', triggerRun);
    refreshBtn.addEventListener('click', fetchArchives);
    logo.addEventListener('click', goHome);
    logo.style.cursor = 'pointer';

    // Initial Load
    fetchArchives();
});
