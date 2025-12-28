const quizArea = document.getElementById('quiz-area');
const quizScoreEl = document.getElementById('quiz-score');
const quizNumberEl = document.getElementById('quiz-number');
const nextBtn = document.getElementById('nextBtn');
const limitSelect = document.getElementById('quiz-limit');
const restartBtn = document.getElementById('restartBtn');

let score = 0;
let qNumber = 0;
let awaitingNext = false;
let limit = parseInt(limitSelect ? limitSelect.value : '10', 10);

function resetQuiz() {
    score = 0;
    qNumber = 0;
    awaitingNext = false;
    quizArea.innerHTML = '';
    quizScoreEl.textContent = '0';
    quizNumberEl.textContent = '0';
    nextBtn.style.display = '';
    restartBtn.style.display = 'none';
    nextBtn.disabled = true;
}

function setScore(delta) {
    score += delta;
    quizScoreEl.textContent = String(score);
}

function setQuestionNumber(n) {
    qNumber = n;
    quizNumberEl.textContent = String(qNumber);
}

function emojiForPerformance(pct) {
    if (pct >= 0.9) return '🏆 Amazing!';
    if (pct >= 0.75) return '🎉 Great job!';
    if (pct >= 0.5) return '🙂 Nice effort!';
    return '💪 Keep practicing!';
}

function showSummary() {
    const pct = score / limit;
    const headline = emojiForPerformance(pct);
    quizArea.innerHTML = `
        <div class="quiz-card">
            <div class="quiz-prompt" style="font-size:1.3rem;">
                ${headline}
            </div>
            <div class="message message-info">You scored <strong>${score}</strong> out of <strong>${limit}</strong>.</div>
        </div>
    `;
    nextBtn.style.display = 'none';
    restartBtn.style.display = '';
}

function button(label, className = 'btn btn-primary') {
    const btn = document.createElement('button');
    btn.className = className;
    btn.textContent = label;
    return btn;
}

function renderWordToGif(question) {
    const { correct, options_gifs } = question;
    const wrapper = document.createElement('div');
    wrapper.className = 'quiz-card';

    const prompt = document.createElement('div');
    prompt.className = 'quiz-prompt';
    prompt.innerHTML = `Select the correct sign for: <strong>${correct.word}</strong>`;
    wrapper.appendChild(prompt);

    const grid = document.createElement('div');
    grid.className = 'quiz-grid';

    options_gifs.forEach(url => {
        const choice = document.createElement('button');
        choice.className = 'quiz-choice';
        const img = document.createElement('img');
        img.src = url;
        img.alt = 'Sign option';
        choice.appendChild(img);
        choice.addEventListener('click', () => evaluate(url === correct.gif, choice));
        grid.appendChild(choice);
    });

    wrapper.appendChild(grid);
    return wrapper;
}

function renderGifToWord(question) {
    const { correct, options_words } = question;
    const wrapper = document.createElement('div');
    wrapper.className = 'quiz-card';

    const gifWrap = document.createElement('div');
    gifWrap.className = 'quiz-gif';
    const img = document.createElement('img');
    img.src = correct.gif;
    img.alt = 'Sign to identify';
    gifWrap.appendChild(img);

    const prompt = document.createElement('div');
    prompt.className = 'quiz-prompt';
    prompt.textContent = 'What word does this sign represent?';

    const grid = document.createElement('div');
    grid.className = 'quiz-grid words';

    options_words.forEach(word => {
        const choice = document.createElement('button');
        choice.className = 'quiz-choice word';
        choice.textContent = word;
        choice.addEventListener('click', () => evaluate(word === correct.word, choice));
        grid.appendChild(choice);
    });

    wrapper.appendChild(gifWrap);
    wrapper.appendChild(prompt);
    wrapper.appendChild(grid);
    return wrapper;
}

function evaluate(isCorrect, targetBtn) {
    if (awaitingNext) return;
    awaitingNext = true;

    if (isCorrect) {
        targetBtn.classList.add('correct');
        setScore(1);
    } else {
        targetBtn.classList.add('incorrect');
    }

    nextBtn.disabled = false;
}

async function loadQuestion() {
    // Completed?
    if (qNumber >= limit) {
        showSummary();
        return;
    }

    awaitingNext = false;
    nextBtn.disabled = true;
    setQuestionNumber(qNumber + 1);

    quizArea.innerHTML = '<div class="loading"><span class="spinner"></span> Loading question...</div>';
    try {
        const res = await fetch('/quiz-data');
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to load');

        quizArea.innerHTML = '';
        let node;
        if (data.type === 'word_to_gif') {
            node = renderWordToGif(data);
        } else {
            node = renderGifToWord(data);
        }
        quizArea.appendChild(node);
    } catch (e) {
        quizArea.innerHTML = '<div class="message message-error">Unable to load question. Please try again.</div>';
    }
}

nextBtn.addEventListener('click', () => {
    loadQuestion();
});

limitSelect && limitSelect.addEventListener('change', () => {
    limit = parseInt(limitSelect.value, 10);
    resetQuiz();
    loadQuestion();
});

restartBtn.addEventListener('click', () => {
    resetQuiz();
    loadQuestion();
});

// bootstrap
document.addEventListener('DOMContentLoaded', () => {
    resetQuiz();
    loadQuestion();
});
