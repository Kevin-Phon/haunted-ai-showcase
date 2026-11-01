import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "../App";
import { ApiError, type Transport } from "../api";
import initial from "../../../../contracts/v1/examples/session.response.json";
function capped() {
  const fresh = structuredClone(initial);
  fresh.state.session_id = "22222222-2222-4222-8222-222222222222";
  return {
    create: vi.fn().mockResolvedValueOnce(initial).mockResolvedValue(fresh),
    get: vi.fn(),
    restart: vi.fn(),
    action: vi
      .fn()
      .mockRejectedValue(
        new ApiError(
          "SESSION_ACTION_LIMIT",
          "Investigation lifetime limit reached. Start a new investigation.",
          500,
          false,
        ),
      ),
  } satisfies Transport;
}
async function reachCap(api: ReturnType<typeof capped>) {
  const user = userEvent.setup();
  render(<App transport={api} />);
  await user.selectOptions(
    screen.getByRole("combobox", { name: "Dialogue mode" }),
    "demo",
  );
  await user.click(screen.getByRole("button", { name: "Enter the manor" }));
  await user.click(await screen.findByRole("button", { name: /◇ Library/ }));
  await screen.findByText("SESSION ACTION LIMIT");
  return user;
}
describe("R03-F1 explicit capacity recovery", () => {
  it("warns and confirms before creating a new session, preserving demo mode and never restarting the capped one", async () => {
    const api = capped(),
      user = await reachCap(api);
    expect(api.create).toHaveBeenCalledTimes(1);
    await user.click(
      screen.getByRole("button", { name: "Start new investigation" }),
    );
    expect(
      screen.getByText(/Current investigation progress will not carry over/),
    ).toBeInTheDocument();
    expect(api.create).toHaveBeenCalledTimes(1);
    expect(api.restart).not.toHaveBeenCalled();
    await user.click(
      screen.getByRole("button", { name: "Cancel new investigation" }),
    );
    expect(api.create).toHaveBeenCalledTimes(1);
    await user.click(
      screen.getByRole("button", { name: "Start new investigation" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Confirm new investigation" }),
    );
    await waitFor(() => expect(api.create).toHaveBeenCalledTimes(2));
    expect(api.create.mock.calls[1][0]).toBe("demo");
    expect(api.create.mock.calls[1][1]).not.toBe(api.create.mock.calls[0][1]);
    expect(api.restart).not.toHaveBeenCalled();
    expect(localStorage.getItem("blackthorn-session")).toBe(
      "22222222-2222-4222-8222-222222222222",
    );
  });
  it("shows process-capacity rejection honestly without automatic retries or silently discarding the current view", async () => {
    const api = capped();
    api.create.mockRejectedValueOnce(
      new ApiError(
        "CONTENT_UNAVAILABLE",
        "All investigation slots are occupied. Restart the backend to free process capacity.",
        null,
        false,
      ),
    );
    const user = await reachCap(api);
    await user.click(
      screen.getByRole("button", { name: "Start new investigation" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Confirm new investigation" }),
    );
    await screen.findByText("CONTENT UNAVAILABLE");
    expect(api.create).toHaveBeenCalledTimes(2);
    expect(api.restart).not.toHaveBeenCalled();
    expect(
      screen.getByRole("heading", { name: "Entrance Hall" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Retry same request" }),
    ).not.toBeInTheDocument();
  });
});
