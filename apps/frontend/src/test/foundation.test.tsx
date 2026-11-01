import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LetterPuzzle, CalibrationPuzzle } from "../Puzzles";
import { Board } from "../Board";
import { GhostDialogue } from "../GhostDialogue";
import { ApiClient } from "../api";
import letter from "../../../../contracts/v1/examples/letter-available.response.json";
import machine from "../../../../contracts/v1/examples/calibration-available.response.json";
import board from "../../../../contracts/v1/examples/deduction-accepted.response.json";
import ghost from "../../../../contracts/v1/examples/eleanor-fallback.response.json";
import type { State } from "../generated/contract";

describe("accessible investigation controls", () => {
  it("submits four unique letter assignments using only select controls", async () => {
    const user = userEvent.setup(),
      submit = vi.fn();
    const puzzle = (letter.state as unknown as State).puzzles[0];
    if (puzzle.id !== "letter_reconstruction") throw Error("fixture");
    render(<LetterPuzzle puzzle={puzzle} busy={false} submit={submit} />);
    expect(
      screen.getByRole("button", { name: "Submit reconstruction" }),
    ).toBeDisabled();
    for (let i = 0; i < 4; i++)
      await user.selectOptions(
        screen.getByLabelText(puzzle.presentation.slots[i].label),
        puzzle.presentation.pieces[i].id,
      );
    await user.click(
      screen.getByRole("button", { name: "Submit reconstruction" }),
    );
    expect(submit).toHaveBeenCalledWith({
      type: "submit_puzzle",
      puzzle_id: "letter_reconstruction",
      solution: {
        placements: puzzle.presentation.slots.map((s, i) => ({
          slot_id: s.id,
          piece_id: puzzle.presentation.pieces[i].id,
        })),
      },
    });
  });
  it("swaps an already-placed letter piece and resets drafts", async () => {
    const user = userEvent.setup();
    const puzzle = (letter.state as unknown as State).puzzles[0];
    if (puzzle.id !== "letter_reconstruction") throw Error("fixture");
    render(<LetterPuzzle puzzle={puzzle} busy={false} submit={vi.fn()} />);
    const [a, b] = puzzle.presentation.slots;
    const [p, q] = puzzle.presentation.pieces;
    await user.selectOptions(screen.getByLabelText(a.label), p.id);
    await user.selectOptions(screen.getByLabelText(b.label), q.id);
    await user.selectOptions(screen.getByLabelText(b.label), p.id);
    expect(screen.getByLabelText(a.label)).toHaveValue(q.id);
    await user.click(screen.getByRole("button", { name: "Reset draft" }));
    expect(screen.getByLabelText(a.label)).toHaveValue("");
  });
  it("submits calibration domains without computing a solution", async () => {
    const user = userEvent.setup(),
      submit = vi.fn();
    const puzzle = (machine.state as unknown as State).puzzles[0];
    if (puzzle.id !== "machine_calibration") throw Error("fixture");
    render(<CalibrationPuzzle puzzle={puzzle} busy={false} submit={submit} />);
    await user.selectOptions(screen.getByLabelText("Phase"), "violet");
    await user.selectOptions(screen.getByLabelText("Stabilizer"), "engaged");
    await user.click(
      screen.getByRole("button", { name: "Submit calibration" }),
    );
    expect(submit).toHaveBeenCalledWith({
      type: "submit_puzzle",
      puzzle_id: "machine_calibration",
      solution: { power_level: 0, phase: "violet", stabilizer: "engaged" },
    });
  });
  it("connects two collected clues without granting a local insight", async () => {
    const user = userEvent.setup(),
      submit = vi.fn();
    const state = board.state as unknown as State;
    render(
      <Board state={{ ...state, insights: [] }} busy={false} submit={submit} />,
    );
    const checks = screen.getAllByRole("checkbox");
    await user.click(checks[0]);
    await user.click(checks[1]);
    await user.click(screen.getByRole("button", { name: "Test connection" }));
    expect(submit).toHaveBeenCalledWith({
      type: "connect_evidence",
      evidence_ids: [state.evidence[0].id, state.evidence[1].id],
    });
    expect(
      screen.getByText("No confirmed deductions yet."),
    ).toBeInTheDocument();
  });
  it("preserves explicit fallback labels and sends tone/evidence with a question", async () => {
    const user = userEvent.setup(),
      submit = vi.fn();
    const state = ghost.state as unknown as State;
    render(<GhostDialogue state={state} busy={false} submit={submit} />);
    expect(screen.getAllByText(/Fallback/).length).toBeGreaterThan(0);
    await user.type(screen.getByLabelText("Your question"), "What happened?");
    await user.selectOptions(screen.getByLabelText("Tone"), "respectful");
    await user.click(screen.getByRole("button", { name: "Ask ghost" }));
    expect(submit).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "talk",
        message: "What happened?",
        tone: "respectful",
        presented_evidence_ids: [],
      }),
    );
  });
});

describe("API transport", () => {
  it("uses exact wire envelope and does not automatically retry mutations", async () => {
    const fetcher = vi.fn().mockRejectedValue(new TypeError("offline"));
    const client = new ApiClient(fetcher);
    await expect(
      client.action(
        "session",
        7,
        { type: "navigate", room_id: "library" },
        "same-id",
      ),
    ).rejects.toThrow();
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({
      request_id: "same-id",
      expected_revision: 7,
      action: { type: "navigate", room_id: "library" },
    });
  });
  it("surfaces typed conflicts with safe recovery metadata", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          contract_version: "1.0.0",
          error: {
            code: "REVISION_CONFLICT",
            message: "Refresh state",
            request_id: null,
            current_revision: 9,
            retryable: true,
          },
        }),
        { status: 409 },
      ),
    );
    await expect(new ApiClient(fetcher).get("session")).rejects.toMatchObject({
      code: "REVISION_CONFLICT",
      revision: 9,
    });
  });
});
