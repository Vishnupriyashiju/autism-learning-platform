/**
 * Social Skill: The Conversation Tree
 * Goal: Teaches situational awareness and polite turn-taking.
 */
function startNeuroGame(container, victoryCallback) {
    const steps = [
        {
            prompt: "A friend says: 'Hi! I got a new toy today!' What do you say?",
            options: [
                { text: "That sounds cool! What is it?", correct: true, feedback: "Great! You asked a question to keep talking." },
                { text: "I like pizza.", correct: false, feedback: "That's off-topic. Try to talk about the toy." },
                { text: "Can I see it?", correct: true, feedback: "Nice! Showing interest is a great social skill." }
            ]
        },
        {
            prompt: "The friend shows you the toy. You have one just like it. What do you say?",
            options: [
                { text: "I have that too! We can play together.", correct: true, feedback: "Perfect! Finding common ground is great." },
                { text: "Mine is better than yours.", correct: false, feedback: "That might hurt your friend's feelings." },
                { text: "Wow, it looks fun!", correct: true, feedback: "Kind words make friends happy!" }
            ]
        }
    ];

    let currentStep = 0;

    function renderStep() {
        const data = steps[currentStep];
        container.innerHTML = `
            <div class="w-100 animate__animated animate__fadeIn">
                <div class="card border-0 bg-light p-4 mb-4 rounded-4 shadow-sm">
                    <h3 class="fw-bold text-dark"><i class="fas fa-comments text-pink me-2"></i>${data.prompt}</h3>
                </div>
                <div id="choice-buttons" class="d-grid gap-3"></div>
                <div id="social-feedback" class="mt-4 fw-bold fs-4 d-none"></div>
            </div>
        `;

        const grid = document.getElementById('choice-buttons');
        const feedback = document.getElementById('social-feedback');

        data.options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = "btn btn-white border-2 py-3 rounded-pill shadow-sm fw-bold fs-5 transition-all";
            btn.style.borderColor = "#f06292";
            btn.innerText = opt.text;

            btn.onclick = () => {
                feedback.innerText = opt.feedback;
                feedback.classList.remove('d-none', 'text-success', 'text-danger');
                
                if (opt.correct) {
                    btn.className = "btn btn-success text-white py-3 rounded-pill shadow";
                    feedback.classList.add('text-success', 'animate__animated', 'animate__pulse');
                    setTimeout(() => {
                        currentStep++;
                        if (currentStep < steps.length) renderStep();
                        else victoryCallback();
                    }, 2000);
                } else {
                    btn.className = "btn btn-danger text-white py-3 rounded-pill shadow animate__animated animate__shakeX";
                    feedback.classList.add('text-danger');
                    setTimeout(() => {
                        btn.className = "btn btn-white border-2 py-3 rounded-pill shadow-sm fw-bold fs-5";
                    }, 1500);
                }
            };
            grid.appendChild(btn);
        });
    }

    renderStep();
}