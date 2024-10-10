class ProgressBar {
    constructor(selector) {
        this.progressBar = document.querySelector(selector);
        this.width = 0;
    }

    start() {
        this.interval = setInterval(() => {
            this.update();
        }, 25);
    }

    update() {
        if (this.width >= 100) {
            clearInterval(this.interval);
            this.redirect();
        } else {
            this.width++;
            this.progressBar.style.width = this.width + '%';
        }
    }

    redirect() {
        setTimeout(() => {
            window.location = "/login";                
        }, 1500);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const progressBar = new ProgressBar(".progress-bar");
    progressBar.start();
});