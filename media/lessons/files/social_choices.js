/**
 * Intermediate Behavioral Skill: Social Scenarios
 * Teaches impulse control and situational awareness.
 */
function startNeuroGame(container, victoryCallback) {
    const scenarios = [
        {
            situation: "A friend is using the swing you want. What do you do?",
            options: [
                { text: "Wait for my turn", correct: true, feedback: "Great patience!" },
                { text: "Push them off", correct: false, feedback: "That might hurt them." },
                { text: "Ask to play together", correct: true, feedback: "Nice communicating!" }
            ]
        },
        {
            situation: "The room is getting too loud and you feel upset. What do you do?",
            options: [
                { text: "Scream loudly", correct: false, feedback: "That makes it louder." },
                { text: "Ask for a break", correct: true, feedback: "Good self-advocacy!" },
                { text: "Use my headphones", correct: true, feedback: "Great problem solving!" }
            ]
        }
    ];

    // Pick a random scenario for this session
    const activeScenario = scenarios[Math.floor(Math.random() * scenarios.length)];
    let successCount = 0;

    container.innerHTML = `
        <div class="w-100 animate__animated animate__fadeIn px-3">
            <div class="card border-0 bg-light p-4 mb-4 rounded-4 shadow-sm">
                <h3 class="fw-bold text-dark">${activeScenario.situation}</h3>
            </div>
            <div id="choice-grid" class="d-grid gap-3"></div>
            <div id="feedback-msg" class="mt-4 fw-bold fs-4 d-none"></div>
        </div>
    `;

    const grid = document.getElementById('choice-grid');
    const msg = document.getElementById('feedback-msg');

    activeScenario.options.forEach(option => {
        const btn = document.createElement('button');
        btn.className = "btn btn-white border-2 py-3 rounded-pill shadow-sm fw-bold fs-5 hover-lift";
        btn.style.borderColor = "#f06292";
        btn.innerText = option.text;

        btn.onclick = () => {
            msg.innerText = option.feedback;
            msg.classList.remove('d-none', 'text-success', 'text-danger');
            
            if (option.correct) {
                btn.className = "btn btn-success text-white py-3 rounded-pill shadow";
                msg.classList.add('text-success', 'animate__animated', 'animate__tada');
                // Allow a second for the child to read the positive reinforcement
                setTimeout(() => victoryCallback(), 1500);
            } else {
                btn.className = "btn btn-danger text-white py-3 rounded-pill shadow animate__animated animate__shakeX";
                msg.classList.add('text-danger');
                setTimeout(() => {
                    btn.className = "btn btn-white border-2 py-3 rounded-pill shadow-sm fw-bold fs-5";
                }, 1000);
            }
        };
        grid.appendChild(btn);
    });
}