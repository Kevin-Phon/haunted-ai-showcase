/* Generated from frozen public API 1.0.0. Run node scripts/generate-types.mjs. */

/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "AI".
 */
export type AI = {
  [k: string]: unknown;
} & {
  source: "live" | "demo" | "fallback" | "not_used";
  reason:
    ("timeout" | "unavailable" | "invalid_output" | "provider_error") | null;
  provider: "ollama" | null;
  model: string | null;
};
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Asset".
 */
export type Asset = {
  [k: string]: unknown;
} & {
  id: string;
  kind: "image" | "audio" | "font";
  src: string;
  alt: string;
  attribution_id: string;
  width: number | null;
  height: number | null;
};
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Puzzle".
 */
export type Puzzle =
  | {
      id: "letter_reconstruction";
      status: "available" | "solved";
      presentation: LetterPresentation;
    }
  | {
      id: "machine_calibration";
      status: "available" | "solved";
      presentation: CalibrationPresentation;
    };
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Action".
 */
export type Action =
  | {
      type: "navigate";
      room_id: string;
    }
  | {
      type: "inspect";
      hotspot_id: string;
    }
  | {
      type: "interact_object";
      object_id: string;
      operation: "open" | "close" | "activate";
    }
  | {
      type: "submit_puzzle";
      puzzle_id: "letter_reconstruction";
      solution: {
        /**
         * @minItems 4
         * @maxItems 4
         */
        placements: [
          {
            slot_id: string;
            piece_id: string;
          },
          {
            slot_id: string;
            piece_id: string;
          },
          {
            slot_id: string;
            piece_id: string;
          },
          {
            slot_id: string;
            piece_id: string;
          },
        ];
      };
    }
  | {
      type: "submit_puzzle";
      puzzle_id: "machine_calibration";
      solution: {
        power_level: number;
        phase: "amber" | "violet" | "cyan";
        stabilizer: "bypass" | "engaged";
      };
    }
  | {
      type: "connect_evidence";
      /**
       * @minItems 2
       * @maxItems 2
       */
      evidence_ids: [string, string];
    }
  | {
      type: "talk";
      ghost_id: "eleanor" | "thomas" | "clara";
      message: string;
      tone: "neutral" | "respectful" | "accusatory";
      /**
       * @maxItems 3
       */
      presented_evidence_ids:
        [] | [string] | [string, string] | [string, string, string];
    }
  | {
      type: "accuse";
      /**
       * @minItems 1
       * @maxItems 5
       */
      claims:
        | [Claim]
        | [Claim, Claim]
        | [Claim, Claim, Claim]
        | [Claim, Claim, Claim, Claim]
        | [Claim, Claim, Claim, Claim, Claim];
    };

