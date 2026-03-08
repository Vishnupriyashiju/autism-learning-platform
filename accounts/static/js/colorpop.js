function startNeuroGame(container, checkVictory) {
    let score = 0;
    container.innerHTML = `<h3>Pop 3 Pink Stars</h3><div id="game-box" class="position-relative" style="height:300px;"></div>`;
    const box = document.getElementById('game-box');
    const spawn = () => {
        const isPink = Math.random() > 0.5;
        const btn = document.createElement('button');
        btn.innerHTML = '⭐'; btn.className = `btn position-absolute rounded-circle ${isPink?'btn-pink':'btn-primary'}`;
        btn.style.left = Math.random()*80+'%'; btn.style.top = Math.random()*80+'%';
        btn.onclick = () => { if(isPink) score++; btn.remove(); if(score>=3) checkVictory(); };
        box.appendChild(btn); setTimeout(() => btn.remove(), 2000);
    };
    const timer = setInterval(spawn, 1000);
}