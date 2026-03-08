function startNeuroGame(container, checkVictory) {
    container.innerHTML = `<h3>Match the Shape</h3><div id="target" style="font-size:4rem; margin:20px;">⭐</div>
    <div id="choices" class="d-flex justify-content-center gap-3">
        <button class="btn btn-light p-4 fs-2" onclick="this.innerText==='⭐'?victory():alert('Try Again!')">🔵</button>
        <button class="btn btn-light p-4 fs-2" onclick="this.innerText==='⭐'?victory():alert('Try Again!')">⭐</button>
        <button class="btn btn-light p-4 fs-2" onclick="this.innerText==='⭐'?victory():alert('Try Again!')">📐</button>
    </div>`;
    window.victory = checkVictory;
}