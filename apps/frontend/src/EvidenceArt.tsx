import type { Evidence, State } from "./generated/contract";
import { safeAsset } from "./RoomScene";

export function EvidenceArt({
  evidence,
  assets,
}: {
  evidence: Evidence;
  assets: State["assets"];
}) {
  const asset = assets.find((item) => item.id === evidence.asset_id);
  return asset && safeAsset(asset.src) ? (
    <img
      className="evidence-thumbnail"
      src={safeAsset(asset.src)}
      alt={asset.alt}
      loading="lazy"
      width={160}
      height={100}
    />
  ) : (
    <div
      className="evidence-sketch"
      data-evidence={evidence.id}
      aria-hidden="true"
    >
      <span />
      <i />
      <b />
    </div>
  );
}
