"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const { jobArgs, dimensions } = require("./job.cjs");
test("audio and video use the same machine-oriented engine contract", () => {
  const directory = path.resolve("My Downloads");
  for (const mode of ["audio", "video"]) {
    const a = jobArgs({ url: "https://example.com/a?title=one%20two", mode, comments: true }, directory);
    assert.deepEqual(a, ["download", "https://example.com/a?title=one%20two", "--" + mode, "--output", directory, "--json"]);
  }
});
test("arbitrary protocols, credentials and options are rejected", () => {
  const directory = path.resolve(".");
  for (const url of ["file:///etc/passwd", "https://x:secret@example.com", "--execute"]) {
    assert.throws(() => jobArgs({ url, mode: "audio", comments: true }, directory));
  }
  assert.throws(() => jobArgs({ url: "https://example.com", mode: "--exec", comments: false }, directory));
});
test("window constraints never exceed the available work area", () => {
  assert.deepEqual(dimensions({ width: 320, height: 380 }), {width:320,height:380,minWidth:320,minHeight:380});
  assert.deepEqual(dimensions({ width: 1024, height: 768 }), {width:820,height:620,minWidth:440,minHeight:420});
});
