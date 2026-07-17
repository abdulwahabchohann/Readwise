(function () {
    const root = document.querySelector('[data-advanced-recommend]');
    if (!root) {
        return;
    }

    const apiUrl = root.dataset.apiUrl;
    const isAuthenticated = root.dataset.authenticated === 'true';
    const form = root.querySelector('[data-advanced-form]');
    const promptInput = root.querySelector('[data-prompt-input]');
    const thinking = root.querySelector('[data-thinking]');
    const errorBox = root.querySelector('[data-error]');
    const results = root.querySelector('[data-results]');
    const cardList = root.querySelector('[data-card-list]');
    const sourcePill = root.querySelector('[data-response-source]');
    const historyList = root.querySelector('[data-history-list]');
    const historyEmpty = root.querySelector('[data-history-empty]');
    const newSearchButton = root.querySelector('[data-new-search]');
    const clearHistoryButton = root.querySelector('[data-clear-history]');
    const submitButton = form ? form.querySelector('button[type="submit"]') : null;
    const historyKey = 'readwise:advanced-recommend-history:v1';
    const savedListKey = 'readwise:advanced-reading-list:v1';

    function getCsrfToken() {
        const input = form ? form.querySelector('input[name="csrfmiddlewaretoken"]') : null;
        if (input && input.value) {
            return input.value;
        }
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    function readJson(key, fallback) {
        try {
            const value = JSON.parse(window.localStorage.getItem(key) || '');
            return value || fallback;
        } catch (error) {
            return fallback;
        }
    }

    function writeJson(key, value) {
        window.localStorage.setItem(key, JSON.stringify(value));
    }

    function clearElement(element) {
        while (element && element.firstChild) {
            element.removeChild(element.firstChild);
        }
    }

    function createElement(tag, className, text) {
        const node = document.createElement(tag);
        if (className) {
            node.className = className;
        }
        if (text !== undefined && text !== null) {
            node.textContent = text;
        }
        return node;
    }

    function normalizeTone(value) {
        const text = String(value || 'thoughtful').toLowerCase();
        if (text.includes('comfort')) return 'comforting';
        if (text.includes('educat') || text.includes('learn')) return 'educational';
        if (text.includes('motivat')) return 'motivating';
        if (text.includes('mind')) return 'mind-expanding';
        if (text.includes('relevant')) return 'relevant';
        return text.split(/\s+/)[0] || 'thoughtful';
    }

    function setLoading(isLoading) {
        if (thinking) {
            thinking.hidden = !isLoading;
        }
        if (submitButton) {
            submitButton.disabled = isLoading;
        }
    }

    function setError(message) {
        if (!errorBox) return;
        if (!message) {
            errorBox.hidden = true;
            errorBox.textContent = '';
            return;
        }
        errorBox.textContent = message;
        errorBox.hidden = false;
    }

    function renderHistory() {
        const items = readJson(historyKey, []);
        clearElement(historyList);
        if (historyEmpty) {
            historyEmpty.hidden = items.length > 0;
        }
        items.forEach((item) => {
            const button = createElement('button', 'advanced-history__item', item.prompt);
            button.type = 'button';
            button.addEventListener('click', () => {
                promptInput.value = item.prompt;
                renderResponse(item.response);
            });
            historyList.appendChild(button);
        });
    }

    function saveHistory(prompt, response) {
        const items = readJson(historyKey, []);
        const nextItems = [
            { prompt, response },
            ...items.filter((item) => item.prompt !== prompt),
        ].slice(0, 5);
        writeJson(historyKey, nextItems);
        renderHistory();
    }

    function savedIdentity(book) {
        return String(book.book_id || `${book.title}|${book.author}`).toLowerCase();
    }

    function isSaved(book) {
        const saved = readJson(savedListKey, []);
        const id = savedIdentity(book);
        return saved.some((item) => item.id === id);
    }

    function saveBook(book, button) {
        const saved = readJson(savedListKey, []);
        const id = savedIdentity(book);
        if (!saved.some((item) => item.id === id)) {
            saved.unshift({
                id,
                title: book.title,
                author: book.author,
                book_url: book.book_url || '',
                in_library: Boolean(book.in_library),
                saved_at: new Date().toISOString(),
            });
            writeJson(savedListKey, saved.slice(0, 100));
        }
        button.textContent = 'Added';
        button.disabled = true;
    }

    function renderBookCard(book, index) {
        const card = createElement('article', 'advanced-book-card');
        card.style.animationDelay = `${index * 150}ms`;

        const top = createElement('div', 'advanced-card__top');
        top.appendChild(createElement('span', 'advanced-card__rank', `#${book.rank || index + 1}`));
        const badge = createElement('span', 'advanced-card__badge', book.mood_tag || 'thoughtful');
        badge.dataset.tone = normalizeTone(book.mood_tag);
        top.appendChild(badge);
        card.appendChild(top);

        const title = createElement('h3', 'advanced-card__title', book.title || 'Untitled');
        card.appendChild(title);
        card.appendChild(createElement('p', 'advanced-card__author', `by ${book.author || 'Author unknown'}`));

        const body = createElement('div', 'advanced-card__body');
        const score = Math.max(0, Math.min(Number(book.match_score || 0), 100));
        const scoreRow = createElement('div', 'advanced-card__score');
        const progress = createElement('div', 'advanced-card__progress');
        const fill = createElement('span');
        fill.style.setProperty('--score-width', `${score}%`);
        progress.appendChild(fill);
        scoreRow.appendChild(progress);
        scoreRow.appendChild(createElement('strong', '', `${score}%`));
        body.appendChild(scoreRow);

        body.appendChild(createElement('p', 'advanced-card__reason', book.reason || 'A strong fit for your prompt.'));

        const meta = createElement('div', 'advanced-card__meta');
        meta.appendChild(createElement('span', 'advanced-card__small-tag', book.genre || 'General'));
        meta.appendChild(createElement('span', 'advanced-card__small-tag', book.difficulty || 'Intermediate'));
        body.appendChild(meta);

        const footer = createElement('div', 'advanced-card__footer');
        const library = createElement(
            'span',
            book.in_library ? 'advanced-card__library' : 'advanced-card__library advanced-card__library--external',
            book.in_library ? 'In ReadWise library' : 'External suggestion'
        );
        footer.appendChild(library);

        if (isAuthenticated) {
            const action = createElement('button', 'advanced-card__action', isSaved(book) ? 'Added' : 'Add to Reading List');
            action.type = 'button';
            action.disabled = isSaved(book);
            action.addEventListener('click', () => saveBook(book, action));
            footer.appendChild(action);
        }
        body.appendChild(footer);
        card.appendChild(body);
        return card;
    }

    function renderResponse(response) {
        const recommendations = Array.isArray(response.recommendations) ? response.recommendations : [];
        clearElement(cardList);
        recommendations.forEach((book, index) => {
            cardList.appendChild(renderBookCard(book, index));
        });
        if (sourcePill) {
            sourcePill.textContent = response.fallback_used ? 'Fallback active' : (response.cached ? 'Cached result' : 'LLM result');
        }
        if (results) {
            results.hidden = recommendations.length === 0;
            if (recommendations.length) {
                results.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }

    async function submitPrompt(prompt) {
        setError('');
        setLoading(true);
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ user_prompt: prompt }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Unable to find recommendations right now.');
            }
            renderResponse(data);
            saveHistory(prompt, data);
        } catch (error) {
            setError(error.message || 'Unable to find recommendations right now.');
        } finally {
            setLoading(false);
        }
    }

    if (form) {
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const prompt = String(promptInput.value || '').trim();
            if (!prompt) {
                setError('Please enter a prompt first.');
                return;
            }
            submitPrompt(prompt);
        });
    }

    if (newSearchButton) {
        newSearchButton.addEventListener('click', () => {
            promptInput.value = '';
            setError('');
            clearElement(cardList);
            if (results) {
                results.hidden = true;
            }
            promptInput.focus();
        });
    }

    if (clearHistoryButton) {
        clearHistoryButton.addEventListener('click', () => {
            writeJson(historyKey, []);
            renderHistory();
        });
    }

    renderHistory();
})();
