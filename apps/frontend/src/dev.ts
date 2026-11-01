// Imported only behind import.meta.env.DEV. These are public contract examples, never rules.
import type { ActionResponse, SessionResponse } from "./generated/contract";
import type { Transport } from "./api";
import { ApiError } from "./api";
const fixtures = import.meta.glob(
  "../../../contracts/v1/examples/*.response.json",
  { import: "default" },
);
export const scenarios = Object.keys(fixtures)
  .filter((p) => !p.endsWith("/health.response.json"))
  .map((p) => p.split("/").at(-1)!.replace(".response.json", ""))
  .sort();
let chosen = "session";
export function selectScenario(name: string) {
  chosen = name;
}
async function read(): Promise<SessionResponse | ActionResponse> {
  const key = Object.keys(fixtures).find((p) =>
    p.endsWith("/" + chosen + ".response.json"),
  );
  if (!key) throw new Error("Unknown public fixture");
  const value = (await fixtures[key]()) as SessionResponse & {
    error?: {
      code: string;
      message: string;
      current_revision: number | null;
      retryable: boolean;
    };
  };
  if (value.error)
    throw new ApiError(
      value.error.code,
      "DEVELOPMENT fixture: " + value.error.message,
      value.error.current_revision,
      value.error.retryable,
    );
  return structuredClone(value);
}
export const transport: Transport = {
  create: async () => read(),
  get: async () => read(),
  restart: async () => read(),
  action: async () => {
    const result = await read();
    if (!("accepted" in result))
      throw new ApiError(
        "MOCK_SCENARIO",
        "Choose an action response scenario. This fixture viewer does not simulate gameplay rules.",
      );
    return result;
  },
};
