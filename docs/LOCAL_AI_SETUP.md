# Local Ollama and Qwen setup

Live dialogue uses a local Ollama endpoint. Deterministic demo mode works without it. No external paid-service API key is needed for this local path. Model/runtime downloads require disk space and network access; this is not a guarantee of offline operation or cost-free computing.

## Install and start

Install Ollama from its [official download page](https://ollama.com/download) and follow the [platform quickstart](https://docs.ollama.com/quickstart). On macOS, use the [official installation instructions](https://docs.ollama.com/macos) and start the installed application. For a CLI-only installation, run the following in a separate terminal only if no Ollama server is already listening:

```sh
ollama serve
```

Do not start a competing server or replace an existing model store. Keep the service local at `http://127.0.0.1:11434`. In another terminal:

```sh
ollama --version
ollama pull qwen2.5:1.5b
ollama list
ollama show qwen2.5:1.5b
ollama run qwen2.5:1.5b "Say hello in one short sentence."
```

The last command is a real standalone inference check, not a game turn. `pull` downloads model files; keep them in Ollama's model store outside the repository. The [official tag page](https://ollama.com/library/qwen2.5:1.5b) identifies a roughly 986 MB Q4_K_M model with digest prefix `65ec06548149`. Tags or current installers may change; inspect the installed metadata rather than assuming a fresh download reproduces an older runtime exactly.

## Recorded configuration and behavior

Development verification used Ollama 0.40.13, `qwen2.5:1.5b`, Q4_K_M, on an 8 GiB Mac. The exact tested model digest was `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`. Runtime and model files were outside the source repository. A current official installer can differ from this recorded version; it has not automatically been validated by the historical tests.

Launch FastAPI with `HAUNTED_OLLAMA_MODEL=qwen2.5:1.5b` and `HAUNTED_OLLAMA_URL=http://127.0.0.1:11434` as shown in [development setup](development.md). The game sends native structured-output requests and validates returned permitted fact IDs/reactions. It uses a ten-second provider deadline and no automatic retries. Cold loading, resource pressure, an unavailable endpoint or invalid output can produce labeled fallback; the mystery remains playable.

Standalone model success or a healthy backend does not prove a particular ghost turn succeeded. In the game, inspect each reply's actual live/demo/fallback label. One complete live-mode test used two real live replies and one timeout fallback. No universal response-time or all-live guarantee is made.

Qwen's model license and Ollama's runtime license are separate from project licensing. See [third-party notices](../THIRD_PARTY_NOTICES.md).
