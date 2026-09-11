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

    const mode = root.dataset.mode || 'classic';
    const listId = root.dataset.listId || '';
    const reviewMode = root.dataset.review === 'true';
    const cardSeconds = parseInt(root.dataset.seconds, 10) || 10;

    let cards = [];
    let currentIndex = 0;
    let knownCount = 0;
    let unknownCount = 0;

    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    const swipeThreshold = 100;

    // Timer mode state
    let timerId = null;
    let deadline = 0;

    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

    async function api(url, options = {}) {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || '',
                ...(options.headers || {})
            },
            ...options
        });
        if (response.status === 401 || response.redirected) {
            window.location.href = '/login/';
            return null;
        }
        return response;
    }

    async function fetchCards() {
        const params = new URLSearchParams();
        if (listId) params.append('list_id', listId);
        if (reviewMode) params.append('review_mode', 'true');
        const url = '/api/cards/' + (params.toString() ? `?${params}` : '');

        try {
            const response = await api(url);
            if (!response) return;
            cards = await response.json();
        } catch (error) {
            console.error('Failed to fetch cards:', error);
            return;
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

    function updateProgress() {
        const progress = cards.length ? (currentIndex / cards.length) * 100 : 0;
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${currentIndex} / ${cards.length}`;
        scoreKnownEl.textContent = knownCount;
        scoreUnknownEl.textContent = unknownCount;

        if (cards.length && currentIndex >= cards.length) {
            stopTimer();
            setTimeout(showCompletion, 400);
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
        const topCard = cardStack.querySelector('.vocab-card:last-child');
        if (!topCard) return;
        const inner = topCard.querySelector('.card-inner');
        if (inner.classList.contains('is-flipped')) return;
        handleAnswer(topCard, false);
        setTimeout(nextCard, 1600);
    }

    // ---- Cards ----

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

        const meanings = data.meanings.length ? data.meanings : ['No meaning saved for this word.'];
        const meaningsHtml = meanings.map((m, index) => `
            <div class="py-3 border-b border-slate-100 last:border-0 w-full text-center">
                ${meanings.length > 1 ? `<span class="text-xs font-bold text-indigo-400 block mb-1 uppercase tracking-tighter">Meaning ${index + 1}</span>` : ''}
                <p class="text-lg text-slate-700 leading-relaxed">${m}</p>
            </div>
        `).join('');

        card.innerHTML = `
            <div class="card-inner">
                <div class="card-face card-front">
                    <div class="swipe-indicator know">Know</div>
                    <div class="swipe-indicator dont-know">Don't Know</div>
                    <h2 class="text-4xl md:text-5xl font-black text-slate-800 tracking-tight text-center break-words w-full px-2">${data.word}</h2>
                    <p class="absolute bottom-8 text-slate-300 text-sm font-medium uppercase tracking-widest">Swipe to reveal</p>
                </div>
                <div class="card-face card-back">
                    <div class="w-full space-y-2 pb-20">${meaningsHtml}</div>
                    <div class="absolute bottom-6 w-full px-6">
                        <button class="next-btn w-full bg-indigo-600 text-white py-3 rounded-xl font-bold shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all">Next card</button>
                    </div>
                </div>
            </div>
        `;

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

            card.style.transform = `translate(${currentX}px, ${currentY}px) rotate(${currentX / 10}deg)`;

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

        api(`/api/cards/${card.dataset.id}/status/`, {
            method: 'POST',
            body: JSON.stringify({ is_known: isKnown })
        }).catch(err => console.error('Failed to update status', err));

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

    document.addEventListener('keydown', (e) => {
        if (currentIndex >= cards.length) return;
        const topCard = cardStack.querySelector('.vocab-card:last-child');
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
});
