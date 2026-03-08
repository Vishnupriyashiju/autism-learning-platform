/**
 * Fine Motor Skill: Precision Tracing
 * Goal: Improve steady hand movement and coordination.
 */
function startNeuroGame(container, victoryCallback) {
    container.innerHTML = `
        <div class="w-100 animate__animated animate__fadeIn text-center">
            <h3 class="fw-bold mb-3">Follow the path to the <span class="text-warning">Big Star!</span></h3>
            <canvas id="traceCanvas" width="400" height="400" class="bg-white rounded-4 shadow-sm border border-2 border-pink" style="touch-action: none; cursor: crosshair;"></canvas>
            <div class="mt-3">
                <button id="resetTrace" class="btn btn-outline-secondary btn-sm rounded-pill">Reset Path</button>
            </div>
        </div>
    `;

    const canvas = document.getElementById('traceCanvas');
    const ctx = canvas.getContext('2d');
    const resetBtn = document.getElementById('resetTrace');
    
    let isDrawing = false;
    const pathPoints = [
        {x: 50, y: 350, type: 'start'},
        {x: 100, y: 150, type: 'waypoint'},
        {x: 300, y: 250, type: 'waypoint'},
        {x: 350, y: 50, type: 'end'}
    ];

    function drawPath() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw the "Safe Zone" Path
        ctx.strokeStyle = "#fdf2f5";
        ctx.lineWidth = 40;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.beginPath();
        ctx.moveTo(pathPoints[0].x, pathPoints[0].y);
        for(let i=1; i<pathPoints.length; i++) ctx.lineTo(pathPoints[i].x, pathPoints[i].y);
        ctx.stroke();

        // Draw Waypoints
        pathPoints.forEach(p => {
            ctx.fillStyle = p.type === 'end' ? '#ffc107' : '#f06292';
            ctx.beginPath();
            ctx.arc(p.x, p.y, 15, 0, Math.PI * 2);
            ctx.fill();
            if(p.type === 'end') {
                ctx.font = "20px FontAwesome";
                ctx.fillStyle = "white";
                ctx.fillText("⭐", p.x-10, p.y+7);
            }
        });
    }

    function handleMove(e) {
        if (!isDrawing) return;
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX || e.touches[0].clientX) - rect.left;
        const y = (e.clientY || e.touches[0].clientY) - rect.top;

        // Check if user reached the end
        const distToEnd = Math.hypot(x - pathPoints[3].x, y - pathPoints[3].y);
        if(distToEnd < 20) {
            isDrawing = false;
            victoryCallback();
        }

        // Visual feedback for tracing
        ctx.strokeStyle = "#f06292";
        ctx.lineWidth = 5;
        ctx.lineTo(x, y);
        ctx.stroke();
    }

    canvas.addEventListener('mousedown', (e) => { isDrawing = true; ctx.beginPath(); });
    canvas.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', () => isDrawing = false);
    
    // Touch support for tablets
    canvas.addEventListener('touchstart', (e) => { e.preventDefault(); isDrawing = true; ctx.beginPath(); });
    canvas.addEventListener('touchmove', handleMove);

    resetBtn.onclick = drawPath;
    drawPath();
}