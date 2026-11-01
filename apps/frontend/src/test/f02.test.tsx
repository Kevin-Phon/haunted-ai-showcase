import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "../App";
import { ApiError, type Transport } from "../api";
import { LetterPuzzle, CalibrationPuzzle } from "../Puzzles";
import initial from "../../../../contracts/v1/examples/session.response.json";
import letter from "../../../../contracts/v1/examples/letter-available.response.json";
import machine from "../../../../contracts/v1/examples/calibration-available.response.json";
import accepted from "../../../../contracts/v1/examples/navigate.response.json";
import type { State } from "../generated/contract";
function api() {
  return {
    create: vi.fn().mockResolvedValue(initial),
    get: vi.fn().mockResolvedValue(initial),
    action: vi
      .fn()
      .mockRejectedValueOnce(
        new ApiError("NETWORK_UNCERTAIN", "Response lost", null, true),
      )
      .mockResolvedValue(accepted),
    restart: vi.fn(),
  } satisfies Transport;
}
async function lostRequest(transport: ReturnType<typeof api>) {
  const user = userEvent.setup();
  render(<App transport={transport} />);
  await user.click(screen.getByRole("button", { name: "Enter the manor" }));
  await user.click(await screen.findByRole("button", { name: /◇ Library/ }));
  await screen.findByRole("button", { name: "Retry same request" });
  return user;
}
describe("F02 recovery regression", () => {
  it("blocks restart while a mutation outcome is unknown", async () => {
    const transport = api();
    await lostRequest(transport);
    expect(
      screen.getByRole("button", { name: "Restart investigation" }),
    ).toBeDisabled();
  });
  it("retains the pending request after reading a snapshot and retries its original envelope", async () => {
    const transport = api();
    const user = await lostRequest(transport);
    await user.click(
      screen.getByRole("button", { name: "Retrieve latest state" }),
    );
    await waitFor(() => expect(transport.get).toHaveBeenCalledTimes(1));
    expect(
      await screen.findByRole("button", { name: "Retry same request" }),
    ).toBeEnabled();
    expect(screen.getByRole("button", { name: /◇ Library/ })).toBeDisabled();
    await user.click(
      screen.getByRole("button", { name: "Retry same request" }),
    );
    await waitFor(() => expect(transport.action).toHaveBeenCalledTimes(2));
    expect(transport.action.mock.calls[0]).toEqual(
      transport.action.mock.calls[1],
    );
  });
});
describe("F02 definitive retry rejection", () => {
  it("releases the uncertain-request gate when its exact retry is definitively rejected", async () => {
    const transport = api();
    transport.action.mockRejectedValueOnce(
      new ApiError("REVISION_CONFLICT", "Retrieve current revision", 2, true),
    );
    const user = await lostRequest(transport);
    await user.click(
      screen.getByRole("button", { name: "Retry same request" }),
    );
    await screen.findByText("REVISION CONFLICT");
    expect(
      screen.queryByRole("button", { name: "Retry same request" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /◇ Library/ })).toBeEnabled();
  });
});
describe("F02 puzzle input regression", () => {
  it("returns cleared letter fragments to the tray without filling another empty slot", async () => {
    const puzzle = (letter.state as unknown as State).puzzles[0];
    if (puzzle.id !== "letter_reconstruction") throw Error("fixture");
    const user = userEvent.setup();
    render(<LetterPuzzle puzzle={puzzle} busy={false} submit={vi.fn()} />);
    const [a, b] = puzzle.presentation.slots;
    await user.selectOptions(
      screen.getByLabelText(a.label),
      puzzle.presentation.pieces[0].id,
    );
    await user.selectOptions(
      screen.getByLabelText(b.label),
      puzzle.presentation.pieces[1].id,
    );
    await user.selectOptions(screen.getByLabelText(a.label), "");
    await user.selectOptions(screen.getByLabelText(b.label), "");
    expect(screen.getByLabelText(a.label)).toHaveValue("");
    expect(screen.getByLabelText(b.label)).toHaveValue("");
  });
  it.each(["", "0.5", "4", "-1"])(
    "does not submit invalid calibration power %j",
    async (value) => {
      const puzzle = (machine.state as unknown as State).puzzles[0];
      if (puzzle.id !== "machine_calibration") throw Error("fixture");
      const user = userEvent.setup(),
        submit = vi.fn();
      render(
        <CalibrationPuzzle puzzle={puzzle} busy={false} submit={submit} />,
      );
      const power = screen.getByRole("spinbutton");
      await user.clear(power);
      if (value) await user.type(power, value);
      expect(
        screen.getByRole("button", { name: "Submit calibration" }),
      ).toBeDisabled();
      expect(submit).not.toHaveBeenCalled();
    },
  );
});
