document.addEventListener('DOMContentLoaded', () => {
    const root = document.getElementById('game-root');
    const cardStack = document.getElementById('card-stack');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const replayBtn = document.getElementById('replay-btn');
    const completionScreen = document.getElementById('completion-screen');
    const completionMessage = document.getElementById('completion-message');
    const emptyScreen = document.getElementById('empty-screen');
    const scoreKnownEl = document.getElementById('score-known');
    const scoreUnknownEl = document.getElementById('score-unknown');
    const timerBar = document.getElementById('timer-bar');
    const timerText = document.getElementById('timer-text');
    const btnKnown = document.getElementById('btn-known');
    const btnUnknown = document.getElementById('btn-unknown');
    const streakBadge = document.getElementById('streak-badge');
    const streakCount = document.getElementById('streak-count');

    const mode = root.dataset.mode || 'classic';
    const listId = root.dataset.listId || '';
    const reviewMode = root.dataset.review === 'true';
    const isAuthenticated = root.dataset.auth === 'true';
    const cardSeconds = parseInt(root.dataset.seconds, 10) || 10;
    const guestStore = `vocabswipe:guest:${listId || 'all'}`;

    let cards = [];
    let currentIndex = 0;
    let knownCount = 0;
    let unknownCount = 0;

    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    const swipeThreshold = 90;

    let timerId = null;
    let deadline = 0;

    // ---- Guest progress (browser only) ----

    function loadGuestKnown() {
        if (isAuthenticated) return new Set();
        try {
            return new Set(JSON.parse(localStorage.getItem(guestStore) || '[]'));
        } catch (err) {
            return new Set();
        }
    }

    const guestKnown = loadGuestKnown();

    function saveGuestKnown() {
        if (isAuthenticated) return;
        try {
            localStorage.setItem(guestStore, JSON.stringify([...guestKnown]));
        } catch (err) {
            /* storage blocked or full — progress just isn't kept */
        }
    }

    // ---- Networking ----

    function readCookie(name) {
        const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

    async function api(url, options = {}) {
        return fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': readCookie('csrftoken') || '',
                ...(options.headers || {})
            },
            ...options
        });
    }

    // ---- Streak ----

    function updateStreakUI(streak) {
        if (!streakBadge) return;
        if (streak > 0) {
            streakBadge.classList.remove('hidden');
            streakCount.textContent = streak;
        } else {
            streakBadge.classList.add('hidden');
        }
    }

    async function fetchStats() {
        if (!isAuthenticated) return;
        try {
            const response = await api('/api/user-stats/');
            const stats = await response.json();
            updateStreakUI(stats.current_streak);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    }

    function playAudio(url) {
        if (!url) return;
        new Audio(url).play().catch(err => console.error('Audio playback failed', err));
    }

    async function fetchCards() {
        const params = new URLSearchParams();
        if (listId) params.append('list_id', listId);
        if (reviewMode) params.append('review_mode', 'true');
        const url = '/api/cards/' + (params.toString() ? `?${params}` : '');

        try {
            const response = await api(url);
            cards = await response.json();
        } catch (error) {
            console.error('Failed to fetch cards:', error);
            cards = [];
        }

        if (!isAuthenticated) {
            cards.forEach(card => { card.is_known = guestKnown.has(card.id); });
        }

        if (!cards.length) {
            cardStack.classList.add('hidden');
            emptyScreen.classList.remove('hidden');
            return;
        }
        updateProgress();
        renderStack();
        startTimer();
    }

    // ---- Progress ----

    function updateProgress() {
        const progress = cards.length ? (currentIndex / cards.length) * 100 : 0;
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${currentIndex} / ${cards.length}`;
        scoreKnownEl.textContent = knownCount;
        scoreUnknownEl.textContent = unknownCount;

        if (cards.length && currentIndex >= cards.length) {
            stopTimer();
            setTimeout(showCompletion, 350);
        }
    }

    function showCompletion() {
        cardStack.classList.add('hidden');
        completionScreen.classList.remove('hidden');
        completionMessage.textContent =
            `${knownCount} known, ${unknownCount} to review out of ${cards.length} words.`;
    }

    // ---- Timer mode ----

    function startTimer() {
        if (mode !== 'timer' || !timerBar) return;
        stopTimer();
        deadline = Date.now() + cardSeconds * 1000;
        timerBar.style.width = '100%';
        timerText.textContent = `${cardSeconds}s`;
        timerId = setInterval(tick, 100);
    }

    function stopTimer() {
        if (timerId) {
            clearInterval(timerId);
            timerId = null;
        }
    }

    function tick() {
        const remaining = Math.max(0, deadline - Date.now());
        const ratio = remaining / (cardSeconds * 1000);
        timerBar.style.width = `${ratio * 100}%`;
        timerText.textContent = `${Math.ceil(remaining / 1000)}s`;

        if (remaining <= 0) {
            stopTimer();
            timeUp();
        }
    }

    function timeUp() {
        const topCard = getTopCard();
        if (!topCard) return;
        if (topCard.querySelector('.card-inner').classList.contains('is-flipped')) return;
        handleAnswer(topCard, false);
        setTimeout(nextCard, 1600);
    }

    // ---- Cards ----

    function getTopCard() {
        return cardStack.querySelector('.vocab-card:last-child');
    }

    function renderStack() {
        cardStack.innerHTML = '';
        if (currentIndex >= cards.length) return;

        for (let i = Math.min(currentIndex + 2, cards.length - 1); i >= currentIndex; i--) {
            cardStack.appendChild(createCardElement(cards[i], i === currentIndex));
        }
    }

    function createCardElement(data, isTop) {
        const card = document.createElement('div');
        card.className = 'vocab-card';
        card.dataset.id = data.id;

        const inner = document.createElement('div');
        inner.className = 'card-inner';

        // Front face
        const front = document.createElement('div');
        front.className = 'card-face card-front';
        front.innerHTML = `
            <div class="swipe-indicator know">Know</div>
            <div class="swipe-indicator dont-know">Review</div>
        `;

        const word = document.createElement('h2');
        word.className = 'text-3xl md:text-4xl font-bold tracking-tight text-center break-words w-full px-2';
        word.textContent = data.word;
        front.appendChild(word);

        const hint = document.createElement('p');
        hint.className = 'absolute bottom-6 text-xs text-mute uppercase tracking-widest';
        hint.textContent = 'Swipe to reveal';
        front.appendChild(hint);

        if (data.audio_url) {
            const audioBtn = document.createElement('button');
            audioBtn.type = 'button';
            audioBtn.className =
                'audio-btn absolute top-4 right-4 w-9 h-9 rounded-full border border-line text-mute hover:text-brand-600 hover:border-brand-300 transition-colors';
            audioBtn.setAttribute('aria-label', `Play pronunciation of ${data.word}`);
            audioBtn.textContent = '♪';
            audioBtn.addEventListener('mousedown', (e) => e.stopPropagation());
            audioBtn.addEventListener('touchstart', (e) => e.stopPropagation(), { passive: true });
            audioBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                playAudio(data.audio_url);
            });
            front.appendChild(audioBtn);
        }

        // Back face
        const back = document.createElement('div');
        back.className = 'card-face card-back';

        const meanings = (data.meanings && data.meanings.length)
            ? data.meanings
            : ['No meaning saved for this word.'];

        const backWord = document.createElement('p');
        backWord.className = 'text-xs uppercase tracking-widest text-mute mb-3';
        backWord.textContent = data.word;
        back.appendChild(backWord);

        const meaningWrap = document.createElement('div');
        meaningWrap.className = 'w-full space-y-3';
        meanings.forEach((meaning, index) => {
            const row = document.createElement('div');
            row.className = 'pb-3 border-b border-line last:border-0 w-full text-center';
            if (meanings.length > 1) {
                const label = document.createElement('span');
                label.className = 'block text-[11px] font-medium text-brand-500 mb-1';
                label.textContent = `Meaning ${index + 1}`;
                row.appendChild(label);
            }
            const text = document.createElement('p');
            text.className = 'text-base leading-relaxed';
            text.textContent = meaning;
            row.appendChild(text);
            meaningWrap.appendChild(row);
        });
        back.appendChild(meaningWrap);

        if (data.example) {
            const example = document.createElement('p');
            example.className = 'w-full mt-4 text-sm text-mute italic text-center px-2';
            example.textContent = `“${data.example}”`;
            back.appendChild(example);
        }

        const nextWrap = document.createElement('div');
        nextWrap.className = 'absolute bottom-5 left-0 w-full px-5';
        nextWrap.innerHTML = `
            <button class="next-btn w-full py-3 rounded-lg bg-ink text-white text-sm font-medium active:scale-[0.98] transition-all">Next card</button>
        `;
        back.appendChild(nextWrap);

        inner.appendChild(front);
        inner.appendChild(back);
        card.appendChild(inner);

        if (isTop) initCardInteractions(card);
        return card;
    }

    function initCardInteractions(card) {
        const inner = card.querySelector('.card-inner');
        const nextBtn = card.querySelector('.next-btn');

        card.addEventListener('mousedown', startDrag);
        card.addEventListener('touchstart', startDrag, { passive: true });

        nextBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            nextCard();
        });

        function startDrag(e) {
            if (inner.classList.contains('is-flipped')) return;

            isDragging = true;
            startX = e.type === 'mousedown' ? e.clientX : e.touches[0].clientX;
            startY = e.type === 'mousedown' ? e.clientY : e.touches[0].clientY;

            card.style.transition = 'none';
            document.addEventListener('mousemove', drag);
            document.addEventListener('touchmove', drag, { passive: false });
            document.addEventListener('mouseup', stopDrag);
            document.addEventListener('touchend', stopDrag);
        }

        function drag(e) {
            if (!isDragging) return;
            if (e.type === 'touchmove') e.preventDefault();

            currentX = (e.type === 'mousemove' ? e.clientX : e.touches[0].clientX) - startX;
            currentY = (e.type === 'mousemove' ? e.clientY : e.touches[0].clientY) - startY;

            card.style.transform = `translate(${currentX}px, ${currentY}px) rotate(${currentX / 14}deg)`;

            if (currentX > 20) {
                card.classList.add('swipe-right');
                card.classList.remove('swipe-left');
            } else if (currentX < -20) {
                card.classList.add('swipe-left');
                card.classList.remove('swipe-right');
            } else {
                card.classList.remove('swipe-right', 'swipe-left');
            }
        }

        function stopDrag() {
            if (!isDragging) return;
            isDragging = false;

            document.removeEventListener('mousemove', drag);
            document.removeEventListener('touchmove', drag);
            document.removeEventListener('mouseup', stopDrag);
            document.removeEventListener('touchend', stopDrag);

            if (Math.abs(currentX) > swipeThreshold) {
                handleAnswer(card, currentX > 0);
            } else {
                card.style.transition = 'transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                card.style.transform = '';
                card.classList.remove('swipe-right', 'swipe-left');
            }

            currentX = 0;
            currentY = 0;
        }
    }

    function handleAnswer(card, isKnown) {
        const inner = card.querySelector('.card-inner');
        if (inner.classList.contains('is-flipped')) return;

        stopTimer();

        if (isKnown) knownCount++; else unknownCount++;
        scoreKnownEl.textContent = knownCount;
        scoreUnknownEl.textContent = unknownCount;

        const cardId = parseInt(card.dataset.id, 10);
        if (isAuthenticated) {
            api(`/api/cards/${cardId}/status/`, {
                method: 'POST',
                body: JSON.stringify({ is_known: isKnown })
            })
                .then(response => response.json())
                .then(result => {
                    if (typeof result.streak === 'number') updateStreakUI(result.streak);
                })
                .catch(err => console.error('Failed to update status', err));
        } else {
            if (isKnown) guestKnown.add(cardId); else guestKnown.delete(cardId);
            saveGuestKnown();
        }

        inner.classList.add('is-flipped');
        card.style.transition = 'transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
        card.style.transform = '';
        card.classList.remove('swipe-right', 'swipe-left');
    }

    function nextCard() {
        currentIndex++;
        updateProgress();
        renderStack();
        if (currentIndex < cards.length) startTimer();
    }

    function answerTop(isKnown) {
        const topCard = getTopCard();
        if (!topCard) return;
        const flipped = topCard.querySelector('.card-inner').classList.contains('is-flipped');
        if (flipped) {
            nextCard();
        } else {
            handleAnswer(topCard, isKnown);
        }
    }

    if (btnKnown) btnKnown.addEventListener('click', () => answerTop(true));
    if (btnUnknown) btnUnknown.addEventListener('click', () => answerTop(false));

    document.addEventListener('keydown', (e) => {
        if (currentIndex >= cards.length) return;
        const topCard = getTopCard();
        if (!topCard) return;
        const flipped = topCard.querySelector('.card-inner').classList.contains('is-flipped');

        if (e.key === 'ArrowRight' && !flipped) {
            handleAnswer(topCard, true);
        } else if (e.key === 'ArrowLeft' && !flipped) {
            handleAnswer(topCard, false);
        } else if ((e.key === 'Enter' || e.key === ' ') && flipped) {
            e.preventDefault();
            nextCard();
        }
    });

    replayBtn.addEventListener('click', () => {
        currentIndex = 0;
        knownCount = 0;
        unknownCount = 0;
        completionScreen.classList.add('hidden');
        cardStack.classList.remove('hidden');
        updateProgress();
        renderStack();
        startTimer();
    });

    fetchCards();
    fetchStats();
});
