/**
 * neuro-custom-engine v1.2 - Voice Activated
 */
async function startNeuroGame(gameContainer, winCallback) {
    // 1. Setup the UI
    gameContainer.innerHTML = `
        <div id="vocal-game" class="text-center p-4 rounded-5 shadow-lg" style="border: 4px solid #f06292; background: white; max-width: 500px; margin: 0 auto;">
            <h3 class="text-pink fw-bold mb-3">🎤 Voice Activation Mode</h3>
            <p class="text-muted mb-4">Make a sound when the <b>Golden Star</b> appears!</p>
            
            <div id="game-target" class="mx-auto d-flex align-items-center justify-content-center shadow-sm mb-3" 
                 style="width: 200px; height: 200px; background: #fdf2f5; border-radius: 50%; border: 8px solid #fff;">
                 <i class="fas fa-microphone fa-3x text-pink animate__animated animate__pulse animate__infinite"></i>
            </div>
            
            <div class="progress mb-3" style="height: 10px;">
                <div id="mic-bar" class="progress-bar bg-pink" style="width: 0%"></div>
            </div>
            <small class="text-muted">Mic Sensitivity: <span id="mic-val">0</span>%</small>
        </div>
    `;

    const target = document.getElementById('game-target');
    const micBar = document.getElementById('mic-bar');

    // 2. Initialize Microphone
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        const microphone = audioContext.createMediaStreamSource(stream);
        const javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);

        analyser.smoothingTimeConstant = 0.8;
        analyser.fftSize = 1024;
        microphone.connect(analyser);
        analyser.connect(javascriptNode);
        javascriptNode.connect(audioContext.destination);

        // 3. Game State Loop
        let isTargetVisible = false;
        const gameInterval = setInterval(() => {
            isTargetVisible = Math.random() > 0.5;
            if (isTargetVisible) {
                target.innerHTML = `<img src="https://cdn-icons-png.flaticon.com/512/1828/1828884.png" width="120">`;
                target.style.borderColor = "#f06292";
            } else {
                target.innerHTML = `<img src="https://cdn-icons-png.flaticon.com/512/414/414927.png" width="120" style="opacity: 0.3;">`;
                target.style.borderColor = "#e0e0e0";
            }
        }, 2000);

        // 4. Voice Detection Logic
        javascriptNode.onaudioprocess = () => {
            const array = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(array);
            let values = 0;
            for (let i = 0; i < array.length; i++) { values += array[i]; }
            const average = values / array.length;
            const volume = Math.round(average);
            
            micBar.style.width = volume + "%";
            
            // If sound is loud enough and star is visible, they win!
            if (volume > 40 && isTargetVisible) {
                clearInterval(gameInterval);
                javascriptNode.onaudioprocess = null; // Stop listening
                stream.getTracks().forEach(track => track.stop()); // Close mic
                
                target.style.background = "#e8f5e9";
                target.innerHTML = `<i class="fas fa-check-circle fa-5x text-success animate__animated animate__bounceIn"></i>`;
                setTimeout(winCallback, 1500);
            }
        };

    } catch (err) {
        target.innerHTML = `<p class="text-danger">Microphone access denied.</p>`;
    }
}