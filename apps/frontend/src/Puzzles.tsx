import { useState } from "react";
import type { Action, Puzzle } from "./generated/contract";
export type Submit = (action: Action) => void;
type Props<T extends Puzzle> = { puzzle: T; busy: boolean; submit: Submit };
export function LetterPuzzle({
  puzzle,
  busy,
  submit,
}: Props<Extract<Puzzle, { id: "letter_reconstruction" }>>) {
  const [placed, setPlaced] = useState<Record<string, string>>({});
  const solved = puzzle.status === "solved";
  function move(slot: string, piece: string) {
    if (busy || solved) return;
    setPlaced((old) => {
      if (!piece) return { ...old, [slot]: "" };
      const next = { ...old };
      const source = Object.keys(old).find((k) => old[k] === piece);
      if (source && source !== slot) next[source] = old[slot] ?? "";
      next[slot] = piece;
      return next;
    });
  }
  return (
    <section className="puzzle paper">
      <p className="eyebrow">Reconstruction / {puzzle.status}</p>
      <h3>Eleanor’s torn letter</h3>
      <p>
        Place each fragment once. Drag into a slot or use the labeled selectors.
        Only the server can confirm the reconstruction.
      </p>
      <div className="fragments">
        {puzzle.presentation.pieces.map((p) => (
          <div
            className="fragment"
            key={p.id}
            draggable={!busy && !solved}
            onDragStart={(e) => e.dataTransfer.setData("text/plain", p.id)}
          >
            {p.text}
          </div>
        ))}
      </div>
      <fieldset disabled={busy || solved}>
        <legend>Letter order</legend>
        {puzzle.presentation.slots.map((slot) => (
          <label
            className="slot"
            key={slot.id}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const piece = e.dataTransfer.getData("text/plain");
              if (puzzle.presentation.pieces.some((p) => p.id === piece))
                move(slot.id, piece);
            }}
          >
            {slot.label}
            <select
              value={placed[slot.id] ?? ""}
              onChange={(e) => move(slot.id, e.target.value)}
            >
              <option value="">Choose a fragment</option>
              {puzzle.presentation.pieces.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.text}
                </option>
              ))}
            </select>
          </label>
        ))}
        <div className="actions">
          <button type="button" onClick={() => setPlaced({})}>
            Reset draft
          </button>
          <button
            className="primary"
            disabled={puzzle.presentation.slots.some((s) => !placed[s.id])}
            onClick={() =>
              submit({
                type: "submit_puzzle",
                puzzle_id: puzzle.id,
                solution: {
                  placements: puzzle.presentation.slots.map((s) => ({
                    slot_id: s.id,
                    piece_id: placed[s.id],
                  })) as Extract<
                    Action,
                    { puzzle_id: "letter_reconstruction" }
                  >["solution"]["placements"],
                },
              })
            }
          >
            Submit reconstruction
          </button>
        </div>
      </fieldset>
      {solved && <p role="status">Reconstruction confirmed by the server.</p>}
    </section>
  );
}
export function CalibrationPuzzle({
  puzzle,
  busy,
  submit,
}: Props<Extract<Puzzle, { id: "machine_calibration" }>>) {
  const [power, setPower] = useState("0");
  const numericPower = Number(power);
  const validPower =
    power.trim() !== "" &&
    Number.isInteger(numericPower) &&
    numericPower >= 0 &&
    numericPower <= 3;
  const [phase, setPhase] = useState<"amber" | "violet" | "cyan">("amber");
  const [stabilizer, setStabilizer] = useState<"bypass" | "engaged">("bypass");
  return (
    <section className="puzzle machine">
      <p className="eyebrow">Memory apparatus / {puzzle.status}</p>
      <h3>Machine calibration</h3>
      <p>{puzzle.presentation.instructions}</p>
      <div className="instrument" aria-hidden="true">
        <span>{power}</span>
        <i className={"crystal " + phase} />
        <span>{stabilizer === "engaged" ? "◉" : "○"}</span>
      </div>
      <fieldset disabled={busy || puzzle.status === "solved"}>
        <legend>Calibration settings</legend>
        {puzzle.presentation.controls.map((c) => (
          <label key={c.id}>
            {c.label}
            {c.kind === "integer" ? (
              <input
                type="number"
                min={c.minimum}
                max={c.maximum}
                step={c.step}
                value={power}
                onChange={(e) => setPower(e.target.value)}
                aria-invalid={!validPower}
                aria-describedby="calibration-power-help"
              />
            ) : (
              <select
                value={c.id === "phase" ? phase : stabilizer}
                onChange={(e) =>
                  c.id === "phase"
                    ? setPhase(e.target.value as typeof phase)
                    : setStabilizer(e.target.value as typeof stabilizer)
                }
              >
                {c.options.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            )}
          </label>
        ))}
        <p id="calibration-power-help">
          Power must be a whole number from 0 to 3.
        </p>
        <button
          className="primary"
          disabled={!validPower}
          onClick={() => {
            if (!validPower) return;
            submit({
              type: "submit_puzzle",
              puzzle_id: puzzle.id,
              solution: { power_level: numericPower, phase, stabilizer },
            });
          }}
        >
          Submit calibration
        </button>
      </fieldset>
      {puzzle.status === "solved" && (
        <p role="status">Calibration confirmed by the server.</p>
      )}
    </section>
  );
}
