// Daten von Flask abrufen

fetch("/blockchain")
.then(response => response.json())
.then(blocks => {
    // let deklariert den Variablen Name
    let container = document.getElementById("blockchain-container"); // Findet das HTML div Element aus index.js für die Blöcke (Da werden die Blöcke eingefügt)

    blocks.forEach(chainblock => { // Für jeden Block
        let blockDiv = document.createElement("div"); // Erstellt neues HTML Element vom Type div (Wird später für Block Daten genutzt)
        blockDiv.classList.add("chainblock"); // Fügt dem neuen div die CSS-Klasse "block" hinzu fürs design später
        
        // Block Daten in HTML Format. In minimiertem Block wird nur Index angezeigt und in ausgefahrenem Block alle details
        blockDiv.innerHTML = `
        <p class="collapsed">Block:  ${chainblock.index}</p>
        <div class="details">
            <p>Index: ${chainblock.index}</p>
            <p>Hash: ${chainblock.hash}</p>
            <p>Previous Hash: ${chainblock.previous_hash}</p>
            <p>Timestamp: ${chainblock.timestamp}</p>
            <p>Data: ${JSON.stringify(chainblock.data, null, 2)}</p>
        </div>
        `;

        container.appendChild(blockDiv); // Fügt Block zur HTML Seite hinzu
    });
})


// Für das Click Event -> Blöcke werden in expanden zustand gesetzt
document.getElementById("blockchain-container").addEventListener("click", function (event) {
    if (event.target.classList.contains("chainblock")) {
        event.target.classList.toggle("expanded");
    }
});
