"use strict";
const { app, BrowserWindow, dialog, ipcMain, screen, session } = require("electron");
const { spawn } = require("node:child_process");
const path = require("node:path");
const readline = require("node:readline");
const { pathToFileURL } = require("node:url");
const { jobArgs, dimensions } = require("./job.cjs");

const view = path.join(__dirname, "index.html");
const viewURL = pathToFileURL(view).href;
let window;
let directory;
let active;

function requireView(event) {
  if (!window || event.sender !== window.webContents ||
      event.senderFrame !== event.sender.mainFrame || event.senderFrame?.url !== viewURL) {
    throw new Error("Untrusted window.");
  }
}

function notify(data) {
  if (window && !window.isDestroyed()) window.webContents.send("sleek:event", data);
}

function enginePath() {
  const name = process.platform === "win32" ? "sleek.exe" : "sleek";
  return app.isPackaged
    ? path.join(process.resourcesPath, "backend", name)
    : path.resolve(__dirname, "../../engine/target/release", name);
}

function stop() {
  if (!active || active.canceled || !active.process.pid) return false;
  const p = active.process;
  if (process.platform === "win32") {
    const systemRoot = process.env.SystemRoot || "C:\\Windows";
    const killer = spawn(path.join(systemRoot, "System32", "taskkill.exe"),
      ["/PID", String(p.pid), "/T", "/F"], { windowsHide: true, stdio: "ignore" });
    killer.on("error", () => p.kill());
  } else {
    try { process.kill(-p.pid, "SIGTERM"); } catch { p.kill(); }
  }
  active.canceled = true;
  return true;
}

ipcMain.handle("sleek:folder", async (event) => {
  requireView(event);
  if (active) return null;
  const result = await dialog.showOpenDialog(window, { defaultPath: directory, properties: ["openDirectory", "createDirectory"] });
  if (result.canceled) return null;
  directory = result.filePaths[0];
  return directory;
});

ipcMain.handle("sleek:state", (event) => {
  requireView(event);
  return { directory };
});

ipcMain.handle("sleek:start", (event, input) => {
  requireView(event);
  if (active) throw new Error("A download is already running.");
  const args = jobArgs(input, directory);
  const processHandle = spawn(enginePath(), args, {
    shell: false, windowsHide: true, detached: process.platform !== "win32", stdio: ["ignore", "pipe", "pipe"]
  });
  active = { process: processHandle, canceled: false };
  const stdout = readline.createInterface({input: processHandle.stdout, crlfDelay: Infinity});
  const stderr = readline.createInterface({input: processHandle.stderr, crlfDelay: Infinity});
  stdout.on("line", (text) => {
    try {
      const event = JSON.parse(text);
      if (event.schema_version === 1) notify(event);
    } catch { /* Engine stdout is versioned JSON, not arbitrary renderer markup. */ }
  });
  stderr.on("line", (text) => notify({event: "diagnostic", message: text.slice(0, 1500)}));
  processHandle.on("error", () => notify({event: "error", message: "Unable to start the bundled engine."}));
  processHandle.on("close", (code) => {
    stdout.close();
    stderr.close();
    const canceled = active?.canceled === true;
    active = undefined;
    notify({event: "exit", code, canceled});
  });
  return true;
});

ipcMain.handle("sleek:stop", (event) => { requireView(event); return stop(); });

function createWindow() {
  const area = screen.getDisplayNearestPoint(screen.getCursorScreenPoint()).workAreaSize;
  window = new BrowserWindow({
    ...dimensions(area), show: false, autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      sandbox: true, contextIsolation: true, nodeIntegration: false,
    },
  });
  window.webContents.on("will-navigate", (event) => event.preventDefault());
  window.webContents.setWindowOpenHandler(() => ({action: "deny"}));
  window.on("closed", () => { stop(); window = undefined; });
  window.once("ready-to-show", () => window.show());
  void window.loadFile(view);
}
app.whenReady().then(() => {
  directory = app.getPath("downloads");
  session.defaultSession.setPermissionRequestHandler((_webContents, _permission, callback) => callback(false));
  createWindow();
  app.on("activate", () => { if (!window) createWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
