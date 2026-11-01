import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "../App";
import { ApiError, type Transport } from "../api";
import initial from "../../../../contracts/v1/examples/session.response.json";
import discovery from "../../../../contracts/v1/examples/discovery.response.json";
import restart from "../../../../contracts/v1/examples/restart.response.json";
import event from "../../../../contracts/v1/examples/event-new.response.json";
import ending from "../../../../contracts/v1/examples/partial_truth.response.json";
import type { SessionResponse, ActionResponse } from "../generated/contract";
// A typed public hotspot extends the empty-scene fixture solely for component interaction tests.
const session: SessionResponse = structuredClone(
  initial,
) as unknown as SessionResponse;
session.state.scene.hotspots = [
  {
    id: "test_desk",
    object_id: "test_drawer",
    label: "Writing desk",
    focus_order: 0,
    bounds: { x: 0.3, y: 0.5, width: 0.15, height: 0.2 },
    interactions: [],
  },
];
function transport() {
  return {
    create: vi.fn().mockResolvedValue(session as SessionResponse),
    get: vi.fn().mockResolvedValue(session),
    restart: vi.fn().mockResolvedValue(restart),
    action: vi.fn().mockResolvedValue(discovery as ActionResponse),
  } satisfies Transport;
}
describe("session orchestration", () => {
  it("starts with real transport choice and applies only accepted discovery state", async () => {
    const user = userEvent.setup(),
      api = transport();
    render(<App transport={api} />);
    await user.click(screen.getByRole("button", { name: "Enter the manor" }));
    await screen.findByRole("heading", { name: session.state.scene.title });
    const hotspot = session.state.scene.hotspots[0];
    await user.click(
      screen.getByRole("button", { name: "Inspect " + hotspot.label }),
    );
    await waitFor(() =>
      expect(api.action).toHaveBeenCalledWith(
        session.state.session_id,
        0,
        { type: "inspect", hotspot_id: hotspot.id },
        expect.any(String),
      ),
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
  it("retries an uncertain mutation with the identical request envelope", async () => {
    const user = userEvent.setup(),
      api = transport();
    api.action.mockRejectedValueOnce(
      new ApiError("NETWORK_UNCERTAIN", "Response lost", null, true),
    );
    render(<App transport={api} />);
    await user.click(screen.getByRole("button", { name: "Enter the manor" }));
    await screen.findByRole("heading", { name: session.state.scene.title });
    await user.click(
      screen.getByRole("button", {
        name: "Inspect " + session.state.scene.hotspots[0].label,
      }),
    );
    await user.click(
      await screen.findByRole("button", { name: "Retry same request" }),
    );
    await waitFor(() => expect(api.action).toHaveBeenCalledTimes(2));
    expect(api.action.mock.calls[0]).toEqual(api.action.mock.calls[1]);
  });
  it("shows terminal state and restarts only after confirmation", async () => {
    const user = userEvent.setup(),
      api = transport();
    api.create.mockResolvedValue(ending);
    render(<App transport={api} />);
    await user.click(screen.getByRole("button", { name: "Enter the manor" }));
    await screen.findByRole("heading", { name: "Partial Truth" });
    await user.click(
      screen.getByRole("button", { name: "Restart investigation" }),
    );
    expect(api.restart).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Confirm restart" }));
    await waitFor(() => expect(api.restart).toHaveBeenCalledTimes(1));
    await screen.findByRole("heading", { name: restart.state.scene.title });
    expect(
      screen.queryByRole("heading", { name: "Partial Truth" }),
    ).not.toBeInTheDocument();
  });
  it("does not replay a dismissed supernatural occurrence from a cached response", async () => {
    const user = userEvent.setup(),
      api = transport();
    api.action.mockResolvedValue(event);
    render(<App transport={api} />);
    await user.click(screen.getByRole("button", { name: "Enter the manor" }));
    await screen.findByRole("heading", { name: session.state.scene.title });
    await user.click(
      screen.getByRole("button", {
        name: "Inspect " + session.state.scene.hotspots[0].label,
      }),
    );
    await user.keyboard("{Escape}");
    await user.click(
      await screen.findByRole("button", { name: "Dismiss apparition" }),
    );
    await user.click(screen.getByRole("button", { name: /◇ Library/ }));
    await waitFor(() => expect(api.action).toHaveBeenCalledTimes(2));
    expect(
      screen.queryByRole("button", { name: "Dismiss apparition" }),
    ).not.toBeInTheDocument();
  });
  it("respects reduced motion preference without hiding controls", async () => {
    const user = userEvent.setup();
    const { container } = render(<App transport={transport()} />);
    await user.click(screen.getByLabelText("Reduced motion"));
    expect(container.querySelector(".app")).toHaveClass("reduce-motion");
    expect(
      screen.getByRole("button", { name: "Enter the manor" }),
    ).toBeEnabled();
  });
});
