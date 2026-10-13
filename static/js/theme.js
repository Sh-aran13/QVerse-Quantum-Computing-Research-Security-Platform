/**
 * QVerse Theme & Workspace Mode Manager
 */

export function initTheme() {
    const savedTheme = localStorage.getItem('qverse_theme') || 'dark';
    setTheme(savedTheme);

    const savedWorkspace = localStorage.getItem('qverse_workspace') || 'dashboard';
    setWorkspace(savedWorkspace);
}

export function setTheme(theme) {
    if (theme === 'system') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    } else {
        document.documentElement.setAttribute('data-theme', theme);
    }
    localStorage.setItem('qverse_theme', theme);
    
    // Update theme toggle UI if present
    document.querySelectorAll('[data-theme-choice]').forEach(el => {
        el.classList.toggle('active', el.getAttribute('data-theme-choice') === theme);
    });
}

export function setWorkspace(mode) {
    document.body.setAttribute('data-workspace', mode);
    localStorage.setItem('qverse_workspace', mode);

    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-mode') === mode);
    });
}

window.addEventListener('DOMContentLoaded', () => {
    initTheme();

    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const mode = e.target.getAttribute('data-mode');
            if (mode) setWorkspace(mode);
        });
    });

    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
        btn.addEventListener('click', () => {
            const current = localStorage.getItem('qverse_theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            setTheme(next);
        });
    });
});
