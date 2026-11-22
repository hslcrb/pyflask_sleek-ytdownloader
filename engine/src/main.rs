use serde_json::{Value, json};
use std::{
    env, fs,
    io::{self, BufRead, BufReader, Write},
    path::{Path, PathBuf},
    process::{Command, ExitCode, Stdio},
};
use url::Url;

const HELP: &str = "Sleek: download media and metadata.
Usage:
  sleek download URL [--video | --audio] [--output DIR] [--no-comments] [--json]
  sleek doctor [--json]
  sleek --help
  sleek --version
By default, save a video, its description and info JSON, and embed tags.
Available comments are included in info JSON. --audio exports MP3.
--json emits one JSON event per line on stdout. Diagnostics go to stderr.
";
const PROGRESS: &str = "sleek.progress:";
const SAVED: &str = "sleek.saved:";

#[derive(Debug)]
struct Download {
    url: String,
    output: PathBuf,
    audio: bool,
    comments: bool,
}

fn parse_download(args: &[String]) -> Result<Download, &'static str> {
    let arg = args.first().ok_or("Provide an HTTP or HTTPS URL.")?;
    let url = Url::parse(arg).map_err(|_| "Provide a valid HTTP or HTTPS URL.")?;
    if !matches!(url.scheme(), "http" | "https")
        || url.host().is_none() || !url.username().is_empty() || url.password().is_some()
    {
        return Err("Use an HTTP or HTTPS URL without credentials.");
    }
    let mut output = None;
    let mut mode = None;
    let mut comments = true;
    let mut index = 1;
    while index < args.len() {
        match args[index].as_str() {
            "--audio" if mode.is_none() => mode = Some(true),
            "--video" if mode.is_none() => mode = Some(false),
            "--no-comments" if comments => comments = false,
            "--output" if output.is_none() => {
                index += 1;
                let v = args.get(index).filter(|v| !v.is_empty()).ok_or("Provide an output directory.")?;
                output = Some(PathBuf::from(v));
            }
            _ => return Err("Unknown or repeated option. See --help."),
        }
        index += 1;
    }
    Ok(Download {
        url: url.into(),
        output: output.unwrap_or_else(|| PathBuf::from(".")),
        audio: mode.unwrap_or(false),
        comments,
    })
}

fn download_args(job: &Download, ffmpeg: &Path, deno: Option<&Path>) -> Vec<std::ffi::OsString> {
    let mut args: Vec<std::ffi::OsString> = [
        "--ignore-config", "--no-playlist", "--playlist-items", "1", "--no-overwrites", "--no-color",
        "--newline", "--progress", "--progress-delta", "0.5",
        "--progress-template", "download:sleek.progress:%(progress)j",
        "--print", "after_move:sleek.saved:%(filepath)j", "--no-simulate",
        "--windows-filenames", "-o", "%(title).150B [%(id)s].%(ext)s",
        "--write-info-json", "--write-description", "--embed-metadata",
        "--no-embed-info-json",
    ].into_iter().map(Into::into).collect();
    args.push("--ffmpeg-location".into());
    args.push(ffmpeg.as_os_str().to_owned());
    if let Some(deno) = deno {
        let mut runtime = std::ffi::OsString::from("deno:");
        runtime.push(deno);
        args.extend(["--js-runtimes".into(), runtime]);
    }
    if job.comments { args.push("--write-comments".into()); }
    else { args.push("--no-write-comments".into()); }
    if job.audio {
        args.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"].into_iter().map(Into::into));
    } else {
        args.extend(["-f", "bv*+ba/b", "--merge-output-format", "mp4"].into_iter().map(Into::into));
    }
    args.extend(["--".into(), job.url.as_str().into()]);
    args
}

fn executable(name: &str) -> Option<PathBuf> {
    let filename = format!("{name}{}", env::consts::EXE_SUFFIX);
    let installed = env::current_exe().ok()?.parent()?.to_path_buf();
    let dirs = [installed.join("tools"), installed.clone()];
    dirs.into_iter().chain(env::var_os("PATH").into_iter().flat_map(|p| env::split_paths(&p).collect::<Vec<_>>()))
        .filter(|p| p.is_absolute()).map(|p| p.join(&filename)).find(|p| p.is_file())
}

fn child(tool: &Path) -> Command {
    let cmd = Command::new(tool);
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        let mut cmd = cmd;
        cmd.creation_flags(0x08000000);
        cmd
    }
    #[cfg(not(windows))]
    cmd
}

struct Reporter<W> { out: W, json: bool }
impl<W: Write> Reporter<W> {
    fn send(&mut self, event: &str, body: Value) -> io::Result<()> {
        if self.json {
            let mut body = body.as_object().cloned().unwrap_or_default();
            body.insert("schema_version".into(), json!(1));
            body.insert("event".into(), json!(event));
            writeln!(self.out, "{}", Value::Object(body))?;
        } else if event == "saved" {
            writeln!(self.out, "Saved: {}", body["path"].as_str().unwrap_or_default())?;
        } else if event == "doctor" {
            writeln!(self.out, "{}", body)?;
        }
        self.out.flush()
    }
    fn fail(&mut self, code: &str, message: &str, status: u8) -> u8 {
        eprintln!("Error: {message}");
        let _ = self.send("error", json!({"code":code,"message":message}));
        status
    }
}

