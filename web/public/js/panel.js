class Panel {
    constructor() {
        this.container = document.getElementById("container");
        this.navigationButtons = document.querySelectorAll("ul li");
        this.pages = {
            dashboard: {
                html: `<h1>Dashboard</h1>`,
                script: ``
            },
            agents: {
                html: `<h1>Agents</h1>`,
                script: ``
            },
            listeners: {
                html: `<h1>Listeners</h1>`,
                script: ``
            },
            worldmap: {
                html: `<h1>World Map</h1>`,
                script: ``
            },
            database: {
                html: `<h1>Database</h1>`,
                script: ``
            },
            notifications: {
                html: `<h1>Notifications</h1>`,
                script: ``
            },
            settings: {
                html: `<h1>Settings</h1>`,
                script: ``
            },
            logout: {
                html: `<h1>Logout</h1>`,
                script: ``
            }
        };
        this.init();
    }

    changePage(button) {
        this.navigationButtons.forEach(button => {
            button.classList.remove("active");
        });
        button.classList.add("active");
        this.container.innerHTML = this.pages[button.id]["html"];
        eval(this.pages[button.id]["script"]);
    }

    init() {
        this.changePage(document.getElementById("dashboard"));

        this.navigationButtons.forEach(button => {
            button.addEventListener("click", () => {
                this.changePage(button);
            });
        });
    }
}

new Panel();