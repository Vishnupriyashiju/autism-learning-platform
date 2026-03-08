/**
 * neuro-custom-engine v1.3 - Communication Request Builder
 */
function startNeuroGame(gameContainer, winCallback) {
    // 1. Setup the UI with a sentence strip
    gameContainer.innerHTML = `
        <div id="comm-game" class="text-center p-4 rounded-5 shadow-lg" style="border: 4px solid #4fc3f7; background: white; max-width: 600px; margin: 0 auto;">
            <h3 class="text-info fw-bold mb-3">🗣️ I Want...</h3>
            <p class="text-muted mb-4">Drag the <b>Apple</b> to the box to ask for a snack!</p>
            
            <div class="d-flex justify-content-center align-items-center gap-3 mb-5 p-3 bg-light rounded-4 border-dashed border-2">
                <div class="p-2 border rounded bg-white fw-bold">I WANT</div>
                <div id="drop-zone" class="d-flex align-items-center justify-content-center" 
                     style="width: 100px; height: 100px; border: 3px dashed #4fc3f7; border-radius: 15px; background: #e3f2fd;">
                     ?
                </div>
            </div>

            <div class="d-flex justify-content-center gap-4">
                <div id="target-item" draggable="true" class="p-2 border rounded-4 shadow-sm bg-white cursor-pointer" style="width: 110px;">
                    <img src="https://cdn-icons-png.flaticon.com/512/415/415733.png" width="80">
                    <div class="small fw-bold mt-2">APPLE</div>
                </div>
                <div id="wrong-item" draggable="true" class="p-2 border rounded-4 shadow-sm bg-white opacity-50" style="width: 110px;">
                    <img src="https://cdn-icons-png.flaticon.com/512/2589/2589175.png" width="80">
                    <div class="small fw-bold mt-2">SOCK</div>
                </div>
            </div>
        </div>
    `;

    const target = document.getElementById('target-item');
    const dropZone = document.getElementById('drop-zone');

    // 2. Drag and Drop Logic
    target.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', 'correct');
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault(); // Required to allow drop
        dropZone.style.background = "#bbdefb";
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.background = "#e3f2fd";
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        const data = e.dataTransfer.getData('text/plain');

        if (data === 'correct') {
            // Success State
            dropZone.innerHTML = `<img src="https://cdn-icons-png.flaticon.com/512/415/415733.png" width="70" class="animate__animated animate__bounceIn">`;
            dropZone.style.border = "3px solid #4caf50";
            dropZone.style.background = "#e8f5e9";
            
            // Winning feedback
            const msg = new SpeechSynthesisUtterance("I want apple"); // Text-to-speech feedback
            window.speechSynthesis.speak(msg);

            setTimeout(winCallback, 2000);
        }
    });
}