export interface HauntedAIAPI100 {
  AI: AI;
  Event: Event;
  Asset: Asset;
  Bounds: Bounds;
  Layer: Layer;
  Interaction: Interaction;
  Hotspot: Hotspot;
  Scene: Scene;
  Room: Room;
  Evidence: Evidence;
  Insight: Insight;
  LetterPresentation: LetterPresentation;
  CalibrationPresentation: CalibrationPresentation;
  Puzzle: Puzzle;
  Ghost: Ghost;
  Turn: Turn;
  Claim: Claim;
  ClaimOption: ClaimOption;
  Ending: Ending;
  Descriptor: Descriptor;
  State: State;
  Action: Action;
  CreateRequest: CreateRequest;
  ActionRequest: ActionRequest;
  RestartRequest: RestartRequest;
  SessionResponse: SessionResponse;
  ActionResponse: ActionResponse;
  Error: Error;
  Health: Health;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Event".
 */
export interface Event {
  id: string;
  sequence: number;
  cue_id: string;
  summary: string;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Bounds".
 */
export interface Bounds {
  x: number;
  y: number;
  width: number;
  height: number;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Layer".
 */
export interface Layer {
  id: string;
  asset_id: string;
  z_index: number;
  parallax_factor: number;
  decorative: boolean;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Interaction".
 */
export interface Interaction {
  operation: "open" | "close" | "activate";
  label: string;
  enabled: boolean;
  disabled_reason: string | null;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Hotspot".
 */
export interface Hotspot {
  id: string;
  object_id: string;
  label: string;
  focus_order: number;
  bounds: Bounds;
  interactions: Interaction[];
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Scene".
 */
export interface Scene {
  room_id: string;
  title: string;
  description: string;
  layers: Layer[];
  hotspots: Hotspot[];
  objects: {
    id: string;
    state: "closed" | "open" | "inactive" | "active" | "calibrated";
    description: string;
  }[];
  ambient_audio_asset_id: string | null;
  canvas: {
    width: 1600;
    height: 900;
  };
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Room".
 */
export interface Room {
  id: string;
  title: string;
  unlocked: boolean;
  hint: string | null;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Evidence".
 */
export interface Evidence {
  id: string;
  title: string;
  description: string;
  room_id: string;
  asset_id: string | null;
  annotations: string[];
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Insight".
 */
export interface Insight {
  id: string;
  title: string;
  description: string;
  /**
   * @minItems 2
   * @maxItems 2
   */
  evidence_ids: [string, string];
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "LetterPresentation".
 */
export interface LetterPresentation {
  /**
   * @minItems 4
   * @maxItems 4
   */
  pieces: [
    {
      id: string;
      text: string;
      asset_id: string | null;
    },
    {
      id: string;
      text: string;
      asset_id: string | null;
    },
    {
      id: string;
      text: string;
      asset_id: string | null;
    },
    {
      id: string;
      text: string;
      asset_id: string | null;
    },
  ];
  /**
   * @minItems 4
   * @maxItems 4
   */
  slots: [
    {
      id: string;
      label: string;
    },
    {
      id: string;
      label: string;
    },
    {
      id: string;
      label: string;
    },
    {
      id: string;
      label: string;
    },
  ];
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "CalibrationPresentation".
 */
export interface CalibrationPresentation {
  /**
   * @minItems 3
   * @maxItems 3
   */
  controls: {
    [k: string]: unknown;
  } & [
    (
      | {
          id: "power_level";
          kind: "integer";
          label: string;
          minimum: 0;
          maximum: 3;
          step: 1;
        }
      | {
          id: "phase";
          kind: "choice";
          label: string;
          /**
           * @minItems 3
           * @maxItems 3
           */
          options: {
            [k: string]: unknown;
          } & {
            [k: string]: unknown;
          } & {
            [k: string]: unknown;
          } & [
              {
                value: "amber" | "violet" | "cyan";
                label: string;
              },
              {
                value: "amber" | "violet" | "cyan";
                label: string;
              },
              {
                value: "amber" | "violet" | "cyan";
                label: string;
              },
            ];
        }
      | {
          id: "stabilizer";
          kind: "choice";
          label: string;
          /**
           * @minItems 2
           * @maxItems 2
           */
          options: {
            [k: string]: unknown;
          } & {
            [k: string]: unknown;
          } & [
              {
                value: "bypass" | "engaged";
                label: string;
              },
              {
                value: "bypass" | "engaged";
                label: string;
              },
            ];
        }
    ),
    (
      | {
          id: "power_level";
          kind: "integer";
          label: string;
          minimum: 0;
          maximum: 3;
          step: 1;
        }
      | {
          id: "phase";
          kind: "choice";
          label: string;
          /**
           * @minItems 3
           * @maxItems 3
           */
          options: {
            [k: string]: unknown;
          } & {
            [k: string]: unknown;
          } & {
            [k: string]: unknown;
          } & [
              {
                value: "amber" | "violet" | "cyan";
                label: string;
              },
              {
                value: "amber" | "violet" | "cyan";
                label: string;
              },
              {
                value: "amber" | "violet" | "cyan";
                label: string;
              },
            ];
        }
      | {
          id: "stabilizer";
          kind: "choice";
          label: string;
          /**
           * @minItems 2
           * @maxItems 2
           */
          options: {
            [k: string]: unknown;
          } & {
            [k: string]: unknown;
          } & [
              {
                value: "bypass" | "engaged";
                label: string;
              },
              {
                value: "bypass" | "engaged";
                label: string;
              },
            ];
        }
    ),
    (
      | {
          id: "power_level";
          kind: "integer";
          label: string;
          minimum: 0;
          maximum: 3;
          step: 1;
        }
      | {
          id: "phase";
          kind: "choice";
          label: string;
          /**
           * @minItems 3
           * @maxItems 3
           */
          options: {
            [k: string]: unknown;
          } & {
            [k: string]: unknown;
          } & {
            [k: string]: unknown;
          } & [
              {
                value: "amber" | "violet" | "cyan";
                label: string;
              },
              {
                value: "amber" | "violet" | "cyan";
                label: string;
              },
              {
                value: "amber" | "violet" | "cyan";
                label: string;
              },
            ];
        }
      | {
          id: "stabilizer";
          kind: "choice";
          label: string;
          /**
           * @minItems 2
           * @maxItems 2
           */
          options: {
            [k: string]: unknown;
          } & {
            [k: string]: unknown;
          } & [
              {
                value: "bypass" | "engaged";
                label: string;
              },
              {
                value: "bypass" | "engaged";
                label: string;
              },
            ];
        }
    ),
  ];
  instructions: string;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Ghost".
 */
export interface Ghost {
  id: "eleanor" | "thomas" | "clara";
  display_name: string;
  available: boolean;
  trust: number;
  suspicion: number;
  emotion: "guarded" | "nervous" | "receptive" | "distressed" | "calm";
  portrait_asset_id: string | null;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Turn".
 */
export interface Turn {
  id: string;
  ghost_id: "eleanor" | "thomas" | "clara";
  player_message: string;
  response_text: string;
  ai: AI;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Claim".
 */
export interface Claim {
  claim_id: string;
  evidence_ids: string[];
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "ClaimOption".
 */
export interface ClaimOption {
  id: string;
  group:
    | "eleanor_action"
    | "eleanor_motive"
    | "thomas_action"
    | "thomas_motive"
    | "cause";
  label: string;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Ending".
 */
export interface Ending {
  id: "truth_revealed" | "partial_truth" | "false_accusation";
  title: string;
  explanation: string;
  supported_claim_ids: string[];
  missing_summary: string;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Descriptor".
 */
export interface Descriptor {
  type:
    | "navigate"
    | "inspect"
    | "interact_object"
    | "submit_puzzle"
    | "connect_evidence"
    | "talk"
    | "accuse";
  target_id: string | null;
  label: string;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "State".
 */
export interface State {
  contract_version: "1.0.0";
  content_version: string;
  session_id: string;
  revision: number;
  mode: "live" | "demo";
  phase: "investigating" | "ended";
  current_room_id: string;
  rooms: Room[];
  scene: Scene;
  assets: Asset[];
  evidence: Evidence[];
  insights: Insight[];
  puzzles: Puzzle[];
  ghosts: Ghost[];
  dialogue: Turn[];
  available_actions: Descriptor[];
  events: Event[];
  progress: {
    earned: number;
    total: number;
    label: string;
  };
  accusation: {
    eligible: boolean;
    hint: string | null;
    options: ClaimOption[];
  };
  ending: Ending | null;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "CreateRequest".
 */
export interface CreateRequest {
  request_id: string;
  content_id: "blackthorn_manor";
  mode: "live" | "demo";
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "ActionRequest".
 */
export interface ActionRequest {
  request_id: string;
  expected_revision: number;
  action: Action;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "RestartRequest".
 */
export interface RestartRequest {
  request_id: string;
  expected_revision: number;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "SessionResponse".
 */
export interface SessionResponse {
  request_id: string | null;
  state: State;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "ActionResponse".
 */
export interface ActionResponse {
  request_id: string;
  accepted: true;
  outcome: "applied" | "no_change" | "incorrect";
  state: State;
  feedback: {
    code: string;
    message: string;
  };
  new_events: Event[];
  dialogue_turn: Turn | null;
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Error".
 */
export interface Error {
  contract_version: "1.0.0";
  error: {
    code:
      | "INVALID_ACTION"
      | "SESSION_NOT_FOUND"
      | "ACTION_NOT_ALLOWED"
      | "REVISION_CONFLICT"
      | "IDEMPOTENCY_CONFLICT"
      | "SESSION_ENDED"
      | "SESSION_ACTION_LIMIT"
      | "REQUEST_TOO_LARGE"
      | "VALIDATION_ERROR"
      | "CONTENT_UNAVAILABLE"
      | "INTERNAL_ERROR";
    message: string;
    request_id: string | null;
    current_revision: number | null;
    retryable: boolean;
  };
}
/**
 * This interface was referenced by `HauntedAIAPI100`'s JSON-Schema
 * via the `definition` "Health".
 */
export interface Health {
  contract_version: "1.0.0";
  status: "ready" | "not_ready";
  content_version: string | null;
  ai: {
    provider: "ollama";
    model: string | null;
    status: "unknown" | "available" | "unavailable";
  };
}
