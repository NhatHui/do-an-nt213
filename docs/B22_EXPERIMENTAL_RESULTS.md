# B22 Experimental Results

## Scope and safety
Local-only Docker lab for unrestricted file upload detection. Payloads contain only `B22_UFU_EXEC_SUCCESS` or `B22_XSS_MARKER`; no command execution payloads were used.

## Verification results
| Test | Result | Detail |
|---|---|---|
| PHP vulnerable accepts PHP with spoofed image Content-Type | PASS | HTTP 200 |
| PHP executes benign marker | PASS | HTTP 200 |
| PHP vulnerable scenario content_type accepts demonstration input | PASS | HTTP 200 |
| PHP vulnerable scenario double_ext accepts demonstration input | PASS | HTTP 200 |
| PHP vulnerable scenario weak_strip accepts demonstration input | PASS | HTTP 200 |
| PHP vulnerable scenario null_byte_sim accepts demonstration input | PASS | HTTP 200 |
| PHP vulnerable scenario magic_bytes accepts demonstration input | PASS | HTTP 200 |
| PHP vulnerable scenario exif_polyglot accepts demonstration input | PASS | HTTP 200 |
| PHP vulnerable scenario path_traversal accepts demonstration input | PASS | HTTP 200 |
| Apache AddHandler executes double-extension benign PHP marker | PASS | HTTP 200 |
| Traversal upload escapes sub/ PHP restriction to parent uploads/ | PASS | HTTP 200 |
| LFI simulator includes only a file under uploads/ | PASS | HTTP 200 |
| LFI simulator rejects path outside uploads/ | PASS | HTTP 403 |
| Image polyglot plus restricted LFI executes appended benign PHP | PASS | HTTP 200 |
| Apache disables PHP execution inside uploads/sub/ | PASS | HTTP 200 |
| PHP defense re-encodes image, removes appended marker and stores outside webroot | PASS | HTTP 201 |
| PHP defense rejects PHP renamed as PNG | PASS | HTTP 415 |
| PHP defended rejects PHP | PASS | HTTP 415 |
| Node routed vulnerable endpoint stores and serves benign HTML marker | PASS | POST 201, GET 200 |
| Node sharp re-encodes PNG and strips appended benign marker outside webroot | PASS | HTTP 201 |
| Node defended retrieval sets download and security headers | PASS | HTTP 200 |
| Node defense rejects spoofed image MIME and extension | PASS | HTTP 415 |
| Node traversal endpoint reports whether original filename escapes upload directory | PASS | HTTP 201 |
| Node defended rejects oversized file | PASS | HTTP 413 |
| PHP defense rejects empty image | PASS | HTTP 415 |
| PHP defense rejects truncated PNG | PASS | HTTP 415 |
| PHP defense rejects extension mismatch | PASS | HTTP 415 |
| PHP defense rejects unexpected file field | PASS | HTTP 400 |
| Node defense rejects empty image | PASS | HTTP 415 |
| Node defense rejects truncated PNG | PASS | HTTP 415 |
| Node defense rejects extension mismatch | PASS | HTTP 415 |
| Node defense rejects unexpected file field | PASS | HTTP 400 |
| PHP defense rejects oversized upload (1048577 bytes) | PASS | HTTP 413 |
| PHP defense rejects oversized upload (2097153 bytes) | PASS | HTTP 413 |
| PHP defense rejects oversized upload (3145729 bytes) | PASS | HTTP 413 |
| SAST detects both intentional vulnerable patterns | PASS | Exit 0 |

## SAST (Semgrep)
- Exit code: `0`
```text
{"version":"1.181.1","results":[{"check_id":"semgrep.b22-node-multer-webroot","path":"/src/node-lab/server.js","start":{"line":14,"col":22,"offset":446},"end":{"line":14,"col":57,"offset":481},"extra":{"message":"Multer destination is inside a publicly served upload directory.","metadata":{},"severity":"WARNING","fingerprint":"requires login","lines":"requires login","validation_state":"NO_VALIDATOR","engine_kind":"OSS"}},{"check_id":"semgrep.b22-php-unrestricted-move-upload","path":"/src/php-lab/src/vuln_upload.php","start":{"line":52,"col":7,"offset":2160},"end":{"line":52,"col":55,"offset":2208},"extra":{"message":"Uploaded file is moved into a webroot path without an allowlist policy.","metadata":{},"severity":"WARNING","fingerprint":"requires login","lines":"requires login","validation_state":"NO_VALIDATOR","engine_kind":"OSS"}}],"errors":[],"paths":{"scanned":["/src/node-lab/server.js","/src/php-lab/src/assets/lab.js","/src/php-lab/src/defended_upload.php","/src/php-lab/src/index.php","/src/php-lab/src/lfi_simulator.php","/src/php-lab/src/vuln_upload.php"]},"time":{"rules":[],"rules_parse_time":0.03983497619628906,"profiling_times":{"config_time":0.18477630615234375,"core_time":0.9742696285247803,"ignores_time":8.320808410644531e-05,"total_time":1.1835625171661377},"parsing_time":{"total_time":0.05190920829772949,"per_file_time":{"mean":0.025954604148864746,"std_dev":9.651171382074608e-07},"very_slow_stats":{"time_ratio":0.0,"count_ratio":0.0},"very_slow_files":[]},"scanning_time":{"total_time":0.0936577320098877,"per_file_time":{"mean":0.01560962200164795,"std_dev":0.0001808194359066799},"very_slow_stats":{"time_ratio":0.0,"count_ratio":0.0},"very_slow_files":[]},"matching_time":{"total_time":0.0058438777923583984,"per_file_and_rule_time":{"mean":0.0029219388961791992,"std_dev":4.186071137723957e-06},"very_slow_stats":{"time_ratio":0.0,"count_ratio":0.0},"very_slow_rules_on_files":[]},"tainting_time":{"total_time":0.0,"per_def_and_rule_time":{"mean":0.0,"std_dev":0.0},"very_slow_stats":{"time_ratio":0.0,"count_ratio":0.0},"very_slow_rules_on_defs":[]},"fixpoint_timeouts":[],"prefiltering":{"project_level_time":0.0,"file_level_time":0.0,"rules_with_project_prefilters_ratio":0.0,"rules_with_file_prefilters_ratio":1.0,"rules_selected_ratio":0.3333333333333333,"rules_matched_ratio":0.3333333333333333},"targets":[],"total_bytes":0,"max_memory_bytes":118848960},"engine_requested":"OSS","skipped_rules":[],"profiling_results":[]}

```

## Interpretation (C2 / C4)
- C2: PHP marker execution demonstrates server-side interpretation of an uploaded file. Node vulnerable routes serve arbitrary uploaded files; HTML marker retrieval is not executed XSS.
- Node traversal is reported only if Multer preserves the submitted parent path and writes outside public/uploads.
- C4: PHP and Node defended routes validate signatures/content and re-encode images before storing outside the webroot.
- Semgrep rules are narrow structural heuristics for this lab, not proof of absence of upload vulnerabilities.
- lfi_simulator.php uses include with a canonical-path boundary restricted to uploads/.
- HTTP 0 means infrastructure BLOCKED, never a successful security test.
- This lab is educational and is bound to loopback by Docker Compose.
