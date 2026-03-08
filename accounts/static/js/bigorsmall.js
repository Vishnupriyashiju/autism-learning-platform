function startNeuroGame(container, checkVictory) {
    container.innerHTML = `<h3>Tap the BIGGEST Object</h3>
    <div class="d-flex align-items-end justify-content-center gap-4">
        <div onclick="victory()" style="font-size:5rem; cursor:pointer;">🍎</div>
        <div onclick="alert('Too small!')" style="font-size:2rem; cursor:pointer;">🍎</div>
    </div>`;
    window.victory = checkVictory;
}