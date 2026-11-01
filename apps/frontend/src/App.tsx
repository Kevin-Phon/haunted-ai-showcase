import { useRef, useState } from "react";
import { MotionConfig } from "motion/react";
import { ApiClient, ApiError, type Transport } from "./api";
import type {
  Action,
  ActionResponse,
  Hotspot,
  Event,
  SessionResponse,
  State,
} from "./generated/contract";
import { RoomScene, Inspection, Journal, safeAsset } from "./RoomScene";
import { Board } from "./Board";
import { LetterPuzzle, CalibrationPuzzle } from "./Puzzles";
import { GhostDialogue } from "./GhostDialogue";
import { Theory } from "./Theory";
import { rememberedSession, rememberSession } from "./sessionMemory";
import { AmbientAudio, DiscoverySound } from "./AmbientAudio";
type DevTools = { scenarios: string[]; select: (name: string) => void };
const tabs = [
  "Explore",
  "Journal",
  "Board",
  "Puzzles",
  "Spirits",
  "Theory",
  "Events",
] as const;
export function App({
  transport = new ApiClient(),
  devTools,
}: {
  transport?: Transport;
  devTools?: DevTools;
}) {
  const [state, setState] = useState<State | null>(null);
  const latest = useRef<State | null>(null);
  const [busy, setBusy] = useState(false);
  const locked = useRef(false);
  const [error, setError] = useState<ApiError | null>(null);
  const retry = useRef<null | {
    job: () => Promise<SessionResponse | ActionResponse>;
    reset: boolean;
  }>(null);
  const [tab, setTab] = useState<(typeof tabs)[number]>("Explore");
  const [notice, setNotice] = useState("");
  const [inspection, setInspection] = useState<Hotspot | null>(null);
  const [mode, setMode] = useState<"live" | "demo">("live");
  const [restartConfirm, setRestartConfirm] = useState(false);
  const [epoch, setEpoch] = useState(0);
  const [newSessionConfirm, setNewSessionConfirm] = useState(false);
  const [reduce, setReduce] = useState(false);
  const [audio, setAudio] = useState(false);
  const [scenario, setScenario] = useState("session");
  const blocked = busy || retry.current !== null;
  const seen = useRef(new Set<string>());
  const [apparition, setApparition] = useState<Event | null>(null);
  async function run(
    job: () => Promise<SessionResponse | ActionResponse>,
    reset = false,
    purpose: "command" | "read" = "command",
  ) {
    const pending = retry.current;
    if (
      locked.current ||
      (purpose === "command" && pending && job !== pending.job)
    )
      return;
    locked.current = true;
    setBusy(true);
    setError(null);
    try {
      const response = await job();
      const next = response.state;
      if (
        !latest.current ||
        next.session_id !== latest.current.session_id ||
        next.revision >= latest.current.revision
      ) {
        latest.current = next;
        setState(next);
        if (!devTools) rememberSession(next.session_id);
      }
      if (reset) {
        seen.current.clear();
        setApparition(null);
      }
      if (
        "feedback" in response &&
        next.revision >= (latest.current?.revision ?? 0)
      ) {
        setNotice(response.feedback.message);
        for (const event of response.new_events) {
          if (!seen.current.has(event.id)) {
            seen.current.add(event.id);
            setApparition(event);
            setNotice(event.summary + " · " + response.feedback.message);
          }
        }
      }
      if (reset) {
        setEpoch((x) => x + 1);
        setTab("Explore");
        setInspection(null);
        setRestartConfirm(false);
        setNewSessionConfirm(false);
      }
      retry.current = purpose === "read" ? pending : null;
      if (retry.current) {
        setError(
          new ApiError(
            "NETWORK_UNCERTAIN",
            "Latest state retrieved. Resolve the pending request using Retry same request before making another change.",
            next.revision,
            true,
          ),
        );
      }
    } catch (err) {
      const typed =
        err instanceof ApiError
          ? err
          : new ApiError(
              "UNEXPECTED",
              "The request failed. Retrieve state before continuing.",
            );
      setError(typed);
      retry.current =
        typed.code === "SESSION_NOT_FOUND"
          ? null
          : purpose === "read" && pending
            ? pending
            : typed.code === "NETWORK_UNCERTAIN" && purpose === "command"
              ? { job, reset }
              : null;
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }
  function submit(action: Action) {
    if (!state || state.phase === "ended" || blocked) return;
    const id = crypto.randomUUID();
    const revision = state.revision;
    const sid = state.session_id;
    void run(() => transport.action(sid, revision, action, id));
  }
  function start() {
    if (blocked) return;
    const id = crypto.randomUUID();
    void run(() => transport.create(state?.mode ?? mode, id), true);
  }
  const ambient = state?.assets.find(
    (a) => a.id === state.scene.ambient_audio_asset_id,
  );
  const discovery = state?.assets.find(
    (a) => a.id === "audio_discovery" && a.kind === "audio",
  );
  const discoverySrc = discovery && safeAsset(discovery.src);
  return (
    <MotionConfig reducedMotion={reduce ? "always" : "user"}>
      <div className={"app " + (reduce ? "reduce-motion" : "")}>
        <a className="skip" href="#main">
          Skip to investigation
        </a>
        <header className="topbar">
          <a className="brand" href="#main">
            <span className="brand-mark">✧</span>
            <span>
              BLACKTHORN<small>PARANORMAL INVESTIGATIONS</small>
            </span>
          </a>
          <div className="settings">
            <label>
              <input
                type="checkbox"
                checked={reduce}
                onChange={(e) => setReduce(e.target.checked)}
              />{" "}
              Reduced motion
            </label>
            <label>
              <input
                type="checkbox"
                checked={audio}
                onChange={(e) => setAudio(e.target.checked)}
              />{" "}
              Sound · ambience and discovery cues
            </label>
          </div>
        </header>
        {devTools && (
          <aside className="dev-banner">
            <strong>
              DEVELOPMENT MOCK TRANSPORT — synthetic fixtures, no gameplay rules
              or live inference
            </strong>
            <label>
              Fixture scenario
              <select
                value={scenario}
                disabled={busy}
                onChange={(e) => {
                  setScenario(e.target.value);
                  devTools.select(e.target.value);
                  setInspection(null);
                  setEpoch((x) => x + 1);
                  latest.current = null;
                }}
              >
                {devTools.scenarios.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
            <button
              disabled={busy}
              onClick={() =>
                void run(() => transport.get(state?.session_id ?? ""), true)
              }
            >
              Load selected fixture
            </button>
            <p>
              Controls send real contract payloads but replay the selected
              response. Select another fixture to view another state; this is
              not a playable backend simulation.
            </p>
          </aside>
        )}
        <div className="request-status" role="status" aria-live="polite">
          {busy ? "Consulting the investigation service…" : notice}
        </div>
        {error && (
          <aside className="error-panel" role="alert">
            <strong>{error.code.replaceAll("_", " ")}</strong>
            <p>{error.message}</p>
            {retry.current && (
              <button
                disabled={busy}
                onClick={() =>
                  retry.current &&
                  void run(retry.current.job, retry.current.reset)
                }
              >
                Retry same request
              </button>
            )}
            {state && (
              <button
                disabled={busy}
                onClick={() =>
                  void run(() => transport.get(state.session_id), false, "read")
                }
              >
                Retrieve latest state
              </button>
            )}
            {(error.code === "SESSION_NOT_FOUND" ||
              error.code === "SESSION_ACTION_LIMIT") && (
              <div>
                {error.code === "SESSION_ACTION_LIMIT" && (
                  <p>
                    This investigation has reached its lifetime action limit.
                    Restarting the same investigation cannot reset that
                    allowance.
                  </p>
                )}
                <button
                  disabled={blocked}
                  onClick={() => setNewSessionConfirm(true)}
                >
                  Start new investigation
                </button>
                {newSessionConfirm && (
                  <section aria-label="New investigation confirmation">
                    <p>
                      Current investigation progress will not carry over. Create
                      a separate investigation with an empty journal and fresh
                      conversation history?
                    </p>
                    <button disabled={blocked} onClick={start}>
                      Confirm new investigation
                    </button>
                    <button
                      disabled={busy}
                      onClick={() => setNewSessionConfirm(false)}
                    >
                      Cancel new investigation
                    </button>
                  </section>
                )}
              </div>
            )}
          </aside>
        )}
        {apparition && (
          <aside
            className="apparition"
            role="region"
            aria-label="Supernatural occurrence"
          >
            <div className="apparition-glow" aria-hidden="true" />
            <p className="eyebrow">A whisper in the manor</p>
            <p>{apparition.summary}</p>
            <button onClick={() => setApparition(null)}>
              Dismiss apparition
            </button>
          </aside>
        )}
        <main id="main" tabIndex={-1}>
          {!state ? (
            <section className="introduction">
              <p className="eyebrow">A supernatural detective mystery</p>
              <h1>
                Whispers of
                <br />
                <em>Blackthorn Manor</em>
              </h1>
              <p className="intro-copy">
                A death in 1926. Three lingering spirits. One century of
                silence.
                <br />
                Enter the manor, gather what remains, and give the dead an
                account of the truth.
              </p>
              <label>
                Dialogue mode
                <select
                  value={mode}
                  disabled={busy}
                  onChange={(e) => setMode(e.target.value as typeof mode)}
                >
                  <option value="live">
                    Live local model · explicit fallback if unavailable
                  </option>
                  <option value="demo">
                    Deterministic demo · authored dialogue
                  </option>
                </select>
              </label>
              <button
                className="primary enter"
                disabled={blocked}
                onClick={start}
              >
                Enter the manor
              </button>
              {!devTools && rememberedSession() && (
                <button
                  disabled={busy}
                  onClick={() => {
                    const id = rememberedSession();
                    if (id) void run(() => transport.get(id), false, "read");
                  }}
                >
                  Resume surviving session
                </button>
              )}
              <p className="control-note">
                Explore with mouse, touch or keyboard. Every drag interaction
                has a labeled control alternative. Audio begins off. Sessions
                survive a page refresh while the backend remains running.
              </p>
              <small>
                Original generated manor artwork · backend-authoritative
                investigation.
              </small>
            </section>
          ) : (
            <>
              <div className="casebar">
                <span className="mode-badge">
                  {state.mode === "demo"
                    ? "Deterministic demo session"
                    : "Live-model session · each reply labels actual source"}
                </span>
                <label className="progress">
                  {state.progress.label}
                  <progress
                    max={state.progress.total || 1}
                    value={state.progress.earned}
                  />
                  <small>
                    {state.progress.earned}/{state.progress.total} milestones
                  </small>
                </label>
                <button
                  disabled={blocked}
                  onClick={() => setRestartConfirm(true)}
                >
                  Restart investigation
                </button>
              </div>
              {restartConfirm && (
                <section
                  className="restart-confirm"
                  aria-label="Restart confirmation"
                >
                  <p>
                    Start this investigation over? Collected evidence and
                    conversation history will be cleared after server
                    confirmation.
                  </p>
                  <button
                    disabled={blocked}
                    onClick={() => {
                      if (blocked) return;
                      const id = crypto.randomUUID();
                      const current = state;
                      void run(
                        () =>
                          transport.restart(
                            current.session_id,
                            current.revision,
                            id,
                          ),
                        true,
                      );
                    }}
                  >
                    Confirm restart
                  </button>
                  <button onClick={() => setRestartConfirm(false)}>
                    Cancel restart
                  </button>
                </section>
              )}
              {state.ending ? (
                <section className="ending" data-ending={state.ending.id}>
                  <p className="eyebrow">The manor remembers</p>
                  <h1>{state.ending.title}</h1>
                  <p>{state.ending.explanation}</p>
                  <p>{state.ending.missing_summary}</p>
                  <small>Ending evaluated by the investigation service.</small>
                </section>
              ) : (
                <>
                  <nav className="case-tabs" aria-label="Investigation tools">
                    {tabs.map((t) => (
                      <button
                        aria-pressed={tab === t}
                        key={t}
                        onClick={() => {
                          setTab(t);
                          setInspection(null);
                        }}
                      >
                        {t}
                        {t === "Journal" ? " / " + state.evidence.length : ""}
                      </button>
                    ))}
                  </nav>
                  <div
                    className="workspace"
                    key={state.session_id + ":" + epoch}
                    aria-busy={blocked}
                  >
                    <div hidden={tab !== "Explore"}>
                      <RoomScene
                        state={state}
                        busy={blocked}
                        submit={submit}
                        onInspect={(h) => {
                          setInspection(h);
                          submit({ type: "inspect", hotspot_id: h.id });
                        }}
                      />
                    </div>
                    <div hidden={tab !== "Journal"}>
                      <Journal state={state} />
                    </div>
                    <div hidden={tab !== "Board"}>
                      <Board state={state} busy={blocked} submit={submit} />
                    </div>
                    <section hidden={tab !== "Puzzles"}>
                      <h2>Objects with unfinished stories</h2>
                      {state.puzzles.length === 0 && (
                        <p>
                          No puzzles revealed yet. Explore objects and follow
                          your evidence.
                        </p>
                      )}
                      {state.puzzles.map((p) =>
                        p.id === "letter_reconstruction" ? (
                          <LetterPuzzle
                            key={p.id}
                            puzzle={p}
                            busy={blocked}
                            submit={submit}
                          />
                        ) : (
                          <CalibrationPuzzle
                            key={p.id}
                            puzzle={p}
                            busy={blocked}
                            submit={submit}
                          />
                        ),
                      )}
                    </section>
                    <div hidden={tab !== "Spirits"}>
                      <GhostDialogue
                        state={state}
                        busy={blocked}
                        submit={submit}
                        synthetic={Boolean(devTools)}
                      />
                    </div>
                    <div hidden={tab !== "Theory"}>
                      <Theory state={state} busy={blocked} submit={submit} />
                    </div>
                    <section hidden={tab !== "Events"}>
                      <h2>Supernatural occurrences</h2>
                      {state.events.length === 0 ? (
                        <p>No recorded occurrences yet.</p>
                      ) : (
                        state.events.map((e) => (
                          <article className="insight" key={e.id}>
                            {e.summary}
                          </article>
                        ))
                      )}
                    </section>
                  </div>
                </>
              )}
              {inspection && state.phase !== "ended" && (
                <Inspection
                  hotspot={inspection}
                  state={state}
                  busy={blocked}
                  submit={submit}
                  close={() => setInspection(null)}
                />
              )}
            </>
          )}
        </main>
        {audio && ambient && safeAsset(ambient.src) && (
          <AmbientAudio key={ambient.id} src={safeAsset(ambient.src)!} />
        )}
        {audio && state && discoverySrc && (
          <DiscoverySound
            key={state.session_id}
            earned={state.progress.earned}
            src={discoverySrc}
          />
        )}
        <footer>
          WHISPERS OF BLACKTHORN MANOR{" "}
          <span>Investigation foundation · contract 1.0.0</span>
          {audio && !ambient && (
            <span>No ambient track supplied for this scene.</span>
          )}
        </footer>
      </div>
    </MotionConfig>
  );
}
