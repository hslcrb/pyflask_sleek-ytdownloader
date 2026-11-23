"use strict";
const get = (id) => document.getElementById(id);
const start = get("start"), stop = get("stop"), folder = get("folder");
const progress = document.querySelector("progress");
const log = get("log"), status = get("status");
const lines = [];
const add = (text) => {
  lines.push(String(text).slice(0, 1600));
  if (lines.length > 60) lines.shift();
  log.textContent = lines.join("\n");
};
const idle = () => { start.disabled = false; stop.disabled = true; folder.disabled = false; };
window.sleek.state().then(({directory}) => { get("directory").textContent = directory; })
  .catch(() => { status.textContent = "Unable to load the download folder."; });
folder.onclick = async () => {
  try {
    const dir = await window.sleek.chooseFolder();
    if (dir) get("directory").textContent = dir;
  } catch (error) { status.textContent = error.message; }
};
document.querySelector("form").onsubmit = async (event) => {
  event.preventDefault();
  if (start.disabled) return;
  lines.length = 0;
  log.textContent = "";
  progress.removeAttribute("value");
  status.textContent = "Starting…";
  start.disabled = folder.disabled = true;
  stop.disabled = false;
  try { await window.sleek.start({url:get("url").value,mode:get("mode").value,comments:get("comments").checked}); }
  catch (error) { status.textContent = error.message; progress.value = 0; idle(); }
};
stop.onclick = async () => {
  try {
    if (await window.sleek.stop()) { stop.disabled = true; status.textContent = "Cancelling…"; }
  } catch (error) { status.textContent = error.message; }
};
window.sleek.subscribe((message) => {
  switch (message.event) {
    case "started": status.textContent = "Downloading…"; break;
    case "progress": {
      const n = message.total_bytes > 0 && typeof message.downloaded_bytes === "number" ?
        Math.min(100, message.downloaded_bytes * 100 / message.total_bytes) : null;
      if (n === null) progress.removeAttribute("value");
      else progress.value = n;
      status.textContent = n === null ? "Downloading…" : `Downloading… ${n.toFixed(1)}%`;
      break;
    }
    case "saved":
      add(message.path);
      if (message.info_json) add(message.info_json);
      if (message.description) add(message.description);
      break;
    case "completed": progress.value = 100; status.textContent = "Download complete"; break;
    case "diagnostic": add(message.message); break;
    case "error": add(message.message); status.textContent = message.message; break;
    case "exit":
      if (message.canceled) { progress.value = 0; status.textContent = "Cancelled"; }
      else if (message.code !== 0) { progress.value = 0; status.textContent = "Download failed. See download details."; }
      idle();
      break;
  }
});
