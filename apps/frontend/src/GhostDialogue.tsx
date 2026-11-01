import { useState } from "react";
import { motion } from "motion/react";
import type { Action, AI, State } from "./generated/contract";
import { safeAsset } from "./RoomScene";
import type { Submit } from "./Puzzles";
export function AiLabel({
  ai,
  synthetic = false,
}: {
  ai: AI;
  synthetic?: boolean;
}) {
  return (
    <span className="mode-badge">
      {synthetic ? "Mock metadata · " : ""}
      {ai.source === "live"
        ? "Live model"
        : ai.source === "fallback"
          ? "Fallback"
          : ai.source === "demo"
            ? "Deterministic demo"
            : "No AI used"}
      {ai.reason ? " · " + ai.reason.replaceAll("_", " ") : ""}
      {ai.model ? " · " + ai.model : ""}
    </span>
  );
}
export function GhostDialogue({
  state,
  busy,
  submit,
  synthetic = false,
}: {
  state: State;
  busy: boolean;
  submit: Submit;
  synthetic?: boolean;
}) {
  const [ghostId, setGhostId] = useState(
    state.ghosts.find((g) => g.available)?.id ?? "eleanor",
  );
  const [message, setMessage] = useState("");
  const [tone, setTone] = useState<"neutral" | "respectful" | "accusatory">(
    "neutral",
  );
  const [evidence, setEvidence] = useState<string[]>([]);
  const ghost = state.ghosts.find((g) => g.id === ghostId);
  const [failedPortrait, setFailedPortrait] = useState<string | null>(null);
  const portrait = state.assets.find((a) => a.id === ghost?.portrait_asset_id);
  const hasPortrait =
    portrait && safeAsset(portrait.src) && portrait.id !== failedPortrait;
  return (
    <section className="interrogation">
      <p className="eyebrow">Beyond the veil</p>
      <h2>Question the spirits</h2>
      <label>
        Ghost
        <select
          value={ghostId}
          onChange={(e) => setGhostId(e.target.value as typeof ghostId)}
        >
          {state.ghosts.map((g) => (
            <option key={g.id} value={g.id}>
              {g.display_name}
              {g.available ? "" : " · absent here"}
            </option>
          ))}
        </select>
      </label>
      {ghost && (
        <div className="ghost-stage">
          <motion.div
            className={"portrait " + ghost.emotion}
            animate={{ opacity: [0.75, 1] }}
            transition={{ duration: 1 }}
            aria-hidden="true"
          >
            {hasPortrait ? (
              <img
                src={safeAsset(portrait.src)}
                alt=""
                loading="lazy"
                width={1024}
                height={1536}
                onError={() => setFailedPortrait(portrait.id)}
              />
            ) : (
              <div className="specter">
                <i />
                <span />
              </div>
            )}
          </motion.div>
          <div>
            <h3>{ghost.display_name}</h3>
            <p>{ghost.emotion}</p>
            <label>
              Trust <meter min={0} max={100} value={ghost.trust} />
              <span>{ghost.trust}/100</span>
            </label>
            <label>
              Suspicion <meter min={0} max={100} value={ghost.suspicion} />
              <span>{ghost.suspicion}/100</span>
            </label>
            {!hasPortrait && (
              <small>Temporary spectral staging · final portrait pending</small>
            )}
          </div>
        </div>
      )}
      <div className="transcript" aria-label="Conversation history">
        {state.dialogue
          .filter((t) => t.ghost_id === ghostId)
          .map((t) => (
            <article key={t.id}>
              <p className="player-line">You: {t.player_message}</p>
              <blockquote>{t.response_text}</blockquote>
              <AiLabel ai={t.ai} synthetic={synthetic} />
            </article>
          ))}
        {state.dialogue.every((t) => t.ghost_id !== ghostId) && (
          <p>No conversation yet. Ask what the spirit remembers.</p>
        )}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (message.trim() && ghost?.available)
            submit({
              type: "talk",
              ghost_id: ghostId,
              message: message.trim(),
              tone,
              presented_evidence_ids: evidence as Extract<
                Action,
                { type: "talk" }
              >["presented_evidence_ids"],
            });
        }}
      >
        <fieldset disabled={busy || !ghost?.available}>
          <legend>Speak to {ghost?.display_name ?? "a spirit"}</legend>
          <label>
            Your question
            <textarea
              maxLength={1000}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              required
            />
          </label>
          <small>
            {message.length}/1000 characters. Your draft stays here if the
            request fails.
          </small>
          <label>
            Tone
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value as typeof tone)}
            >
              <option value="neutral">Neutral</option>
              <option value="respectful">Respectful</option>
              <option value="accusatory">Accusatory</option>
            </select>
          </label>
          <details>
            <summary>Present evidence ({evidence.length}/3)</summary>
            {state.evidence.map((item) => (
              <label key={item.id}>
                <input
                  type="checkbox"
                  checked={evidence.includes(item.id)}
                  disabled={
                    !evidence.includes(item.id) && evidence.length === 3
                  }
                  onChange={() =>
                    setEvidence((old) =>
                      old.includes(item.id)
                        ? old.filter((id) => id !== item.id)
                        : [...old, item.id],
                    )
                  }
                />
                {item.title}
              </label>
            ))}
          </details>
          <button className="primary" disabled={!message.trim()}>
            Ask ghost
          </button>
        </fieldset>
      </form>
    </section>
  );
}
