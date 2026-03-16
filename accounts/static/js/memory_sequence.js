/* Save as memory_sequence.js in your media folder */
function startNeuroGame(container, victoryCallback) {
    const icons = ['fa-star', 'fa-heart', 'fa-moon', 'fa-sun'];
    let sequence = [];
    let userStep = 0;

    container.innerHTML = `
        <div class="text-center">
            <div id="status-msg" class="mb-4 fw-bold text-pink">Watch the Pattern...</div>
            <div id="grid" class="d-flex justify-content-center gap-3">
                ${icons.map((icon, i) => `
                    <button class="btn btn-light p-4 rounded-4 shadow-sm icon-btn" data-index="${i}">
                        <i class="fas ${icon} fa-2x text-pink"></i>
                    </button>
                `).join('')}
            </div>
        </div>
    `;

    function playSequence() {
        sequence.push(Math.floor(Math.random() * 4));
        let i = 0;
        const interval = setInterval(() => {
            const btn = container.querySelectorAll('.icon-btn')[sequence[i]];
            btn.classList.add('animate__animated', 'animate__flash', 'bg-soft-pink');
            setTimeout(() => btn.classList.remove('animate__animated', 'animate__flash', 'bg-soft-pink'), 500);
            i++;
            if (i >= sequence.length) {
                clearInterval(interval);
                document.getElementById('status-msg').innerText = "Your Turn!";
            }
        }, 800);
    }

    container.querySelectorAll('.icon-btn').forEach((btn, index) => {
        btn.onclick = () => {
            if (index == sequence[userStep]) {
                userStep++;
                if (userStep === sequence.length) {
                    if (sequence.length === 3) victoryCallback(); // Win after 3 rounds
                    else {
                        userStep = 0;
                        setTimeout(playSequence, 1000);
                    }
                }
            } else {
                alert("Try again! Watch closely.");
                sequence = []; userStep = 0; playSequence();
            }
        };
    });

    playSequence();
}