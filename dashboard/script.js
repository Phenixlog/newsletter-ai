/**
 * Newsletter Studio - Stable Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // ===================================
    // State
    // ===================================
    let archiveItems = [];
    let currentPage = 'dashboard';

    // ===================================
    // DOM Elements
    // ===================================
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    const runBtn = document.getElementById('run-btn');
    const quickLaunch = document.getElementById('quick-launch');
    const toast = document.getElementById('toast');

    // ===================================
    // Navigation
    // ===================================
    function navigateTo(pageName) {
        navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.page === pageName);
        });

        pages.forEach(page => {
            page.classList.toggle('active', page.id === `page-${pageName}`);
        });

        currentPage = pageName;
        loadPageData(pageName);
    }

    function loadPageData(pageName) {
        if (pageName === 'dashboard') loadDashboard();
        if (pageName === 'newsletters') loadArchives();
        if (pageName === 'recipients') loadRecipients();
        if (pageName === 'settings') loadSettings();
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(item.dataset.page);
        });
    });

    // ===================================
    // API Interactions
    // ===================================
    async function fetchArchives() {
        try {
            const res = await fetch('/api/news');
            const data = await res.json();
            archiveItems = data.files || [];
            return archiveItems;
        } catch (err) {
            console.error('Failed to fetch archives:', err);
            return [];
        }
    }

    async function fetchArchiveContent(id) {
        try {
            const res = await fetch(`/api/news/${id}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch archive content:', err);
            return null;
        }
    }

    async function triggerRun() {
        try {
            runBtn.disabled = true;
            runBtn.innerHTML = '<span class="btn-icon">⏳</span><span>Génération...</span>';

            await fetch('/api/run', { method: 'POST' });
            showToast('🚀 Génération lancée en arrière-plan...');

            setTimeout(() => {
                runBtn.disabled = false;
                runBtn.innerHTML = '<span class="btn-icon">🚀</span><span>Lancer la Veille</span>';
                loadPageData(currentPage);
            }, 5000);
        } catch (err) {
            showToast('❌ Erreur lors du lancement');
            runBtn.disabled = false;
        }
    }

    // ===================================
    // Page: Dashboard
    // ===================================
    async function loadDashboard() {
        const archives = await fetchArchives();

        document.getElementById('stat-newsletters').textContent = archives.length;
        // Recipients stat is hardcoded for now or fetched from a simple endpoint if we had one
        document.getElementById('stat-recipients').textContent = '-';

        const recentList = document.getElementById('recent-list');
        if (archives.length === 0) {
            recentList.innerHTML = '<li class="empty-state">Aucune archive</li>';
            return;
        }

        recentList.innerHTML = archives.slice(0, 5).map(n => `
            <li data-id="${n.id}">
                <span>📅 Semaine ${n.week_number || '?'}</span>
                <span style="color: var(--text-muted)">${n.display_date}</span>
            </li>
        `).join('');

        recentList.querySelectorAll('li').forEach(li => {
            li.addEventListener('click', () => {
                navigateTo('newsletters');
                setTimeout(() => loadArchiveDetail(li.dataset.id), 100);
            });
        });
    }

    // ===================================
    // Page: Archives
    // ===================================
    async function loadArchives() {
        await fetchArchives();
        const archiveList = document.getElementById('archive-list');

        if (archiveItems.length === 0) {
            archiveList.innerHTML = '<li class="empty">Aucune archive</li>';
            document.getElementById('newsletter-viewer').innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📰</div>
                    <h3>Aucune archive</h3>
                    <p>Commencez par lancer une veille.</p>
                </div>
            `;
            return;
        }

        archiveList.innerHTML = archiveItems.map(n => `
            <li class="archive-item" data-id="${n.id}">
                📅 ${n.display_date} (Hb ${n.week_number})
            </li>
        `).join('');

        archiveList.querySelectorAll('.archive-item').forEach(item => {
            item.addEventListener('click', () => loadArchiveDetail(item.dataset.id));
        });
    }

    async function loadArchiveDetail(id) {
        const data = await fetchArchiveContent(id);
        if (!data) return;

        document.querySelectorAll('.archive-item').forEach(item => {
            item.classList.toggle('active', item.dataset.id == id);
        });

        const viewer = document.getElementById('newsletter-viewer');
        viewer.classList.remove('empty');

        viewer.innerHTML = `
            <div class="newsletter-card">
                <span class="section-label">🔥 Highlight</span>
                <h3 class="highlight-title">
                    <a href="${data.highlight.url}" target="_blank" class="news-link">${data.highlight.name} ↗</a>
                </h3>
                <p class="desc">${data.highlight.description}</p>
                <div class="so-what">
                    <strong>Impact Business :</strong> ${data.highlight.so_what}
                </div>
            </div>
            
            <div class="news-grid">
                <div class="sub-card">
                    <span class="section-label">📌 Section 1</span>
                    ${(data.france_news || []).map(n => `
                        <div style="margin-bottom: 16px;">
                            <h4><a href="${n.url}" target="_blank" class="news-link">${n.name} ↗</a></h4>
                            <p class="desc-small">${n.description}</p>
                        </div>
                    `).join('')}
                </div>
                <div class="sub-card">
                    <span class="section-label">🌍 Section 2</span>
                    ${(data.international_news || []).map(n => `
                        <div style="margin-bottom: 16px;">
                            <h4><a href="${n.url}" target="_blank" class="news-link">${n.name} ↗</a></h4>
                            <p class="desc-small">${n.description}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="newsletter-card" style="margin-top: 20px;">
                <span class="section-label">🛠️ Outil/Focus</span>
                <h3><a href="${data.tool_of_the_week.url}" target="_blank" class="news-link">${data.tool_of_the_week.name} ↗</a></h3>
                <p class="desc">${data.tool_of_the_week.description}</p>
            </div>
            
            <div class="takeaway-box">
                "${data.take_away}"
            </div>
        `;
    }

    // ===================================
    // Page: Recipients (Static for now)
    // ===================================
    function loadRecipients() {
        const list = document.getElementById('recipients-list');
        list.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px;">Gestion simplifiée : Modifiez TO_EMAIL dans les variables d\'environnement.</td></tr>';
    }

    // ===================================
    // Page: Settings
    // ===================================
    function loadSettings() {
        // Simple placeholders
        console.log('Settings page loaded');
    }

    // ===================================
    // Init
    // ===================================
    function init() {
        navigateTo('dashboard');
    }

    if (runBtn) runBtn.addEventListener('click', triggerRun);
    if (quickLaunch) quickLaunch.addEventListener('click', triggerRun);

    init();
});

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}
