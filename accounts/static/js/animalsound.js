function startNeuroGame(container, checkVictory) {
    container.innerHTML = `<h3>Who says 'Meow'?</h3>
    <div class="d-flex justify-content-center gap-3">
        <button class="btn btn-light fs-1" onclick="victory()">🐱</button>
        <button class="btn btn-light fs-1" onclick="alert('Woof!')">🐶</button>
        <button class="btn btn-light fs-1" onclick="alert('Quack!')">🦆</button>
    </div>`;
    window.victory = checkVictory;
}