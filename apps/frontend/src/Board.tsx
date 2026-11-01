import { useState } from "react";
import { motion } from "motion/react";
import type { State } from "./generated/contract";
import type { Submit } from "./Puzzles";
import { EvidenceArt } from "./EvidenceArt";
export function Board({
  state,
  busy,
  submit,
}: {
  state: State;
  busy: boolean;
  submit: Submit;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const [order, setOrder] = useState<string[]>([]);
  const cards = [...state.evidence].sort((a, b) => {
    const rank = (id: string) => {
      const i = order.indexOf(id);
      return i < 0
        ? order.length + state.evidence.findIndex((e) => e.id === id)
        : i;
    };
    return rank(a.id) - rank(b.id);
  });
  function moveCard(id: string, delta: number) {
    const ids = cards.map((e) => e.id);
    const from = ids.indexOf(id),
      to = from + delta;
    if (to < 0 || to >= ids.length) return;
    [ids[from], ids[to]] = [ids[to], ids[from]];
    setOrder(ids);
  }
  function toggle(id: string) {
    setSelected((old) =>
      old.includes(id)
        ? old.filter((x) => x !== id)
        : old.length < 2
          ? [...old, id]
          : old,
    );
  }
  return (
    <section>
      <p className="eyebrow">Connections / {state.insights.length} confirmed</p>
      <h2>The detective board</h2>
      <p>
        Arrange the cards freely. Select exactly two clues to test a deduction.
        Card placement never changes the case.
      </p>
      <div className="board">
        {state.insights.length > 0 && (
          <div className="board-thread" aria-hidden="true" />
        )}
        {state.ghosts.map((g) => (
          <div className="suspect" key={g.id}>
            {g.display_name}
          </div>
        ))}
        <div className="evidence-grid">
          {cards.map((e, index) => (
            <motion.article
              drag
              dragMomentum={false}
              dragConstraints={{ left: -20, right: 20, top: -20, bottom: 20 }}
              className="board-card"
              key={e.id}
            >
              <EvidenceArt evidence={e} assets={state.assets} />
              <p className="eyebrow">{e.room_id.replaceAll("_", " ")}</p>
              <h3>{e.title}</h3>
              <p>{e.description}</p>
              <label>
                <input
                  type="checkbox"
                  checked={selected.includes(e.id)}
                  disabled={
                    busy || (!selected.includes(e.id) && selected.length === 2)
                  }
                  onChange={() => toggle(e.id)}
                />{" "}
                Connect {e.title}
              </label>
              <div className="card-order">
                <button
                  aria-label={"Move " + e.title + " earlier"}
                  disabled={index === 0}
                  onClick={() => moveCard(e.id, -1)}
                >
                  ← Earlier
                </button>
                <button
                  aria-label={"Move " + e.title + " later"}
                  disabled={index === cards.length - 1}
                  onClick={() => moveCard(e.id, 1)}
                >
                  Later →
                </button>
              </div>
            </motion.article>
          ))}
        </div>
      </div>
      {state.evidence.length === 0 && (
        <p>No evidence collected yet. Inspect the mansion’s objects.</p>
      )}
      <button
        className="primary"
        disabled={busy || selected.length !== 2}
        onClick={() =>
          submit({
            type: "connect_evidence",
            evidence_ids: [selected[0], selected[1]],
          })
        }
      >
        Test connection
      </button>
      <h3>Confirmed deductions</h3>
      {state.insights.length === 0 ? (
        <p>No confirmed deductions yet.</p>
      ) : (
        state.insights.map((i) => (
          <article className="insight" key={i.id}>
            <h4>{i.title}</h4>
            <p>{i.description}</p>
            <small>
              {i.evidence_ids
                .map(
                  (id) => state.evidence.find((e) => e.id === id)?.title ?? id,
                )
                .join(" ↔ ")}
            </small>
          </article>
        ))
      )}
    </section>
  );
}
