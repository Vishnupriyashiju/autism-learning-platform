/**
 * neuro-custom-engine v1.0
 * This function is called by system_player.html
 */
function startNeuroGame(gameContainer, winCallback) {
    // 1. Clear the container and add custom HTML
    gameContainer.innerHTML = `
        <div id="vocal-game" class="text-center p-4 rounded-4 shadow-sm" style="border: 3px solid #f06292; background: #fffafa;">
            <h3 class="text-pink fw-bold mb-4">Vocal Recognition Game</h3>
            <p class="text-muted">Click the microphone when you see the pink star!</p>
            <div id="game-target" class="mx-auto d-flex align-items-center justify-content-center shadow" 
                 style="width: 150px; height: 150px; background: white; border-radius: 50%; font-size: 3rem; cursor: pointer;">
                 ❓
            </div>
        </div>
    `;

    const target = document.getElementById('game-target');
    
    // 2. Simple game logic: Change icon every 2 seconds
    const interval = setInterval(() => {
        const isTarget = Math.random() > 0.5;
        target.innerText = isTarget ? "⭐" : "☁️";
        target.dataset.active = isTarget;
    }, 2000);

    // 3. Handle the win condition
    target.onclick = () => {
        if (target.dataset.active === "true") {
            clearInterval(interval);
            target.style.background = "#e8f5e9";
            target.innerText = "✅";
            // Trigger the system's victory UI
            winCallback();
        }
    };
}