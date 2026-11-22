"use strict";
const path = require("node:path");

function jobArgs(input, directory) {
  if (!input || typeof input.url !== "string" || input.url.length > 4096 ||
      !["audio", "video"].includes(input.mode) || typeof input.comments !== "boolean" ||
      !path.isAbsolute(directory)) throw new Error("Invalid download request.");
  const url = new URL(input.url);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password)
    throw new Error("Enter an HTTP or HTTPS URL without credentials.");
  const args = ["download", url.href, "--" + input.mode, "--output", directory, "--json"];
  if (!input.comments) args.push("--no-comments");
  return args;
}

function dimensions(workArea) {
  const width = Math.min(workArea.width, 820);
  const height = Math.min(workArea.height, 620);
  return { width, height, minWidth: Math.min(width, 440), minHeight: Math.min(height, 420) };
}

module.exports = { jobArgs, dimensions };
