#!/usr/bin/env node

const fs                   = require("node:fs");
const path                 = require("node:path");
const https                = require("node:https");
const crypto               = require("node:crypto");
const express              = require("express");
const session              = require("express-session");
const socketIO             = require("socket.io");
const { Command, program } = require("commander");

class GhostOps {
    constructor() {
        this.banner = `
┏┓┓     ┏┓   
┃┓┣┓┏┓┏╋┃┃┏┓┏
┗┛┛┗┗┛┛┗┗┛┣┛┛
          ┛  `;
        this.metadt = JSON.parse(fs.readFileSync(path.join(__dirname, "package.json"), "utf-8"));
    }

    showBanner() {
        console.log(this.banner);
        console.log(`
[#] CodeName    :: ${this.metadt.name}
[#] Description :: ${this.metadt.description}
[#] Version     :: ${this.metadt.version}
[#] Author      :: ${this.metadt.author}
[#] License     :: ${this.metadt.license}
[#] Repository  :: ${this.metadt.repository.url.split("+")[1]}
`       );
    }

    webIndex(req, res) {
        res.sendFile(path.join(__dirname, "web", "pages", "index.html"));
    }

    webLogin(req, res) {
        res.sendFile(path.join(__dirname, "web", "pages", "login.html"));
    }

    webPanel(req, res) {
        res.sendFile(path.join(__dirname, "web", "pages", "panel.html"));
    }
    
    init(host, port, sslc, sslk) {
        const app = express();

        const httpsServer = https.createServer(
            {
                key: fs.readFileSync(sslk), cert: fs.readFileSync(sslc)
            },
            app
        );

        const socktServer = new socketIO.Server(httpsServer);

        const sessionMgmt = session({
            secret: crypto.randomBytes(32).toString("hex"),
            resave: false,
            saveUninitialized: true,
            cookie: { secure: true }
        });

        app.use(sessionMgmt);
        app.use(express.json());
        app.use(express.static(path.join(__dirname, "web", "static")));

        app.use((err, req, res, next) => {
            res.status(500).json({ message: "Internal server error" });
        });

        socktServer.engine.use(sessionMgmt);

        app.get("/",      (req, res) => this.webIndex(req, res));
        app.get("/login", (req, res) => this.webLogin(req, res));
        app.get("/panel", (req, res) => this.webPanel(req, res));

        httpsServer.on("error", (err) => {
            console.error(err.message);
        });

        httpsServer.listen(port, host, () => {
            console.log(`[*] GhostOps server is running at https://${host}:${port}`);
        });

        process.on("SIGINT", () => {
            process.exit(0);
        })
    }

    main() {
        this.showBanner();

        const program = new Command();
        
        program
        .name(this.metadt.name)
        .description(this.metadt.description)
        
        program
        .requiredOption("--host <host>", "IPv4 host or domain")
        .requiredOption("--port <port>", "Port number 0-65535")
        .requiredOption("--sslc <path>", "Path to SSL crt")
        .requiredOption("--sslk <path>", "Path to SSL key")

        program
        .parse(process.argv);
        
        const args = program.opts();

        this.init(args.host, args.port, args.sslc, args.sslk)
    }
}

new GhostOps().main()