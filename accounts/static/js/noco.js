function startNeuroGame(container, checkVictory) {
    container.innerHTML = `<h3>Click in Order: 1, 2, 3</h3>
    <div class="d-flex justify-content-center gap-3">
        <button id="b2" class="btn btn-pink p-4" onclick="step(2)">2</button>
        <button id="b1" class="btn btn-pink p-4" onclick="step(1)">1</button>
        <button id="b3" class="btn btn-pink p-4" onclick="step(3)">3</button>
    </div>`;
    let current = 1;
    window.step = (n) => { if(n===current) { document.getElementById('b'+n).style.opacity='0.3'; current++; } if(current>3) checkVictory(); };
}