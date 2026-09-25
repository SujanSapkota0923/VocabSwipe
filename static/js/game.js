document.addEventListener('DOMContentLoaded', () => {
    const root = document.getElementById('game-root');
    const cardStack = document.getElementById('card-stack');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const replayBtn = document.getElementById('replay-btn');
    const completionScreen = document.getElementById('completion-screen');
    const completionMessage = document.getElementById('completion-message');
    const completionScore = document.getElementById('completion-score');
    const reviewLink = document.getElementById('review-link');
    const emptyScreen = document.getElementById('empty-screen');
    const loadingScreen = document.getElementById('loading-screen');
    const errorScreen = document.getElementById('error-screen');
    const retryBtn = document.getElementById('retry-btn');
    const scoreKnownEl = document.getElementById('score-known');
    const scoreUnknownEl = document.getElementById('score-unknown');
    const timerBar = document.getElementById('timer-bar');
    const timerText = document.getElementById('timer-text');
    const controls = document.getElementById('game-controls');
    const answerButtons = document.getElementById('answer-buttons');
    const btnKnown = document.getElementById('btn-known');
    const btnUnknown = document.getElementById('btn-unknown');
    const btnNext = document.getElementById('btn-next');
    const streakBadge = document.getElementById('streak-badge');
    const streakCount = document.getElementById('streak-count');

    const mode = root.dataset.mode || 'classic';
    const listId = root.dataset.listId || '';
    const reviewMode = root.dataset.review === 'true';
    const isAuthenticated = root.dataset.auth === 'true';
    const cardSeconds = parseInt(root.dataset.seconds, 10) || 10;
    const guestStore = `vocabswipe:guest:${listId || 'all'}`;

    // A drag past this distance, or a quick flick past FLICK_DISTANCE, answers the card.
    const SWIPE_DISTANCE = 96;
    const FLICK_DISTANCE = 36;
    const FLICK_SPEED = 0.55; // px per ms
    const LEAVE_MS = 220;
    const TIMEOUT_REVEAL_MS = 1600;

    let cards = [];
    let currentIndex = 0;
    let knownCount = 0;
    let unknownCount = 0;
    let lastAnswer = null; // true = known, false = review, for the fly-out direction
    let advancing = false;
    let autoAdvanceId = null;

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

    // ---- Screens ----

    function showOnly(screen) {
        [cardStack, loadingScreen, errorScreen, emptyScreen, completionScreen].forEach(el => {
            el.classList.toggle('hidden', el !== screen);
        });
        // Answer buttons only make sense while there is a card to answer.
        controls.classList.toggle('is-idle', screen !== cardStack);
    }

    async function fetchCards() {
        const params = new URLSearchParams();
        if (listId) params.append('list_id', listId);
        if (reviewMode) params.append('review_mode', 'true');
        const url = '/api/cards/' + (params.toString() ? `?${params}` : '');

        showOnly(loadingScreen);

        try {
            const response = await api(url);
            if (!response.ok) throw new Error(`Request failed with ${response.status}`);
            cards = await response.json();
        } catch (error) {
            // A dropped connection is not the same as an empty deck, so it gets
            // its own screen with a retry instead of "No words here".
            console.error('Failed to fetch cards:', error);
            cards = [];
            showOnly(errorScreen);
            return;
        }

        if (!isAuthenticated) {
            cards.forEach(card => { card.is_known = guestKnown.has(card.id); });
        }

        if (!cards.length) {
            showOnly(emptyScreen);
            return;
        }

        startDeck();
    }

    function startDeck() {
        currentIndex = 0;
        knownCount = 0;
        unknownCount = 0;
        showOnly(cardStack);
        renderStack();
        setControls('answer');
        updateProgress();
        startTimer();
    }

    // ---- Progress ----

    function updateProgress() {
        const progress = cards.length ? (currentIndex / cards.length) * 100 : 0;
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${Math.min(currentIndex + 1, cards.length)} / ${cards.length}`;
        scoreKnownEl.textContent = knownCount;
        scoreUnknownEl.textContent = unknownCount;
    }

    function showCompletion() {
        stopTimer();
        progressBar.style.width = '100%';
        progressText.textContent = `${cards.length} / ${cards.length}`;
        const answered = knownCount + unknownCount;
        const score = answered ? Math.round((knownCount / answered) * 100) : 0;
        completionScore.textContent = `${score}%`;
        completionMessage.textContent =
            `${knownCount} known · ${unknownCount} to review · ${cards.length} word${cards.length === 1 ? '' : 's'}`;
        if (reviewLink) reviewLink.classList.toggle('hidden', unknownCount === 0);
        showOnly(completionScreen);
        replayBtn.focus({ preventScroll: true });
    }

    // ---- Timer mode ----

    function startTimer() {
        if (mode !== 'timer' || !timerBar) return;
        stopTimer();
        deadline = Date.now() + cardSeconds * 1000;
        timerBar.style.width = '100%';
        if (timerText) timerText.textContent = `${cardSeconds}s`;
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
        timerBar.style.width = `${(remaining / (cardSeconds * 1000)) * 100}%`;
        if (timerText) timerText.textContent = `${Math.ceil(remaining / 1000)}s`;

        if (remaining <= 0) {
            stopTimer();
            timeUp();
        }
    }

    function timeUp() {
        const topCard = getTopCard();
        if (!topCard || isRevealed(topCard)) return;
        answer(topCard, false);
        autoAdvanceId = setTimeout(nextCard, TIMEOUT_REVEAL_MS);
    }

    // ---- Controls ----

    function setControls(state) {
        const revealed = state === 'next';
        answerButtons.classList.toggle('hidden', revealed);
        btnNext.classList.toggle('hidden', !revealed);
    }

    // ---- Cards ----

    function getTopCard() {
        const all = cardStack.querySelectorAll('.vocab-card:not(.is-leaving)');
        return all.length ? all[all.length - 1] : null;
    }

    function isRevealed(card) {
        return card.classList.contains('is-revealed');
    }

    // The stack holds up to three cards, the top one last. A layer in front of
    // them carries the card that is flying away, so the next card can move up
    // while it leaves.
    function renderStack() {
        cardStack.innerHTML = '';
        const flyLayer = document.createElement('div');
        flyLayer.className = 'fly-layer';
        cardStack.appendChild(flyLayer);

        for (let i = Math.min(currentIndex + 2, cards.length - 1); i >= currentIndex; i--) {
            cardStack.appendChild(createCardElement(cards[i]));
        }
        const top = getTopCard();
        if (top) initCardInteractions(top);
    }

    function el(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function icon(name) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'icon');
        svg.setAttribute('aria-hidden', 'true');
        const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        use.setAttribute('href', `#${name}`);
        svg.appendChild(use);
        return svg;
    }

    function createCardElement(data) {
        const card = el('article', 'vocab-card');
        card.dataset.id = data.id;
        card.setAttribute('aria-label', `Card: ${data.word}`);

        const inner = el('div', 'card-inner');

        // Front face
        const front = el('div', 'card-face card-front');
        front.appendChild(el('span', 'swipe-stamp stamp-know', 'Know'));
        front.appendChild(el('span', 'swipe-stamp stamp-review', 'Review'));
        front.appendChild(el('h2', 'card-word', data.word));

        if (data.audio_url) {
            const audioBtn = el('button', 'icon-btn audio-btn');
            audioBtn.type = 'button';
            audioBtn.setAttribute('aria-label', `Play pronunciation of ${data.word}`);
            audioBtn.appendChild(icon('i-sound'));
            // Keep a tap on the speaker from starting a drag.
            audioBtn.addEventListener('pointerdown', (e) => e.stopPropagation());
            audioBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                playAudio(data.audio_url);
            });
            front.appendChild(audioBtn);
        }

        const hint = el('p', 'card-hint');
        hint.appendChild(el('span', '', '← Don’t know'));
        hint.appendChild(el('span', '', 'Know it →'));
        front.appendChild(hint);

        // Back face
        const back = el('div', 'card-face card-back');
        back.appendChild(el('p', 'card-back-word', data.word));

        const meanings = (data.meanings && data.meanings.length)
            ? data.meanings
            : ['No meaning saved for this word.'];

        const meaningWrap = el('ol', 'meaning-list');
        if (meanings.length === 1) meaningWrap.classList.add('is-single');
        meanings.forEach(meaning => meaningWrap.appendChild(el('li', 'meaning', meaning)));
        back.appendChild(meaningWrap);

        if (data.example) {
            back.appendChild(el('p', 'card-example', `“${data.example}”`));
        }

        inner.appendChild(front);
        inner.appendChild(back);
        card.appendChild(inner);
        return card;
    }

    function initCardInteractions(card) {
        let pointerId = null;
        let startX = 0;
        let startY = 0;
        let dx = 0;
        let dy = 0;
        let lastX = 0;
        let lastT = 0;
        let velocity = 0;
        let frame = null;
        const knowStamp = card.querySelector('.stamp-know');
        const reviewStamp = card.querySelector('.stamp-review');

        function paint() {
            frame = null;
            const rotate = dx / 16;
            card.style.transform = `translate3d(${dx}px, ${dy * 0.35}px, 0) rotate(${rotate}deg)`;
            const strength = Math.min(Math.abs(dx) / SWIPE_DISTANCE, 1);
            knowStamp.style.opacity = dx > 0 ? strength : 0;
            reviewStamp.style.opacity = dx < 0 ? strength : 0;
        }

        function resetStamps() {
            knowStamp.style.opacity = 0;
            reviewStamp.style.opacity = 0;
        }

        card.addEventListener('pointerdown', (e) => {
            if (isRevealed(card) || advancing || !e.isPrimary) return;
            if (e.pointerType === 'mouse' && e.button !== 0) return;
            pointerId = e.pointerId;
            card.setPointerCapture(pointerId);
            startX = lastX = e.clientX;
            startY = e.clientY;
            lastT = e.timeStamp;
            dx = dy = velocity = 0;
            card.classList.add('is-dragging');
        });

        card.addEventListener('pointermove', (e) => {
            if (e.pointerId !== pointerId) return;
            dx = e.clientX - startX;
            dy = e.clientY - startY;
            const dt = e.timeStamp - lastT;
            if (dt > 0) velocity = (e.clientX - lastX) / dt;
            lastX = e.clientX;
            lastT = e.timeStamp;
            if (!frame) frame = requestAnimationFrame(paint);
        });

        function release(e) {
            if (e.pointerId !== pointerId) return;
            pointerId = null;
            if (frame) {
                cancelAnimationFrame(frame);
                frame = null;
            }
            card.classList.remove('is-dragging');

            const flicked = Math.abs(dx) > FLICK_DISTANCE && Math.abs(velocity) > FLICK_SPEED
                && Math.sign(velocity) === Math.sign(dx);
            if (e.type !== 'pointercancel' && (Math.abs(dx) > SWIPE_DISTANCE || flicked)) {
                answer(card, dx > 0);
            } else {
                card.style.transform = '';
                resetStamps();
            }
            dx = dy = 0;
        }

        card.addEventListener('pointerup', release);
        card.addEventListener('pointercancel', release);
    }

    function answer(card, isKnown) {
        if (!card || isRevealed(card)) return;

        stopTimer();
        lastAnswer = isKnown;

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

        // Settle back to the centre and turn over to show the meaning.
        card.style.transform = '';
        card.querySelectorAll('.swipe-stamp').forEach(s => { s.style.opacity = 0; });
        card.classList.add('is-revealed', isKnown ? 'was-known' : 'was-review');

        const hadFocus = document.activeElement === btnKnown || document.activeElement === btnUnknown;
        setControls('next');
        if (hadFocus) btnNext.focus({ preventScroll: true });
    }

    function nextCard() {
        if (advancing) return;
        if (autoAdvanceId) {
            clearTimeout(autoAdvanceId);
            autoAdvanceId = null;
        }
        const top = getTopCard();
        if (!top) return;

        advancing = true;
        currentIndex++;

        // Fly the answered card off in the direction it was answered.
        const flyLayer = cardStack.querySelector('.fly-layer');
        const direction = lastAnswer === false ? -1 : 1;
        top.classList.add('is-leaving');
        flyLayer.appendChild(top);
        top.getBoundingClientRect(); // commit the start position so the move animates
        top.style.transform =
            `translate3d(${direction * (window.innerWidth * 0.9)}px, -24px, 0) rotate(${direction * 14}deg)`;
        top.style.opacity = '0';
        setTimeout(() => top.remove(), LEAVE_MS);

        if (currentIndex >= cards.length) {
            updateProgress();
            setTimeout(() => {
                advancing = false;
                showCompletion();
            }, LEAVE_MS);
            return;
        }

        // Queue the card two places behind the new top, then let the new top
        // accept input. The CSS transition moves the remaining cards up.
        const incoming = currentIndex + 2;
        if (incoming < cards.length) {
            cardStack.insertBefore(createCardElement(cards[incoming]), flyLayer.nextSibling);
        }
        const newTop = getTopCard();
        if (newTop) initCardInteractions(newTop);

        setControls('answer');
        updateProgress();
        startTimer();
        // Short lock so a double tap on "Next" cannot skip a card.
        setTimeout(() => { advancing = false; }, 120);
    }

    function answerTop(isKnown) {
        const topCard = getTopCard();
        if (!topCard) return;
        if (isRevealed(topCard)) nextCard(); else answer(topCard, isKnown);
    }

    btnKnown.addEventListener('click', () => answerTop(true));
    btnUnknown.addEventListener('click', () => answerTop(false));
    btnNext.addEventListener('click', nextCard);

    document.addEventListener('keydown', (e) => {
        if (e.altKey || e.ctrlKey || e.metaKey) return;
        // A focused button handles its own Enter/Space as a click.
        if (e.target.closest && e.target.closest('button, a, input, textarea')) {
            if (e.key === 'Enter' || e.key === ' ') return;
        }
        if (cardStack.classList.contains('hidden')) return;
        const topCard = getTopCard();
        if (!topCard) return;
        const revealed = isRevealed(topCard);

        if (e.key === 'ArrowRight' && !revealed) {
            e.preventDefault();
            answer(topCard, true);
        } else if (e.key === 'ArrowLeft' && !revealed) {
            e.preventDefault();
            answer(topCard, false);
        } else if ((e.key === 'Enter' || e.key === ' ') && revealed) {
            e.preventDefault();
            nextCard();
        }
    });

    retryBtn.addEventListener('click', fetchCards);
    replayBtn.addEventListener('click', startDeck);

    fetchCards();
    fetchStats();
});
