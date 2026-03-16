/* Save as size_sort.js in your media folder */
function startNeuroGame(container, victoryCallback) {
    container.innerHTML = `
        <div class="d-flex flex-column align-items-center w-100">
            <div id="drop-zones" class="d-flex gap-4 mb-5">
                <div class="zone p-4 rounded-5 border-dashed" data-size="small" style="width:150px; height:150px; border:3px dashed #f06292;">SMALL</div>
                <div class="zone p-4 rounded-5 border-dashed" data-size="large" style="width:200px; height:200px; border:3px dashed #f06292;">LARGE</div>
            </div>
            <div id="items" class="d-flex gap-3">
                <div class="drag-item bg-white shadow-sm p-3 rounded-4" draggable="true" data-size="small">🐭 Mouse</div>
                <div class="drag-item bg-white shadow-sm p-3 rounded-4" draggable="true" data-size="large">🐘 Elephant</div>
            </div>
        </div>
    `;

    let matches = 0;
    const items = container.querySelectorAll('.drag-item');
    const zones = container.querySelectorAll('.zone');

    items.forEach(item => {
        item.ondragstart = (e) => e.dataTransfer.setData("text", e.target.dataset.size);
    });

    zones.forEach(zone => {
        zone.ondragover = (e) => e.preventDefault();
        zone.ondrop = (e) => {
            const data = e.dataTransfer.getData("text");
            if (data === zone.dataset.size) {
                zone.style.background = "#e8f5e9";
                matches++;
                if (matches === 2) victoryCallback(); // Triggers finishLevel()
            }
        };
    });
}