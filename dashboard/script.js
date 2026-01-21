/**
 * Newsletter Studio - Multi-Newsletter JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // ===================================
    // State
    // ===================================
    let activeNewsletterId = 'ia-hebdo';
    let newslettersConfig = [];
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
    const newsletterSelect = document.getElementById('newsletter-select');

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
    async function fetchConfigs() {
        try {
            const res = await fetch('/api/config');
            const data = await res.json();
            newslettersConfig = data.newsletters || [];
            updateSwitcher();
            return newslettersConfig;
        } catch (err) {
            console.error('Failed to fetch configs:', err);
            return [];
        }
    }

    async function fetchArchives() {
        try {
            const res = await fetch(`/api/news?newsletter_id=${activeNewsletterId}`);
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

            const res = await fetch(`/api/run?newsletter_id=${activeNewsletterId}`, { method: 'POST' });
            showToast(`🚀 Génération de "${activeNewsletterId}" lancée...`);

            setTimeout(() => {
                runBtn.disabled = false;
                runBtn.innerHTML = '<span class="btn-icon">🚀</span><span>Lancer la Veille</span>';
                loadPageData(currentPage);
            }, 10000);
        } catch (err) {
            showToast('❌ Erreur lors du lancement');
            runBtn.disabled = false;
        }
    }

    // ===================================
    // UI Helpers
    // ===================================
    function updateSwitcher() {
        newsletterSelect.innerHTML = newslettersConfig.map(n => `
            <option value="${n.id}" ${n.id === activeNewsletterId ? 'selected' : ''}>
                ${n.name}
            </option>
        `).join('') + '<option value="new">+ Nouvelle Newsletter</option>';
    }

    newsletterSelect.addEventListener('change', () => {
        if (newsletterSelect.value === 'new') {
            activeNewsletterId = 'new';
            navigateTo('settings');
            prepareNewForm();
            return;
        }
        activeNewsletterId = newsletterSelect.value;
        loadPageData(currentPage);
        showToast(`Newsletter active : ${activeNewsletterId}`);
    });

    // ===================================
    // Page: Dashboard
    // ===================================
    async function loadDashboard() {
        const archives = await fetchArchives();
        const config = newslettersConfig.find(c => c.id === activeNewsletterId);

        document.getElementById('stat-newsletters').textContent = archives.length;
        document.getElementById('stat-recipients').textContent = config ? config.recipients.length : '-';

        const recentList = document.getElementById('recent-list');
        if (archives.length === 0) {
            recentList.innerHTML = '<li class="empty-state">Aucune archive pour cette newsletter</li>';
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
                    <p>Commencez par lancer une veille pour cette newsletter.</p>
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
    // Page: Recipients
    // ===================================
    function loadRecipients() {
        const config = newslettersConfig.find(c => c.id === activeNewsletterId);
        const list = document.getElementById('recipients-list');

        if (!config || !config.recipients.length) {
            list.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px;">Aucun destinataire configuré</td></tr>';
            return;
        }

        list.innerHTML = config.recipients.map((email, i) => `
            <tr>
                <td class="recipient-email">${email}</td>
                <td><span class="badge badge-group">Tous</span></td>
                <td><span class="badge badge-active">Actif</span></td>
                <td>
                    <button class="btn-icon-sm" data-email="${email}">🗑️</button>
                </td>
            </tr>
        `).join('');

        list.querySelectorAll('.btn-icon-sm').forEach(btn => {
            btn.addEventListener('click', async () => {
                const email = btn.dataset.email;
                config.recipients = config.recipients.filter(e => e !== email);
                await saveConfig(config);
                loadRecipients();
            });
        });
    }

    document.getElementById('add-recipient-btn')?.addEventListener('click', () => {
        document.getElementById('modal-add-recipient').classList.remove('hidden');
    });

    document.getElementById('save-recipient')?.addEventListener('click', async () => {
        const email = document.getElementById('new-email').value.trim();
        if (!email.includes('@')) return showToast('Email invalide');

        const config = newslettersConfig.find(c => c.id === activeNewsletterId);
        if (!config) return;

        config.recipients.push(email);
        await saveConfig(config);
        document.getElementById('modal-add-recipient').classList.add('hidden');
        document.getElementById('new-email').value = '';
        loadRecipients();
    });

    // ===================================
    // Page: Settings (Gestion)
    // ===================================
    function loadSettings() {
        const config = newslettersConfig.find(c => c.id === activeNewsletterId);
        if (!config) {
            if (activeNewsletterId === 'new') prepareNewForm();
            return;
        }

        document.getElementById('setting-theme').value = config.theme || '';
        document.getElementById('setting-tone').value = config.tone || 'professionnel';
        document.getElementById('setting-language').value = config.language || 'fr';
        document.getElementById('setting-sender-name').value = config.from_name || '';

        // Populate additional fields if we added them to UI
        const nameInput = document.getElementById('setting-name') || createExtraInput('Nom de la Newsletter', 'setting-name');
        nameInput.value = config.name;

        const idInput = document.getElementById('setting-id') || createExtraInput('ID (unique, sans espace)', 'setting-id');
        idInput.value = config.id;
        idInput.disabled = true;
    }

    function prepareNewForm() {
        activeNewsletterId = 'new';
        document.getElementById('setting-theme').value = '';
        document.getElementById('setting-sender-name').value = '';

        const nameInput = document.getElementById('setting-name') || createExtraInput('Nom de la Newsletter', 'setting-name');
        nameInput.value = '';

        const idInput = document.getElementById('setting-id') || createExtraInput('ID (unique, sans espace)', 'setting-id');
        idInput.value = '';
        idInput.disabled = false;

        showToast('Mode création : Nouvelle Newsletter');
    }

    function createExtraInput(label, id) {
        const group = document.createElement('div');
        group.className = 'form-group';
        group.innerHTML = `<label>${label}</label><input type="text" id="${id}">`;
        const container = document.querySelector('.settings-form');
        container.prepend(group);
        return document.getElementById(id);
    }

    document.getElementById('save-settings')?.addEventListener('click', async () => {
        const id = document.getElementById('setting-id')?.value || activeNewsletterId;
        const name = document.getElementById('setting-name')?.value || id;

        if (!id) return showToast('ID requis');

        const config = {
            id,
            name,
            description: `Newsletter sur ${name}`,
            theme: document.getElementById('setting-theme').value,
            keywords: document.getElementById('setting-theme').value.split(',').map(s => s.trim()),
            tone: document.getElementById('setting-tone').value,
            language: document.getElementById('setting-language').value,
            recipients: newslettersConfig.find(c => c.id === activeNewsletterId)?.recipients || [],
            from_name: document.getElementById('setting-sender-name').value,
            active: true
        };

        await saveConfig(config);
        showToast('✅ Configuration enregistrée');
        await fetchConfigs();
        activeNewsletterId = id;
        navigateTo('settings');
    });

    async function saveConfig(config) {
        try {
            await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
        } catch (err) {
            console.error('Save failed:', err);
        }
    }

    // ===================================
    // Init
    // ===================================
    async function init() {
        await fetchConfigs();
        if (newslettersConfig.length > 0) {
            activeNewsletterId = newslettersConfig[0].id;
        }
        navigateTo('dashboard');
    }

    // Global event for modal close
    document.querySelector('.modal-close')?.addEventListener('click', () => {
        document.getElementById('modal-add-recipient').classList.add('hidden');
    });

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
