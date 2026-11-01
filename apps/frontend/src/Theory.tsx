import { useState } from "react";
import type { Action, State } from "./generated/contract";
import type { Submit } from "./Puzzles";
export function Theory({
  state,
  busy,
  submit,
}: {
  state: State;
  busy: boolean;
  submit: Submit;
}) {
  const [choices, setChoices] = useState<Record<string, string>>({});
  const [supports, setSupports] = useState<Record<string, string[]>>({});
  const [review, setReview] = useState(false);
  const groups = [...new Set(state.accusation.options.map((o) => o.group))];
  const claims = Object.values(choices)
    .filter(Boolean)
    .map((id) => ({ claim_id: id, evidence_ids: supports[id] ?? [] }));
  return (
    <section>
      <p className="eyebrow">The final account</p>
      <h2>What happened at Blackthorn Manor?</h2>
      <p>
        Separate actions, motives and consequences. The server evaluates your
        claims and collected evidence. A valid final submission ends this
        investigation.
      </p>
      {state.accusation.hint && <p>{state.accusation.hint}</p>}
      <fieldset disabled={busy || !state.accusation.eligible}>
        <legend>Your theory</legend>
        {groups.map((group) => (
          <div className="theory-group" key={group}>
            <label>
              {group.replaceAll("_", " ")}
              <select
                value={choices[group] ?? ""}
                onChange={(e) => {
                  setChoices((old) => ({ ...old, [group]: e.target.value }));
                  setReview(false);
                }}
              >
                <option value="">Leave unresolved</option>
                {state.accusation.options
                  .filter((o) => o.group === group)
                  .map((o) => (
                    <option value={o.id} key={o.id}>
                      {o.label}
                    </option>
                  ))}
              </select>
            </label>
            {choices[group] && (
              <fieldset>
                <legend>Supporting evidence</legend>
                {state.evidence.map((e) => (
                  <label key={e.id}>
                    <input
                      type="checkbox"
                      checked={(supports[choices[group]] ?? []).includes(e.id)}
                      onChange={() => {
                        const id = choices[group];
                        setSupports((old) => ({
                          ...old,
                          [id]: (old[id] ?? []).includes(e.id)
                            ? old[id].filter((x) => x !== e.id)
                            : [...(old[id] ?? []), e.id],
                        }));
                        setReview(false);
                      }}
                    />
                    {e.title}
                  </label>
                ))}
              </fieldset>
            )}
          </div>
        ))}
        <button disabled={claims.length === 0} onClick={() => setReview(true)}>
          Review theory
        </button>
        {review && (
          <div className="theory-review">
            <h3>Confirm your account</h3>
            {claims.map((c) => (
              <p key={c.claim_id}>
                {
                  state.accusation.options.find((o) => o.id === c.claim_id)
                    ?.label
                }{" "}
                — {c.evidence_ids.length} supporting clues
              </p>
            ))}
            <p>This concludes the current case. You can restart afterward.</p>
            <button
              className="primary"
              onClick={() =>
                submit({
                  type: "accuse",
                  claims: claims as Extract<
                    Action,
                    { type: "accuse" }
                  >["claims"],
                })
              }
            >
              Submit final theory
            </button>
            <button onClick={() => setReview(false)}>Keep investigating</button>
          </div>
        )}
      </fieldset>
    </section>
  );
}
