function startNeuroGame(container, checkVictory) {
    container.innerHTML = `<h3>What comes next?</h3>
    <p class="fs-2">🍎 🍌 🍎 ...</p>
    <div class="d-flex justify-content-center gap-3">
        <button class="btn btn-light fs-2" onclick="alert('Nope')">🍎</button>
        <button class="btn btn-light fs-2" onclick="victory()">🍌</button>
    </div>`;
    window.victory = checkVictory;
}