//! Canonical JSON vectors computed by the hanzo-research crate, for the Python port's tests.
use hanzo_research::lineage::{DataPurpose, EnvironmentV1, LineagePolicy, ResearchEvent};
use hanzo_research::{rfc8785_canonicalize, rfc8785_digest, Measure, ResearchWal, Run};
use serde_json::{json, Value};
use std::collections::BTreeMap;

fn main() {
    let out = std::env::args().nth(1).expect("out dir");
    let values: Vec<(&str, Value)> = vec![
        ("sorting", json!({"b": 2, "a": 1, "c": {"z": true, "x": false}})),
        ("empty", json!({"o": {}, "a": [], "s": "", "n": null})),
        ("escapes", json!({"s": "q\" b\\ s/ \u{8}\u{c}\n\r\t \u{1} \u{1f} \u{7f} é 😀 \u{2028}"})),
        ("utf16", json!({"\u{e9}": 1, "\u{1f600}": 2, "\u{ff61}": 3, "a": 4, "\u{10000}": 5, "\u{ffff}": 6})),
        ("ints", json!([0, 1, -1, 42, 9007199254740991i64, -9007199254740991i64])),
        ("floats", json!([0.5, 0.1, -1.5, 1.0, 100.0, 3.14159, 123456.789, 0.000001, 1e20, 2.5e-5, 0.8734610296764017])),
        ("nested", json!([{"b": [1, {"d": 1, "c": 2}], "a": "x"}, [[], {}]])),
    ];
    let mut vecs = Vec::new();
    for (name, v) in &values {
        let bytes = rfc8785_canonicalize(v).unwrap();
        vecs.push(json!({"name": name, "value": v, "canonical": String::from_utf8(bytes).unwrap(), "digest": rfc8785_digest(v).unwrap()}));
    }
    // Where the crate's numbers part from RFC 8785 (ES Number::toString): recorded, not asserted equal.
    let mut apart = Vec::new();
    for x in [1e21f64, 1e-7, 1.5e300, -0.0, 5e-324] {
        apart.push(json!({"value": x, "canonical": String::from_utf8(rfc8785_canonicalize(&x).unwrap()).unwrap()}));
    }
    for x in [9007199254740993u64, u64::MAX] {
        apart.push(json!({"value": x, "canonical": String::from_utf8(rfc8785_canonicalize(&x).unwrap()).unwrap()}));
    }
    let run = Run {
        project: "default".into(), id: "demo.bench-dev-cfg-sys".into(), benchmark: "demo.bench".into(),
        split: "dev".into(), system: "sys".into(), version: "m@abc".into(), k: Some(10), temperature: Some(0.0),
        commit: "0123456789abcdef0123456789abcdef01234567".into(), questions: Some(100), answered: Some(100),
        when: "2026-10-15T00:00:00Z".into(), ended: "2026-10-15T00:10:00Z".into(), by: "dgx".into(),
        measures: vec![Measure { category: "all".into(), metric: "accuracy".into(), value: 0.81, lo: Some(0.72), hi: Some(0.88), n: Some(100), of: Some(100) }],
        notes: "é 😀".into(), revision: "original".into(), ..Run::default()
    };
    let env = EnvironmentV1 {
        git_sha: "abc".into(), git_branch: "main".into(), git_dirty: true, host: "dgx".into(), os: "Linux".into(),
        kernel_version: "7.0.0".into(), cargo_lock_hash: "".into(), image_digest: "".into(), precision_config: "bf16".into(),
        determinism_config: "".into(), compiler_version: "rustc".into(),
        lib_versions: BTreeMap::from([("hanzo-ml".to_string(), "0.11.112".to_string())]),
    };
    let ev = ResearchEvent::new("run-1".into(), "worker-0".into(), "run-1-worker-0-1-step".into(), 1,
        "0".repeat(64), json!({"step": 1, "loss": 1.25}), "2026-10-15T00:00:00Z".into()).unwrap();
    let policy = LineagePolicy::derive(DataPurpose::TeacherMining, true, &[&LineagePolicy::root(DataPurpose::Train, true)]);
    let records = json!({
        "run": {"value": serde_json::to_value(&run).unwrap(), "digest": rfc8785_digest(&run).unwrap()},
        "environment": {"value": serde_json::to_value(&env).unwrap(), "digest": env.digest().unwrap()},
        "event": {"value": serde_json::to_value(&ev).unwrap(), "digest": ev.digest().unwrap()},
        "policy": {"value": serde_json::to_value(&policy).unwrap(), "digest": rfc8785_digest(&policy).unwrap()},
    });
    let dir = std::path::Path::new(&out);
    let _ = std::fs::remove_dir_all(dir.join("wal"));
    let mut wal = ResearchWal::open(&dir.join("wal"), "run-1").unwrap();
    wal.append("step", &json!({"step": 1, "loss": 1.25})).unwrap();
    wal.append("step", &json!({"step": 2, "loss": 1.1})).unwrap();
    wal.append("eval", &json!({"accuracy": 0.81, "split": "dev", "é": "😀"})).unwrap();
    let doc = json!({
        "crate": "hanzo-research", "source": "hanzoai/ml hanzo-research @ 7c967bf79",
        "vectors": vecs, "apart": apart, "records": records,
        "wal": {"last": wal.last_event_hash(), "sequence": wal.sequence()},
    });
    std::fs::write(dir.join("rust.json"), serde_json::to_string_pretty(&doc).unwrap() + "\n").unwrap();
}
