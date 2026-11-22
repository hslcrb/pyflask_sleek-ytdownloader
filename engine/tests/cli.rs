use std::process::Command;
fn cli(args: &[&str]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_sleek")).args(args).output().unwrap()
}
#[test]
fn help_is_available_without_tools() {
    let out = cli(&["--help"]);
    assert!(out.status.success());
    let text = String::from_utf8(out.stdout).unwrap();
    assert!(text.contains("download"));
    assert!(text.contains("--json"));
}
#[test]
fn invalid_input_is_actionable_and_machine_readable() {
    for url in ["file:///tmp/a", "--config-location", "https://user:secret@example.com/"] {
        let out = cli(&["download", url, "--json"]);
        assert_eq!(out.status.code(), Some(2));
        let v: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
        assert_eq!(v["event"], "error");
        assert_eq!(v["code"], "invalid_input");
        assert!(!String::from_utf8_lossy(&out.stderr).contains("secret"));
    }
}
