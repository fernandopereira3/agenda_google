/* theme.js — Simples Sistema
   Gerencia tema claro/escuro. Padrão: claro (institucional).
   Persiste a preferência do usuário em localStorage. */

(function () {
    'use strict';

    const STORAGE_KEY = 'simples-theme';
    const DARK_CLASS  = 'dark-theme';

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add(DARK_CLASS);
        } else {
            document.documentElement.classList.remove(DARK_CLASS);
        }
    }

    function getSavedTheme() {
        try { return localStorage.getItem(STORAGE_KEY); } catch { return null; }
    }

    function saveTheme(theme) {
        try { localStorage.setItem(STORAGE_KEY, theme); } catch { /* noop */ }
    }

    /* Aplica tema salvo (ou padrão claro) antes do render para evitar flash */
    const saved = getSavedTheme();
    applyTheme(saved || 'light');

    /* Expõe função global para o botão de alternância, se existir */
    window.toggleTheme = function () {
        const isDark = document.documentElement.classList.contains(DARK_CLASS);
        const next   = isDark ? 'light' : 'dark';
        applyTheme(next);
        saveTheme(next);
    };
}());