fn run_download(job: Download, report: &mut Reporter<impl Write>) -> u8 {
    let (Some(ytdlp), Some(ffmpeg), Some(_)) = (executable("yt-dlp"), executable("ffmpeg"), executable("ffprobe")) else {
        return report.fail("dependency_missing", "Install yt-dlp, FFmpeg and FFprobe, then run sleek doctor.", 3);
    };
    if fs::create_dir_all(&job.output).is_err() {
        return report.fail("output_unavailable", "Could not create the output directory.", 2);
    }
    let output = match fs::canonicalize(&job.output) {
        Ok(path) => path,
        Err(_) => return report.fail("output_unavailable", "Could not open the output directory.", 2),
    };
    let _ = report.send("started", json!({"mode":if job.audio {"audio"} else {"video"}}));
    let mut process = match child(&ytdlp).args(download_args(&job, &ffmpeg, executable("deno").as_deref())).current_dir(&output)
        .stdin(Stdio::null()).stdout(Stdio::piped()).stderr(Stdio::inherit()).spawn() {
        Ok(child) => child,
        Err(_) => return report.fail("spawn_failed", "Could not start yt-dlp.", 3),
    };
    let mut saved = 0;
    let reader = BufReader::new(process.stdout.take().expect("stdout is piped"));
    for line in reader.split(b'\n') {
        let Ok(line) = line else { break };
        let line = String::from_utf8_lossy(&line);
        let line = line.trim_end();
        if let Some(value) = line.strip_prefix(PROGRESS).and_then(|s| serde_json::from_str::<Value>(s).ok()) {
            let _ = report.send("progress", json!({
                "downloaded_bytes":value["downloaded_bytes"].as_u64(),
                "total_bytes":value["total_bytes"].as_u64().or_else(||value["total_bytes_estimate"].as_u64()),
                "eta_seconds":value["eta"].as_u64(),
                "bytes_per_second":value["speed"].as_f64(),
            }));
        } else if let Some(path) = line.strip_prefix(SAVED).and_then(|s| serde_json::from_str::<String>(s).ok()) {
            let path = output.join(path);
            let info = path.with_extension("info.json");
            let desc = path.with_extension("description");
            let _ = report.send("saved", json!({"path":path,"info_json":info.is_file().then_some(info),
                "description":desc.is_file().then_some(desc),"comments_requested":job.comments}));
            saved += 1;
        }
    }
    if !process.wait().is_ok_and(|s| s.success()) || saved == 0 {
        return report.fail("download_failed", "No completed download. See extractor diagnostics.", 4);
    }
    let _ = report.send("completed", json!({"saved_count":saved}));
    0
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let machine = args.iter().any(|a| a == "--json");
    let args: Vec<_> = args.into_iter().filter(|a| a != "--json").collect();
    let mut report = Reporter { out: io::stdout().lock(), json: machine };
    let status = match args.as_slice() {
        [] => { let _ = write!(report.out, "{HELP}"); 2 },
        [one] if one == "--help" || one == "-h" || one == "help" => { let _ = write!(report.out, "{HELP}"); 0 },
        [one] if one == "--version" => {
            if machine { let _ = report.send("version", json!({"version":env!("CARGO_PKG_VERSION")})); }
            else { let _ = writeln!(report.out, "sleek {}", env!("CARGO_PKG_VERSION")); }
            0
        },
        [one] if one == "doctor" => {
            let tools: Vec<_> = ["yt-dlp", "ffmpeg", "ffprobe", "deno"].into_iter().map(|name| {
                let path = executable(name);
                let ready = path.as_ref().is_some_and(|p| child(p)
                    .arg(if ["yt-dlp", "deno"].contains(&name) { "--version" } else { "-version" })
                    .output().is_ok_and(|status| status.status.success()));
                json!({"tool":name,"available":ready,"required":name != "deno","path":path})
            }).collect();
            let ready = tools.iter().all(|v| v["required"] != true || v["available"] == true);
            let _ = report.send("doctor", json!({"ready":ready,"tools":tools}));
            if ready { 0 } else { 3 }
        },
        [action, rest @ ..] if action == "download" => match parse_download(rest) {
            Ok(job) => run_download(job, &mut report),
            Err(err) => report.fail("invalid_input", err, 2),
        },
        _ => report.fail("invalid_input", "Unknown command. See --help.", 2),
    };
    ExitCode::from(status)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn metadata_flags_apply_to_audio_and_video() {
        for mode in ["--audio", "--video"] {
            let job = parse_download(&["https://example.com/movie".into(), mode.into()]).unwrap();
            let args = download_args(&job, Path::new("/tools/ffmpeg"), None);
            for flag in ["--write-info-json", "--write-description", "--write-comments", "--embed-metadata", "--ignore-config"] {
                assert!(args.iter().any(|v| v == flag), "{flag}");
            }
            assert_eq!(args[args.len() - 2], "--");
            assert_eq!(args.iter().any(|v| v == "--audio-format"), mode == "--audio");
        }
    }
    #[test]
    fn comments_can_be_disabled_without_disabling_metadata() {
        let job = parse_download(&["https://example.com/movie".into(), "--no-comments".into()]).unwrap();
        assert!(!job.comments);
        assert!(download_args(&job, Path::new("ffmpeg"), None).iter().any(|v| v == "--write-info-json"));
    }
}
