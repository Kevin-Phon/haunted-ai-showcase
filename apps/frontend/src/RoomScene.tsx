import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import type { Hotspot, State } from "./generated/contract";
import type { Submit } from "./Puzzles";
import { EvidenceArt } from "./EvidenceArt";
export function safeAsset(src: string) {
  return /^[a-zA-Z0-9_./-]+$/.test(src) &&
    !src.startsWith("//") &&
    !src.split("/").includes("..")
    ? src
    : undefined;
}
export function RoomScene({
  state,
  busy,
  submit,
  onInspect,
}: {
  state: State;
  busy: boolean;
  submit: Submit;
  onInspect: (hotspot: Hotspot) => void;
}) {
  const [missingRoom, setMissingRoom] = useState<string | null>(null);
  const [zoom, setZoom] = useState(false);
  const scene = state.scene;
  const navigate = state.available_actions.filter((a) => a.type === "navigate");
  return (
    <section aria-label="Mansion exploration">
      <div className="room-title">
        <div>
          <p className="eyebrow">
            Blackthorn Manor / {state.current_room_id.replaceAll("_", " ")}
          </p>
          <h1>{scene.title}</h1>
        </div>
        <span className="chapter">1926 — 2026</span>
      </div>
      <p className="room-description">{scene.description}</p>
      <p className="explore-guide">
        Click an illuminated object below, or choose it from Objects in this
        room. Inspect first, then use any available action.
      </p>
      <motion.div
        className="scene"
        data-room={scene.room_id}
        onPointerMove={(e) => {
          const bounds = e.currentTarget.getBoundingClientRect();
          e.currentTarget.style.setProperty(
            "--depth-x",
            `${((e.clientX - bounds.left) / bounds.width - 0.5) * 6}px`,
          );
        }}
        onPointerLeave={(e) =>
          e.currentTarget.style.setProperty("--depth-x", "0px")
        }
        initial={{ opacity: 0.7 }}
        animate={{ opacity: 1 }}
        key={scene.room_id}
        style={{ aspectRatio: `${scene.canvas.width}/${scene.canvas.height}` }}
      >
        <motion.div
          className="scene-camera"
          animate={{ scale: zoom ? 1.15 : 1 }}
          transition={{ duration: 0.35 }}
        >
          <div className="architecture" aria-hidden="true">
            <div className="window window-left" />
            <div className="window window-right" />
            <div className="arch-door" />
            <div className="floor" />
            <div className="chandelier" />
            <div className="scene-desk" />
          </div>
          {scene.layers.map((layer) => {
            const asset = state.assets.find((a) => a.id === layer.asset_id);
            return asset && safeAsset(asset.src) ? (
              <img
                className="scene-layer"
                style={{ zIndex: layer.z_index }}
                key={layer.id}
                src={safeAsset(asset.src)}
                width={scene.canvas.width}
                height={scene.canvas.height}
                fetchPriority="high"
                alt={layer.decorative ? "" : asset.alt}
                onError={() => setMissingRoom(scene.room_id)}
              />
            ) : null;
          })}
          {scene.objects.some(
            (object) =>
              object.id === "library_letter_drawer" &&
              object.state === "closed",
          ) && (
            <div className="drawer-closed-cover" aria-hidden="true">
              <span />
            </div>
          )}
          <div className="mist" aria-hidden="true" />
          <div className="scene-vignette" aria-hidden="true" />
          {scene.hotspots.map((h) => (
            <button
              key={h.id}
              className="hotspot"
              disabled={busy}
              style={{
                left: h.bounds.x * 100 + "%",
                top: h.bounds.y * 100 + "%",
                width: h.bounds.width * 100 + "%",
                height: h.bounds.height * 100 + "%",
              }}
              onClick={() => onInspect(h)}
              aria-label={"Inspect " + h.label}
            >
              <span>✧</span>
              <span className="hotspot-label">{h.label}</span>
            </button>
          ))}
        </motion.div>
        <span className="scene-note">
          {scene.layers.length === 0 || missingRoom === scene.room_id
            ? "Temporary architectural staging · final room art pending"
            : "Layered scene · inspect illuminated objects"}
        </span>
      </motion.div>
      <button aria-pressed={zoom} onClick={() => setZoom(!zoom)}>
        {zoom ? "Reset scene zoom" : "Zoom scene"}
      </button>
      <section className="object-list" aria-label="Objects in this room">
        <h2>
          Objects in this room <small>({scene.hotspots.length})</small>
        </h2>
        {[...scene.hotspots]
          .sort((a, b) => a.focus_order - b.focus_order)
          .map((h) => (
            <button key={h.id} disabled={busy} onClick={() => onInspect(h)}>
              <span aria-hidden="true">✧ </span>
              {h.label} · Inspect
            </button>
          ))}
      </section>
      {state.current_room_id !== "entrance_hall" && (
        <p className="route-guide">
          Return to the Entrance Hall to reach the other rooms.
        </p>
      )}
      <nav className="room-nav" aria-label="Room navigation">
        {state.rooms.map((room) => (
          <button
            key={room.id}
            aria-current={
              room.id === state.current_room_id ? "location" : undefined
            }
            disabled={busy || !navigate.some((a) => a.target_id === room.id)}
            title={room.hint ?? undefined}
            onClick={() => submit({ type: "navigate", room_id: room.id })}
          >
            {room.unlocked ? "◇" : "⌑"}{" "}
            {room.id === "entrance_hall" && state.current_room_id !== room.id
              ? "Return to "
              : ""}
            {room.title}
            {!room.unlocked && (
              <small>Locked{room.hint ? " · " + room.hint : ""}</small>
            )}
          </button>
        ))}
      </nav>
    </section>
  );
}
export function Inspection({
  hotspot,
  state,
  busy,
  submit,
  close,
}: {
  hotspot: Hotspot;
  state: State;
  busy: boolean;
  submit: Submit;
  close: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const prior = document.activeElement as HTMLElement | null;
    const el = ref.current;
    if (el?.showModal) el.showModal();
    else el?.setAttribute("open", "");
    el?.querySelector("button")?.focus();
    return () => {
      el?.close?.();
      prior?.focus();
    };
  }, []);
  const current = state.scene.hotspots.find((h) => h.id === hotspot.id);
  const obj = state.scene.objects.find((o) => o.id === hotspot.object_id);
  return (
    <dialog
      ref={ref}
      aria-label={"Inspect " + hotspot.label}
      onCancel={(e) => {
        e.preventDefault();
        close();
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") {
          e.preventDefault();
          close();
        }
        if (e.key === "Tab") {
          const controls = Array.from(
            ref.current?.querySelectorAll<HTMLButtonElement>(
              "button:not(:disabled)",
            ) ?? [],
          );
          const first = controls[0],
            last = controls.at(-1);
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last?.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first?.focus();
          }
        }
      }}
    >
      <button className="close" onClick={close}>
        Close inspection
      </button>
      <p className="eyebrow">Object inspection</p>
      <h2>{hotspot.label}</h2>
      <div
        className={"object-illustration " + (obj?.state ?? "closed")}
        aria-hidden="true"
      >
        <span />
      </div>
      <p>
        {obj?.description ??
          "Inspection requested. The server determines what this object reveals."}
      </p>
      {obj && <p className="mode-badge">{obj.state}</p>}
      <div className="actions">
        {current?.interactions.map((i) => (
          <button
            key={i.operation}
            disabled={busy || !i.enabled}
            title={i.disabled_reason ?? undefined}
            onClick={() =>
              submit({
                type: "interact_object",
                object_id: hotspot.object_id,
                operation: i.operation,
              })
            }
          >
            {i.label}
            {i.disabled_reason ? " · " + i.disabled_reason : ""}
          </button>
        ))}
      </div>
      {!current && (
        <p>
          This interaction is no longer available in the accepted room state.
        </p>
      )}
    </dialog>
  );
}
export function Journal({ state }: { state: State }) {
  return (
    <section>
      <p className="eyebrow">Collected / {state.evidence.length}</p>
      <h2>Detective’s journal</h2>
      {state.evidence.length === 0 ? (
        <p>Your journal is empty. Inspect objects to uncover evidence.</p>
      ) : (
        <div className="journal-grid">
          {state.evidence.map((e) => (
            <article className="journal-entry" key={e.id}>
              <EvidenceArt evidence={e} assets={state.assets} />
              <small>{e.room_id.replaceAll("_", " ")}</small>
              <h3>{e.title}</h3>
              <p>{e.description}</p>
              {e.annotations.map((a, i) => (
                <p className="annotation" key={i}>
                  {a}
                </p>
              ))}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
