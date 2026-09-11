document.addEventListener('DOMContentLoaded', () => {
    const cardStack = document.getElementById('card-stack');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const replayBtn = document.getElementById('replay-btn');
    const completionScreen = document.getElementById('completion-screen');
    const gameContainer = document.getElementById('game-container');
    const completionMessage = document.getElementById('completion-message');
    const streakBadge = document.getElementById('streak-badge');
    const streakCount = document.getElementById('streak-count');

    let cards = [];
    let currentIndex = 0;
    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    const swipeThreshold = 100;

    const urlParams = new URLSearchParams(window.location.search);
    const reviewMode = urlParams.get('review_mode');
    const currentListId = urlParams.get('list_id');

    function getApiPassword() {
        let password = localStorage.getItem('api_password');
        if (!password) {
            password = prompt('Enter API Password:');
            if (password) {
                localStorage.setItem('api_password', password);
            }
        }
        return password;
    }

    async function fetchWithAuth(url, options = {}) {
        const password = getApiPassword();
        if (!password) return null;

        const defaultOptions = {
            headers: {
                'X-Api-Password': password,
                'Content-Type': 'application/json'
            }
        };

        const mergedOptions = {
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };

        const response = await fetch(url, mergedOptions);

        if (response.status === 401) {
            localStorage.removeItem('api_password');
            alert('Invalid password. Please try again.');
            window.location.reload();
            return null;
        }

        return response;
    }

    async function fetchStats() {
        try {
            const response = await fetchWithAuth('/api/user-stats/');
            if (!response) return;
            const stats = await response.json();
            updateStreakUI(stats.current_streak);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    }

    function updateStreakUI(streak) {
        if (streak > 0) {
            streakBadge.classList.remove('hidden');
            streakCount.textContent = streak;
        } else {
            streakBadge.classList.add('hidden');
        }
    }

    async function fetchCards() {
        try {
            let url = '/api/cards/';
            const params = new URLSearchParams();
            if (currentListId) params.append('list_id', currentListId);
            if (reviewMode) params.append('review_mode', reviewMode);

            if (params.toString()) {
                url += `?${params.toString()}`;
            }

            const response = await fetchWithAuth(url);
            if (!response) return;

            cards = await response.json();
            updateProgress();
            renderStack();
        } catch (error) {
            console.error('Failed to fetch cards:', error);
        }
    }

    function updateProgress() {
        const progress = cards.length > 0 ? (currentIndex / cards.length) * 100 : 0;
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${currentIndex} / ${cards.length}`;

        if (currentIndex === cards.length && cards.length > 0) {
            setTimeout(showCompletion, 500);
        }
    }

    function showCompletion() {
        cardStack.classList.add('hidden');
        completionScreen.classList.remove('hidden');
        if (reviewMode) {
            completionMessage.textContent = "You've finished your review! All caught up.";
        } else {
            completionMessage.textContent = "You've finished the entire deck. Ready for another round?";
        }
    }

    function renderStack() {
        cardStack.innerHTML = '';
        if (currentIndex >= cards.length) return;

        // Render top 3 cards in stack
        for (let i = Math.min(currentIndex + 2, cards.length - 1); i >= currentIndex; i--) {
            const cardData = cards[i];
            const card = createCardElement(cardData, i === currentIndex);
            cardStack.appendChild(card);
        }
    }

    function playAudio(url) {
        if (!url) return;
        const audio = new Audio(url);
        audio.play().catch(e => console.error("Audio playback failed", e));
    }

    function createCardElement(data, isTop) {
        const card = document.createElement('div');
        card.className = 'vocab-card';
        card.dataset.id = data.id;

        const meaningsHtml = data.meanings.map((m, index) => `
            <div class="py-3 border-b border-slate-100 last:border-0 w-full text-center">
                ${data.meanings.length > 1 ? `<span class="text-xs font-bold text-indigo-400 block mb-1 uppercase tracking-tighter">Meaning ${index + 1}</span>` : ''}
                <p class="text-lg text-slate-700 leading-relaxed">${m}</p>
            </div>
        `).join('');

        const audioButtonHtml = data.audio_url ? `
            <button class="audio-btn absolute top-4 right-4 p-2 bg-slate-50 rounded-full hover:bg-slate-100 transition-colors" onclick="event.stopPropagation();">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
            </button>
        ` : '';

        const exampleHtml = data.example ? `
            <div class="mt-6 p-4 bg-indigo-50 rounded-xl w-full">
                <span class="text-xs font-bold text-indigo-400 block mb-2 uppercase tracking-tighter">Example</span>
                <p class="text-slate-600 italic">"${data.example}"</p>
            </div>
        ` : '';

        card.innerHTML = `
            <div class="card-inner">
                <div class="card-face card-front">
                    <div class="swipe-indicator know">Know</div>
                    <div class="swipe-indicator dont-know">Don't Know</div>
                    ${audioButtonHtml}
                    <h2 class="text-5xl font-black text-slate-800 tracking-tight text-center break-words w-full px-4">${data.word}</h2>
                    <p class="absolute bottom-10 text-slate-300 text-sm font-medium uppercase tracking-widest animate-pulse">Swipe to reveal</p>
                </div>
                <div class="card-face card-back">
                    <div class="w-full">
                        <h3 class="text-3xl font-black text-slate-800 tracking-tight text-center break-words mb-4">${data.word}</h3>
                        <div class="max-h-64 overflow-y-auto w-full px-2">
                            <div class="space-y-2">
                                ${meaningsHtml}
                            </div>
                            ${exampleHtml}
                        </div>
                    </div>
                    <div class="absolute bottom-8 w-full px-8">
                        <button class="next-btn w-full bg-indigo-600 text-white py-3 rounded-xl font-bold shadow-lg shadow-indigo-100 transition-all hover:bg-indigo-700">Next Card</button>
                    </div>
                </div>
            </div>
        `;

        if (isTop) {
            initCardInteractions(card);
            const audioBtn = card.querySelector('.audio-btn');
            if (audioBtn) {
                audioBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    playAudio(data.audio_url);
                });
            }
        }

        return card;
    }

    function initCardInteractions(card) {
        const inner = card.querySelector('.card-inner');
        const nextBtn = card.querySelector('.next-btn');

        card.addEventListener('mousedown', startDrag);
        card.addEventListener('touchstart', startDrag, { passive: true });

        if (nextBtn) {
            nextBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                nextCard();
            });
        }

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

            const rotate = currentX / 10;
            card.style.transform = `translate(${currentX}px, ${currentY}px) rotate(${rotate}deg)`;

            // Visual feedback
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
                const direction = currentX > 0 ? 1 : -1;
                handleSwipe(card, direction);
            } else {
                card.style.transition = 'transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                card.style.transform = '';
                card.classList.remove('swipe-right', 'swipe-left');
            }

            currentX = 0;
            currentY = 0;
        }
    }

    async function handleSwipe(card, direction) {
        const inner = card.querySelector('.card-inner');
        const cardId = card.dataset.id;
        const isKnown = direction > 0;

        // Update status in background
        fetchWithAuth(`/api/cards/${cardId}/status/`, {
            method: 'POST',
            body: JSON.stringify({ is_known: isKnown })
        }).then(async res => {
            if (res) {
                const data = await res.json();
                if (data.streak !== undefined) {
                    updateStreakUI(data.streak);
                }
            }
        }).catch(err => console.error("Failed to update status", err));

        // Flip and stay
        inner.classList.add('is-flipped');
        card.style.transition = 'transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
        card.style.transform = '';
        card.classList.remove('swipe-right', 'swipe-left');
    }

    function nextCard() {
        currentIndex++;
        updateProgress();
        renderStack();
    }

    // Keyboard support
    document.addEventListener('keydown', (e) => {
        if (currentIndex >= cards.length) return;
        const topCard = cardStack.querySelector('.vocab-card:last-child');
        if (!topCard) return;
        const inner = topCard.querySelector('.card-inner');

        if (e.key === 'ArrowRight' && !inner.classList.contains('is-flipped')) {
            handleSwipe(topCard, 1);
        } else if (e.key === 'ArrowLeft' && !inner.classList.contains('is-flipped')) {
            handleSwipe(topCard, -1);
        } else if ((e.key === 'Enter' || e.key === ' ') && inner.classList.contains('is-flipped')) {
            nextCard();
        }
    });

    replayBtn.addEventListener('click', () => {
        currentIndex = 0;
        completionScreen.classList.add('hidden');
        cardStack.classList.remove('hidden');
        updateProgress();
        renderStack();
    });

    fetchCards();
    fetchStats();
});
