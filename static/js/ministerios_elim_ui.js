// --- Analytics Helper ---

/**
 * Global helper to track events in Google Analytics 4.
 * @param {string} eventName 
 * @param {Object} params 
 */
function elimTrackEvent(eventName, params = {}) {
    // Intentionally local-only. Aggregate server metrics are recorded on
    // completed searches, church visits and doctrine progress without user IDs.
    return { eventName, params };
}

// --- Utility Functions ---

function showMessageModal(message, isSuccess = true) {
    const modalElement = document.getElementById('messageModal');
    const modalBody = document.getElementById('messageModalBody');
    const modalHeader = document.getElementById('messageModalHeader');

    if (!modalElement || !modalBody || !modalHeader) return;

    if (modalElement.hasAttribute('aria-hidden')) {
        modalElement.removeAttribute('aria-hidden');
    }

    modalBody.textContent = message;
    modalHeader.className = isSuccess ? 'modal-header bg-success text-white' : 'modal-header bg-danger text-white';

    const modal = new bootstrap.Modal(modalElement, {
        backdrop: 'static',
        keyboard: true
    });

    modal.show();

    modalElement.addEventListener('hidden.bs.modal', function () {
        modalElement.setAttribute('aria-hidden', 'true');
    }, { once: true });
}

function showSuccess(message) {
    if (message.toLowerCase().includes('éxito') || message.toLowerCase().includes('bienvenido')) {
        showWelcomeModal(message);
    } else {
        showMessageModal(message, true);
    }
}

function showError(message) {
    showMessageModal(message, false);
}

function showWelcomeModal(message) {
    const modalElement = document.getElementById('welcomeModal');
    const messageElement = document.getElementById('welcomeModalMessage');

    if (!modalElement || !messageElement) return;

    if (message) {
        messageElement.textContent = message;
    }

    const modal = new bootstrap.Modal(modalElement, {
        backdrop: 'static'
    });
    modal.show();
}

function togglePassword(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    if (!input || !icon) return;

    if (input.type === 'password') {
        input.type = 'text';
        icon.innerHTML = '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/><line x1="1" y1="1" x2="23" y2="23" stroke="#666" stroke-width="2"/>';
    } else {
        input.type = 'password';
        icon.innerHTML = '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>';
    }
}

function showForgotPassword() {
    const loginForm = document.getElementById('loginForm');
    const forgotForm = document.getElementById('forgotPasswordForm');
    if (loginForm) loginForm.style.display = 'none';
    if (forgotForm) forgotForm.style.display = 'block';
    elimTrackEvent('forgot_password_view');
}

// --- Initialization Functions ---

function initThemeToggle() {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (!themeToggleBtn) return;

    const iconDark = themeToggleBtn.querySelector('.theme-icon-dark');
    const iconLight = themeToggleBtn.querySelector('.theme-icon-light');

    function updateIcons(theme) {
        if (theme === 'dark') {
            if (iconDark) iconDark.style.display = 'none';
            if (iconLight) iconLight.style.display = 'inline-block';
        } else {
            if (iconDark) iconDark.style.display = 'inline-block';
            if (iconLight) iconLight.style.display = 'none';
        }
    }

    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    updateIcons(currentTheme);

    themeToggleBtn.addEventListener('click', () => {
        const theme = document.documentElement.getAttribute('data-theme');
        const newTheme = theme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateIcons(newTheme);
        elimTrackEvent('theme_toggle', { theme: newTheme });
    });
}

function initNavbarScroll() {
    window.addEventListener('scroll', function () {
        const nav = document.querySelector('.navbar-custom');
        if (!nav) return;
        if (window.scrollY > 50) {
            nav.classList.add('navbar-scrolled');
        } else {
            nav.classList.remove('navbar-scrolled');
        }
    });
}

