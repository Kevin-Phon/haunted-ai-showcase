// Optional real API projection audit. No private content is imported into this package.
import { readFileSync } from "node:fs";
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RoomScene, Inspection } from "../RoomScene";
import { LetterPuzzle } from "../Puzzles";
import { GhostDialogue } from "../GhostDialogue";
import { Theory } from "../Theory";
import { App } from "../App";
import type { State } from "../generated/contract";
const source = process.env.HAUNTED_PUBLIC_AUDIT;
const snapshots = source
  ? (JSON.parse(readFileSync(source, "utf8")) as Record<string, State>)
  : null;
describe.skipIf(!snapshots)(
  "F02 real API public projection controls (in-process receipts)",
  () => {
    it("keyboard room/hotspot inspection uses public action references", async () => {
      const s = snapshots!.library,
        submit = vi.fn(),
        inspect = vi.fn(),
        user = userEvent.setup();
      render(
        <RoomScene
          state={s}
          busy={false}
          submit={submit}
          onInspect={inspect}
        />,
      );
      const hotspot = s.scene.hotspots[0];
      screen.getByRole("button", { name: "Inspect " + hotspot.label }).focus();
      await user.keyboard("{Enter}");
      expect(inspect).toHaveBeenCalledWith(hotspot);
      const descriptor = s.available_actions.find(
        (a) => a.type === "navigate",
      )!;
      const room = s.rooms.find((r) => r.id === descriptor.target_id)!;
      const button = screen.getByRole("button", {
        name: new RegExp(room.title),
      });
      button.focus();
      await user.keyboard("{Enter}");
      expect(submit).toHaveBeenCalledWith({
        type: "navigate",
        room_id: room.id,
      });
    });
    it("keyboard object operation and modal focus wrapping work on the real public hotspot", async () => {
      const s = snapshots!.library;
      const hotspot = s.scene.hotspots.find((h) =>
        h.interactions.some((i) => i.enabled),
      )!;
      const action = hotspot.interactions.find((i) => i.enabled)!;
      const submit = vi.fn(),
        close = vi.fn(),
        user = userEvent.setup();
      render(
        <Inspection
          hotspot={hotspot}
          state={s}
          busy={false}
          submit={submit}
          close={close}
        />,
      );
      const first = screen.getByRole("button", { name: "Close inspection" });
      expect(first).toHaveFocus();
      await user.keyboard("{Shift>}{Tab}{/Shift}");
      expect(screen.getByRole("button", { name: action.label })).toHaveFocus();
      await user.keyboard("{Enter}");
      expect(submit).toHaveBeenCalledWith({
        type: "interact_object",
        object_id: hotspot.object_id,
        operation: action.operation,
      });
      await user.keyboard("{Escape}");
      expect(close).toHaveBeenCalled();
    });
    it("revealed real letter accepts non-drag controls without revealing an answer", async () => {
      const puzzle = snapshots!.interacted.puzzles.find(
        (p) => p.id === "letter_reconstruction",
      );
      if (!puzzle || puzzle.id !== "letter_reconstruction")
        throw Error("Canonical letter not revealed");
      const submit = vi.fn(),
        user = userEvent.setup();
      render(<LetterPuzzle puzzle={puzzle} busy={false} submit={submit} />);
      for (let i = 0; i < 4; i++)
        await user.selectOptions(
          screen.getByLabelText(puzzle.presentation.slots[i].label),
          puzzle.presentation.pieces[i].id,
        );
      screen.getByRole("button", { name: "Submit reconstruction" }).focus();
      await user.keyboard("{Enter}");
      expect(submit).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "submit_puzzle",
          puzzle_id: puzzle.id,
        }),
      );
    });
    it("real demo dialogue and relationship state render with the correct label", () => {
      const s = snapshots!.dialogue;
      render(<GhostDialogue state={s} busy={false} submit={vi.fn()} />);
      expect(screen.getByText("Deterministic demo")).toBeInTheDocument();
      const turn = s.dialogue.at(-1)!;
      expect(screen.getByText(turn.response_text)).toBeInTheDocument();
    });
    it("structured theory remains reviewable before keyboard terminal submission", async () => {
      const s = snapshots!.theory,
        submit = vi.fn(),
        user = userEvent.setup();
      render(<Theory state={s} busy={false} submit={submit} />);
      const option = s.accusation.options[0];
      await user.selectOptions(
        screen.getByLabelText(option.group.replaceAll("_", " ")),
        option.id,
      );
      screen.getByRole("button", { name: "Review theory" }).focus();
      await user.keyboard("{Enter}");
      expect(submit).not.toHaveBeenCalled();
      screen.getByRole("button", { name: "Submit final theory" }).focus();
      await user.keyboard("{Enter}");
      expect(submit).toHaveBeenCalledWith({
        type: "accuse",
        claims: [{ claim_id: option.id, evidence_ids: [] }],
      });
    });
    it("real terminal projection and restart confirmation preserve server authority", async () => {
      const s = snapshots!.terminal,
        user = userEvent.setup();
      const api = {
        create: vi.fn().mockResolvedValue({ request_id: null, state: s }),
        get: vi.fn(),
        action: vi.fn(),
        restart: vi
          .fn()
          .mockResolvedValue({ request_id: null, state: snapshots!.restarted }),
      };
      render(<App transport={api} />);
      screen.getByRole("button", { name: "Enter the manor" }).focus();
      await user.keyboard("{Enter}");
      await screen.findByRole("heading", { name: s.ending!.title });
      screen.getByRole("button", { name: "Restart investigation" }).focus();
      await user.keyboard("{Enter}");
      expect(api.restart).not.toHaveBeenCalled();
      screen.getByRole("button", { name: "Confirm restart" }).focus();
      await user.keyboard("{Enter}");
      await waitFor(() => expect(api.restart).toHaveBeenCalledTimes(1));
      await screen.findByRole("heading", {
        name: snapshots!.restarted.scene.title,
      });
    });
  },
);
