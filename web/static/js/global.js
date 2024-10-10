class Cursor {
    constructor() {
        this.cursorElement = document.createElement("span");
        this.cursorElement.className = "cursor";
        document.body.appendChild(this.cursorElement);
        this.init();
    }

    init() {
        document.body.style.cursor = "none";
        document.addEventListener('mousemove', (e) => {
            this.updatePosition(e);
            this.cursorElement.style.display = "block";
        });
    }

    updatePosition(e) {
        this.cursorElement.style.top = `${e.clientY}px`;
        this.cursorElement.style.left = `${e.clientX}px`;
    }
}

new Cursor();