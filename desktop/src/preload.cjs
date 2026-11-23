"use strict";
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("sleek", {
  state: () => ipcRenderer.invoke("sleek:state"),
  chooseFolder: () => ipcRenderer.invoke("sleek:folder"),
  start: (request) => ipcRenderer.invoke("sleek:start", request),
  stop: () => ipcRenderer.invoke("sleek:stop"),
  subscribe: (callback) => {
    const handler = (_event, message) => callback(message);
    ipcRenderer.on("sleek:event", handler);
    return () => ipcRenderer.removeListener("sleek:event", handler);
  },
});
