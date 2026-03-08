/**
 * Behavioral Skill: Social Battery Management
 * Goal: Teaches children to recognize when they need a 'break' to stay regulated.
 */
function startNeuroGame(container, victoryCallback) {
    let batteryLevel = 60; // Start at 60%
    
    const activities = [
        { name: "Loud Party", impact: -30, type: 'drain', icon: "🎉" },
        { name: "Quiet Corner", impact: 20, type: 'charge', icon: "📚" },
        { name: "Bright Lights", impact: -20, type: 'drain', icon: "💡" },
        { name: "Noise Headphones", impact: 15, type: 'charge', icon: "🎧" },
        { name: "Deep Breathing", impact: 25, type: 'charge', icon: "🌬️" },
        { name: "Crowded Mall", impact: -40, type: 'drain', icon: "🛍️" }
    ];

    container.innerHTML = `
        <div class="w-100 animate__animated animate__fadeIn">
            <h3 class="fw-bold mb-4">Keep your battery in the <span class="text-success">Green Zone!</span></h3>
            
            <div class="progress mb-5" style="height: 60px; border-radius: 30px; border: 4px solid #333;">
                <div id="battery-bar" class="progress-bar progress-bar-striped progress-bar-animated bg-success" 
                     role="progressbar" style="width: 60%;">
                    <span id="battery-text" class="fw-bold fs-4">60%</span>
                </div>
            </div>

            <div id="activity-grid" class="row g-3 justify-content-center"></div>
        </div>
    `;

    const bar = document.getElementById('battery-bar');
    const text = document.getElementById('battery-text');
    const grid = document.getElementById('activity-grid');

    function updateBattery(amount) {
        batteryLevel = Math.min(100, Math.max(0, batteryLevel + amount));
        bar.style.width = batteryLevel + "%";
        text.innerText = batteryLevel + "%";

        // Color Logic
        if (batteryLevel > 70) bar.className = "progress-bar bg-success";
        else if (batteryLevel > 30) bar.className = "progress-bar bg-warning";
        else bar.className = "progress-bar bg-danger";

        if (batteryLevel >= 100) {
            setTimeout(victoryCallback, 800);
        }
    }

    activities.forEach(act => {
        const col = document.createElement('div');
        col.className = "col-6 col-md-4";
        col.innerHTML = `
            <div class="card h-100 border-2 rounded-4 shadow-sm p-3 cursor-pointer hover-lift">
                <div class="fs-1 mb-2">${act.icon}</div>
                <div class="fw-bold small">${act.name}</div>
                <div class="small ${act.type === 'drain' ? 'text-danger' : 'text-success'}">
                    ${act.impact > 0 ? '+' : ''}${act.impact}%
                </div>
            </div>
        `;
        col.onclick = () => updateBattery(act.impact);
        grid.appendChild(col);
    });
}