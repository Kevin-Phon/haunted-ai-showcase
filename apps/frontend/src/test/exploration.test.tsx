import { it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RoomScene } from "../RoomScene";
import fixture from "../../../../contracts/v1/examples/session.response.json";
import type { State } from "../generated/contract";

it("keeps object inspection visible without expanding a disclosure", async () => {
  const state = structuredClone(fixture.state) as unknown as State;
  state.scene.hotspots = [
    {
      id: "hs",
      object_id: "plaque",
      label: "Case plaque",
      focus_order: 0,
      bounds: { x: 0.2, y: 0.4, width: 0.15, height: 0.2 },
      interactions: [],
    },
  ];
  const inspect = vi.fn();
  render(
    <RoomScene
      state={state}
      busy={false}
      submit={vi.fn()}
      onInspect={inspect}
    />,
  );
  const list = screen.getByRole("region", { name: "Objects in this room" });
  await userEvent.click(
    within(list).getByRole("button", { name: /Case plaque/ }),
  );
  expect(inspect).toHaveBeenCalledWith(state.scene.hotspots[0]);
  expect(list.closest("details")).toBeNull();
});

it("explains Hall routes and only enables server-authorized travel", async () => {
  const state = structuredClone(fixture.state) as unknown as State;
  state.current_room_id = "study";
  state.available_actions = [
    { type: "navigate", target_id: "entrance_hall", label: "Entrance Hall" },
  ];
  const submit = vi.fn();
  render(
    <RoomScene
      state={state}
      busy={false}
      submit={submit}
      onInspect={vi.fn()}
    />,
  );
  expect(
    screen.getByText(/Return to the Entrance Hall to reach the other rooms/),
  ).toBeVisible();
  await userEvent.click(
    screen.getByRole("button", { name: /Return to Entrance Hall/ }),
  );
  expect(submit).toHaveBeenCalledWith({
    type: "navigate",
    room_id: "entrance_hall",
  });
});