function initSearchModal() {
    const searchModal = document.getElementById('searchModal');
    const searchInput = document.getElementById('searchInput');
    const openBtn = document.getElementById('openSearchBtn');
    const closeBtn = document.getElementById('closeSearchBtn');
    const suggestionsContainer = document.getElementById('searchSuggestions');
    const suggestionsList = document.getElementById('searchSuggestionsList');
    const searchLoading = document.getElementById('searchLoading');
    const noResults = document.getElementById('searchNoResults');

    if (!searchModal || !openBtn || !closeBtn) return;

    let debounceTimer;

    function openSearchModal() {
        searchModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        setTimeout(() => searchInput && searchInput.focus(), 100);
        elimTrackEvent('search_modal_open');
    }

    function closeSearchModal() {
        searchModal.classList.remove('active');
        document.body.style.overflow = '';
        if (searchInput) {
            searchInput.value = '';
            if (suggestionsContainer) suggestionsContainer.style.display = 'none';
        }
    }

    function performInstantSearch(query) {
        if (!query || query.length < 2) {
            if (suggestionsContainer) suggestionsContainer.style.display = 'none';
            return;
        }

        if (suggestionsContainer) suggestionsContainer.style.display = 'block';
        if (searchLoading) searchLoading.style.display = 'block';
        if (suggestionsList) suggestionsList.innerHTML = '';
        if (noResults) noResults.style.display = 'none';

        fetch(`/search/?query=${encodeURIComponent(query)}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (searchLoading) searchLoading.style.display = 'none';

                if (data.results && data.results.length > 0) {
                    if (suggestionsList) {
                        suggestionsList.replaceChildren();
                        data.results.forEach(item => {
                            const link = document.createElement('a');
                            link.href = item.url;
                            link.className = 'search-suggestion-item';
                            if (item.image) {
                                const img = document.createElement('img');
                                img.src = item.image;
                                img.alt = '';
                                img.loading = 'lazy';
                                link.appendChild(img);
                            } else {
                                const icon = document.createElement('div');
                                icon.className = 'suggestion-icon';
                                icon.setAttribute('aria-hidden', 'true');
                                icon.textContent = '›';
                                link.appendChild(icon);
                            }
                            const details = document.createElement('div');
                            details.className = 'suggestion-details';
                            const title = document.createElement('div');
                            title.className = 'suggestion-title';
                            title.textContent = item.title;
                            const meta = document.createElement('div');
                            meta.className = 'suggestion-meta';
                            meta.textContent = item.type_label;
                            details.append(title, meta);
                            link.appendChild(details);
                            suggestionsList.appendChild(link);
                        });
                    }
                } else {
                    if (noResults) noResults.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Search error:', error);
                if (searchLoading) searchLoading.style.display = 'none';
            });
    }

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                performInstantSearch(this.value);
            }, 300);
        });
    }

    openBtn.addEventListener('click', openSearchModal);
    closeBtn.addEventListener('click', closeSearchModal);

    searchModal.addEventListener('click', function (e) {
        if (e.target === searchModal) {
            closeSearchModal();
        }
    });

    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (searchModal.classList.contains('active')) {
                closeSearchModal();
            } else {
                openSearchModal();
            }
        }
        if (e.key === 'Escape' && searchModal.classList.contains('active')) {
            closeSearchModal();
        }
    });
}

async function initVerse(fallbackVerses) {
    const verseText = document.getElementById('verse-text');
    const verseRef = document.getElementById('verse-ref');

    if (!verseText || !verseRef) return;

    function setVerse(text, ref) {
        verseText.style.opacity = 0;
        setTimeout(() => {
            verseText.textContent = `"${text}"`;
            verseRef.textContent = ref;
            verseText.style.transition = 'opacity 1s ease';
            verseText.style.opacity = 1;
        }, 300);
    }

    // Select locally so the footer works offline and sends no visitor data to a third party.
    if (fallbackVerses && fallbackVerses.length > 0) {
        const dayNumber = Math.floor(Date.now() / 86400000);
        const verse = fallbackVerses[dayNumber % fallbackVerses.length];
        setVerse(verse.text, verse.ref);
    }
}

function initCountryFlags(inputId, datalistId, flagImgId, countriesMap) {
    const input = document.getElementById(inputId);
    const datalist = document.getElementById(datalistId);
    const flagImg = document.getElementById(flagImgId);
    if (!input || !datalist || !countriesMap) return;

    const normalizeStr = (str) => str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
    const normalizedCountriesMap = {};
    for (const [name, code] of Object.entries(countriesMap)) {
        normalizedCountriesMap[normalizeStr(name)] = code;
    }

    const all = Array.from(datalist.options).map(o => o.value);

    function updateFlagFor(name) {
        if (!name || !flagImg) {
            if (flagImg) {
                flagImg.style.display = 'none';
                flagImg.src = '';
            }
            return;
        }
        const q = normalizeStr(name);
        const code = normalizedCountriesMap[q];
        if (code) {
            flagImg.src = 'https://flagcdn.com/24x18/' + code + '.png';
            flagImg.style.display = '';
        } else {
            flagImg.style.display = 'none';
            flagImg.src = '';
        }
    }

    input.addEventListener('input', function () {
        const q = normalizeStr(input.value);
        datalist.innerHTML = '';
        all.forEach(function (name) {
            if (!q || normalizeStr(name).startsWith(q)) {
                const opt = document.createElement('option');
                opt.value = name;
                datalist.appendChild(opt);
            }
        });
        updateFlagFor(input.value);
    });

    input.addEventListener('change', function () {
        updateFlagFor(input.value);
    });
}

// --- Form Handling ---

/**
 * Enhanced AJAX form handler with analytics tracking.
 * @param {string} formId 
 * @param {Function} successCallback 
 * @param {string} trackingEvent (Optional) Name of the GA4 event to fire on success.
 */
function handleAjaxForm(formId, successCallback, trackingEvent = null) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(this);
        const submitButton = this.querySelector('button[type="submit"]');
        if (!submitButton) return;

        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Procesando...';

        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (trackingEvent) {
                        elimTrackEvent(trackingEvent, {
                            form_id: formId,
                            status: 'success'
                        });
                    }
                    if (successCallback) successCallback(data);
                } else {
                    let errorMessage = 'Por favor corrige los siguientes errores:\n';
                    if (data.errors) {
                        for (const [field, errors] of Object.entries(data.errors)) {
                            errorMessage += `${field}: ${errors.join(', ')}\n`;
                        }
                    } else {
                        errorMessage = data.message || 'Ha ocurrido un error. Inténtalo de nuevo.';
                    }
                    showError(errorMessage);

                    if (trackingEvent) {
                        elimTrackEvent(`${trackingEvent}_error`, {
                            form_id: formId,
                            error: errorMessage
                        });
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Ha ocurrido un error de conexión. Inténtalo de nuevo.');
                if (trackingEvent) {
                    elimTrackEvent(`${trackingEvent}_error`, {
                        form_id: formId,
                        error: 'connection_error'
                    });
                }
            })
            .finally(() => {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            });
    });
}

// Global Alert Override
window.alert = function (message) {
    showMessageModal(message, false);
};

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', function () {
    initThemeToggle();
    initNavbarScroll();
    initSearchModal();

    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            once: true,
            offset: 100,
            easing: 'ease-out-cubic',
        });
    }
});
