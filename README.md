# Neton AI

Official, optional AI integration for Neton. Source and sample history were extracted
from the framework; `neton.ai` packages and `com.netonstream:neton-ai` coordinates remain.
AI versions no longer follow Framework versions and are not constrained by its BOM.

Current independent candidate: **0.1.0-alpha.1** (not published). Framework acceptance uses
the exact unpublished candidate in `tools/framework-candidate.json`, Kotlin **2.4.20**,
and JVM 17 build tooling. Beta26 cannot be advertised as supported on Linux: its Security
OpenSSL 3 provider conflicts with HTTP's OpenSSL 4. The pinned candidate unifies the backend;
compatibility is accepted only after its CI and this project's native matrix pass. Do not mix arbitrary
Kotlin/Native compiler versions. Upgrading AI alone does not require a framework release.
Legacy `1.0.0-beta26` AI artifacts remain untouched. The independent version is intentionally
lower: declare it explicitly; remove legacy AI dependencies/BOM constraints rather than
relying on Gradle's highest-version conflict resolution. No downgrade is automatic.

Canonical specifications: [neton-docs ai.md](https://github.com/netonframework/netonframework.github.io/blob/main/docs/zh-hans/spec/ai.md).
AI contracts remain explicit opt-in APIs, governed by this project's release line.

```sh
python3 tools/framework_candidate.py /absolute/path/to/new-candidate-directory
./gradlew -Pneton.repository=/absolute/path/to/new-candidate-directory/repository :neton-ai:macosArm64Test :neton-ai:checkProtocolLayering
./gradlew -Pneton.repository=/absolute/path/to/new-candidate-directory/repository :examples:neton-ai-sample:linkDebugExecutableMacosArm64
```

The download requires GitHub CLI authentication and a successful pinned core workflow.
It verifies revision and every repository payload against that workflow's signed-candidate
evidence. There is no fallback to a sibling checkout or another version. These candidates
are CI artifacts, not Maven Central releases. AI release staging is blocked while this
candidate-only pin exists; switch to a supported published Framework version and rerun
the same CI before staging an independent AI release.

Use `linuxX64` or `mingwX64` on those hosts. CI runs actual Native tests and links the
sample on all three, plus a compiled five-target ABI baseline on macOS. Fixtures are
deterministic protocol replays, not certification of live third-party services.

## Release procedure

1. Review `aiVersion`, framework compatibility, API/ABI changes and release notes; commit
   and wait for AI CI on that exact main SHA. Never change `netonVersion` merely to match AI.
2. Configure the GitHub `release` environment with required reviewers and secrets
   `SIGNING_KEY` (armored PGP private key), `SIGNING_PASSWORD`, and `CENTRAL_TOKEN`
   (Central user token encoded as required by its API). Never commit credentials.
3. Explicitly dispatch `Stage AI release for Central validation` with the committed AI
   version. It builds signed artifacts and a SHA manifest and submits USER_MANAGED staging.
4. Inspect Central validation, signatures, dependencies and staged consumer acceptance.
   A maintainer separately authorizes publication in Central; staging is not publication.
5. After publication, independently resolve from Maven Central and rerun sample acceptance,
   then create the corresponding release/tag. Do not claim these steps occurred from CI alone.

No automatic tag-triggered publication, framework release or mutable latest dependency is used.
Central staging semantics follow the [official Publisher API](https://central.sonatype.org/publish/publish-portal-api/).
