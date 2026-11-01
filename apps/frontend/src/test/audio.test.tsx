import { it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AmbientAudio, DiscoverySound } from "../AmbientAudio";
import userEvent from "@testing-library/user-event";
import { App } from "../App";
import type { Transport } from "../api";
import type { SessionResponse } from "../generated/contract";
import initial from "../../../../contracts/v1/examples/session.response.json";

it.each([
  ["media/server-selected-cue.wav", "audio", "media/server-selected-cue.wav"],
  [null, "audio", null],
  ["https://unapproved.example/cue.wav", "audio", null],
  ["media/picture.png", "image", null],
] as const)(
  "uses only a safe public audio reference (%s, %s)",
  async (src, kind, expected) => {
    vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
    const response = structuredClone(initial) as unknown as SessionResponse;
    response.state.assets = src
      ? [
          {
            id: "audio_discovery",
            kind,
            src,
            alt: "Discovery cue",
            attribution_id: "test",
            width: null,
            height: null,
          },
        ]
      : [];
    const transport = {
      create: vi.fn().mockResolvedValue(response),
      get: vi.fn(),
      action: vi.fn(),
      restart: vi.fn(),
    } satisfies Transport;
    const view = render(<App transport={transport} />);
    await userEvent.click(
      screen.getByRole("button", { name: "Enter the manor" }),
    );
    await screen.findByRole("heading", {
      name: response.state.scene.title,
    });
    await userEvent.click(
      screen.getByRole("checkbox", {
        name: "Sound · ambience and discovery cues",
      }),
    );
    const cue = view.container.querySelector("audio");
    if (expected) expect(cue).toHaveAttribute("src", expected);
    else expect(cue).toBeNull();
  },
);

it("exposes recoverable playback denial and stops ambience on exit", async () => {
  vi.spyOn(HTMLMediaElement.prototype, "play").mockRejectedValue(
    new Error("autoplay denied"),
  );
  const pause = vi
    .spyOn(HTMLMediaElement.prototype, "pause")
    .mockImplementation(() => {});
  const view = render(<AmbientAudio src="/media/manor-ambience-v1.wav" />);
  expect(await screen.findByText(/Sound could not start/)).toBeVisible();
  expect(screen.getByLabelText("Manor ambience")).toHaveAttribute("controls");
  view.unmount();
  expect(pause).toHaveBeenCalledOnce();
});

it("does not replay historical progress and stops opted-in cues on exit", async () => {
  const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
  const pause = vi
    .spyOn(HTMLMediaElement.prototype, "pause")
    .mockImplementation(() => {});
  const view = render(<DiscoverySound earned={4} src="media/test-cue.wav" />);
  expect(play).not.toHaveBeenCalled();
  view.rerender(<DiscoverySound earned={5} src="media/test-cue.wav" />);
  await waitFor(() => expect(play).toHaveBeenCalledOnce());
  view.rerender(<DiscoverySound earned={0} src="media/test-cue.wav" />);
  expect(play).toHaveBeenCalledOnce();
  view.unmount();
  expect(pause).toHaveBeenCalledOnce();
});
