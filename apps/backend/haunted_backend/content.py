"""Private content loader and semantic validation. No content file is served as an asset."""

import copy
import json
from pathlib import Path, PurePosixPath

from jsonschema import ValidationError

from .schemas import validate


class ContentError(ValueError):
    pass


class Content:
    def __init__(self, data):
        self.data = copy.deepcopy(data)
        try:
            validate("Content", self.data)
            self._index()
            self._references()
            self._reachable()
        except (ValidationError, KeyError, TypeError, ValueError) as exc:
            raise ContentError("Private content is invalid or unreachable.") from exc

    @classmethod
    def load(cls, path):
        try:
            return cls(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            raise ContentError("Private content is unavailable.") from exc

    def _index(self):
        for name in (
            "rooms",
            "objects",
            "evidence",
            "puzzles",
            "deductions",
            "ghosts",
            "knowledge",
            "rules",
            "claims",
            "endings",
            "timeline",
            "events",
            "assets",
            "attributions",
        ):
            records = self.data[name]
            mapping = {x["id"]: x for x in records}
            if len(mapping) != len(records):
                raise ContentError("Duplicate IDs.")
            setattr(self, name, mapping)
        self.gated_puzzles = {
            e["target_id"]
            for name in ("rules", "puzzles", "deductions")
            for r in getattr(self, name).values()
            for e in r["effects"]
            if e["kind"] == "enable_puzzle"
        }
        self.hotspots = {o["hotspot"]["id"]: o for o in self.objects.values()}
        if len(self.hotspots) != len(self.objects):
            raise ContentError("Duplicate hotspots.")
        required = {
            "rooms": {
                "entrance_hall",
                "library",
                "study",
                "laboratory",
                "grand_ballroom",
                "hidden_passage",
            },
            "ghosts": {"eleanor", "thomas", "clara"},
            "puzzles": {"letter_reconstruction", "machine_calibration"},
            "evidence": {
                "damaged_notebook",
                "torn_letter",
                "servant_log",
                "memory_crystal",
                "maintenance_record",
                "gathering_photograph",
                "sealed_report",
                "final_recording",
            },
            "deductions": {
                "deduction_hidden_route",
                "deduction_protective_sabotage",
                "deduction_partial_restart",
                "deduction_fatal_instability",
            },
            "endings": {"truth_revealed", "partial_truth", "false_accusation"},
        }
        for name, ids in required.items():
            if set(getattr(self, name)) != ids:
                raise ContentError("Unexpected canonical IDs.")
        self._ref(self.rooms, self.data["initial_room_id"])
        if (
            self.data["initial_room_id"] != "entrance_hall"
            or not self.rooms["entrance_hall"]["initially_unlocked"]
            or self.rooms["hidden_passage"]["initially_unlocked"]
        ):
            raise ContentError("Invalid initial rooms.")

    @staticmethod
    def _ref(mapping, value):
        if value not in mapping:
            raise ContentError("Unknown typed reference.")

    def _predicate(self, p):
        for key, mapping in (
            ("all_evidence", self.evidence),
            ("all_insights", self.deductions),
            ("all_puzzles", self.puzzles),
        ):
            for id in p[key]:
                self._ref(mapping, id)
        seen = set()
        for item in p["object_states"]:
            self._ref(self.objects, item["object_id"])
            if item["object_id"] in seen:
                raise ContentError("Conflicting object predicates.")
            seen.add(item["object_id"])

    def _effects(self, effects):
        for e in effects:
            mapping = {
                "grant_evidence": self.evidence,
                "grant_insight": self.deductions,
                "unlock_room": self.rooms,
                "reveal_object": self.objects,
                "set_object_state": self.objects,
                "emit_event": self.events,
                "enable_puzzle": self.puzzles,
            }[e["kind"]]
            self._ref(mapping, e["target_id"])
            if (e["kind"] == "set_object_state") != (e["state"] is not None):
                raise ContentError("Invalid effect state.")

    def _references(self):
        for a in self.assets.values():
            path = a["src"]
            if (
                not path
                or path.startswith("/")
                or any(c in path for c in ("\\", ":", "?", "#", "\x00"))
                or ".." in PurePosixPath(path).parts
            ):
                raise ContentError("Asset paths must be safe relative paths.")
            self._ref(self.attributions, a["attribution_id"])
        for room in self.rooms.values():
            for id in room["adjacent_room_ids"]:
                self._ref(self.rooms, id)
            layer_ids = set()
            for layer in room["layers"]:
                if layer["id"] in layer_ids:
                    raise ContentError("Duplicate layers.")
                layer_ids.add(layer["id"])
                self._ref(self.assets, layer["asset_id"])
                a = self.assets[layer["asset_id"]]
                if a["kind"] != "image" or a["width"] * 9 != a["height"] * 16:
                    raise ContentError("Incompatible room layer canvas.")
            if room["ambient_audio_asset_id"] is not None:
                self._ref(self.assets, room["ambient_audio_asset_id"])
                if self.assets[room["ambient_audio_asset_id"]]["kind"] != "audio":
                    raise ContentError("Invalid ambient asset.")
        for obj in self.objects.values():
            self._ref(self.rooms, obj["room_id"])
            h = obj["hotspot"]
            if h["object_id"] != obj["id"]:
                raise ContentError("Mismatched hotspot owner.")
            b = h["bounds"]
            if (
                b["width"] <= 0
                or b["height"] <= 0
                or b["x"] + b["width"] > 1
                or b["y"] + b["height"] > 1
            ):
                raise ContentError("Invalid hotspot rectangle.")
            ops = [x["operation"] for x in h["interactions"]]
            if len(set(ops)) != len(ops):
                raise ContentError("Duplicate operations.")
        for record in [*self.evidence.values(), *self.ghosts.values(), *self.puzzles.values()]:
            self._ref(self.rooms, record["room_id"])
            for field in ("asset_id", "portrait_asset_id"):
                if record.get(field) is not None:
                    self._ref(self.assets, record[field])
        for record in self.evidence.values():
            self._ref(self.attributions, record["attribution_id"])
        for g in self.ghosts.values():
            for id in g["relevant_evidence_ids"]:
                self._ref(self.evidence, id)
            if len(g["generic_fallback"]) > 1200:
                raise ContentError("Oversized fallback.")
        for p in self.puzzles.values():
            self._predicate(p["requires"])
            self._effects(p["effects"])
            if p["id"] == "letter_reconstruction":
                pieces = [x["id"] for x in p["presentation"]["pieces"]]
                slots = [x["id"] for x in p["presentation"]["slots"]]
                solution = p["solution"]["placements"]
                if (
                    len(set(pieces)) != 4
                    or len(set(slots)) != 4
                    or set(pieces) != {x["piece_id"] for x in solution}
                    or set(slots) != {x["slot_id"] for x in solution}
                ):
                    raise ContentError("Invalid letter membership.")
                for piece in p["presentation"]["pieces"]:
                    if piece["asset_id"] is not None:
                        self._ref(self.assets, piece["asset_id"])
        pairs = set()
        for d in self.deductions.values():
            pair = tuple(sorted(d["evidence_ids"]))
            if pair in pairs:
                raise ContentError("Ambiguous deduction pair.")
            pairs.add(pair)
            for id in pair:
                self._ref(self.evidence, id)
            self._predicate(d["requires"])
            self._effects(d["effects"])
        graph = {id: set() for id in self.deductions}
        for rule in self.rules.values():
            t = rule["trigger"]
            self._ref(
                {
                    "inspect": self.hotspots,
                    "interact_object": self.objects,
                    "puzzle_solved": self.puzzles,
                    "insight_earned": self.deductions,
                }[t["type"]],
                t["target_id"],
            )
            if (t["type"] == "interact_object") != (t["operation"] is not None):
                raise ContentError("Invalid typed trigger.")
            if t["type"] == "interact_object" and not any(
                x["operation"] == t["operation"] and x["enabled"]
                for x in self.objects[t["target_id"]]["hotspot"]["interactions"]
            ):
                raise ContentError("Rule operation is not declared/enabled on its object.")
            self._predicate(rule["requires"])
            self._effects(rule["effects"])
            if t["type"] == "insight_earned":
                graph[t["target_id"]].update(
                    e["target_id"] for e in rule["effects"] if e["kind"] == "grant_insight"
                )

        def visit(id, stack):
            if id in stack:
                raise ContentError("Cyclic insight effects.")
            for child in graph[id]:
                visit(child, stack | {id})

        for id in graph:
            visit(id, set())
        for k in self.knowledge.values():
            self._predicate(k["requires"])
            if len(k["fallback_text"]) > 1200:
                raise ContentError("Oversized fallback.")
            for id in k["supersedes_ids"]:
                self._ref(self.knowledge, id)
                if self.knowledge[id]["ghost_id"] != k["ghost_id"]:
                    raise ContentError("Cross-ghost supersession.")
            if k["critical"] and (
                k["minimum_trust"] is not None or k["maximum_suspicion"] is not None
            ):
                raise ContentError("Critical disclosure cannot depend on meters.")
        for name in ("claims", "timeline"):
            for record in getattr(self, name).values():
                for id in record["support_evidence_ids"]:
                    self._ref(self.evidence, id)
        correct = [c for c in self.claims.values() if c["correct"]]
        groups = {"eleanor_action", "eleanor_motive", "thomas_action", "thomas_motive", "cause"}
        if (
            {c["group"] for c in correct} != groups
            or len(correct) != 5
            or any(not c["support_evidence_ids"] for c in correct)
        ):
            raise ContentError("Five supported canonical claim groups required.")
        if any(
            not any(c["group"] == group and not c["correct"] for c in self.claims.values())
            for group in groups
        ):
            raise ContentError("Missing alternative hypotheses.")

    def _reachable(self):
        """Find an executable private proof, never credit historical semantic events.

        Best-first search uses the runtime transition kernel with no dialogue/model calls.
        The bound rejects content too complex to verify rather than accepting a guess.
        This validates a complete mechanical path; Data still reviews narrative logic.
        """
        import heapq
        from itertools import count

        from .engine import Engine
        from .errors import GameError

        engine = Engine(self)
        initial = engine.initial("validation", "demo")
        serial = count()
        frontier = []
        seen = set()

        def freeze(value):
            if isinstance(value, dict):
                return tuple((k, freeze(v)) for k, v in sorted(value.items()))
            if isinstance(value, set):
                return tuple(sorted(value))
            if isinstance(value, list):
                return tuple(freeze(v) for v in value)
            return value

        def add(state, visited, path):
            key = (freeze(state), tuple(sorted(visited)))
            if key in seen:
                return
            seen.add(key)
            score = (
                10 * (len(state["evidence"]) + len(state["insights"]) + len(state["solved"]))
                + 2 * len(visited)
                + len(state["visible"])
                + len(state["unlocked"])
                + len(state["enabled"])
            )
            heapq.heappush(frontier, (-score, next(serial), state, visited, path))

        add(initial, {initial["room"]}, [])
        expanded = 0
        while frontier and expanded < 2048:
            _, _, state, visited, path = heapq.heappop(frontier)
            expanded += 1
            if (
                set(self.evidence) <= state["evidence"]
                and set(self.deductions) <= state["insights"]
                and set(self.puzzles) <= state["solved"]
                and set(self.rooms) <= visited
            ):
                # Exercise the same evaluator to prove the fully supported ending is legal.
                claims = [
                    {"claim_id": c["id"], "evidence_ids": c["support_evidence_ids"]}
                    for c in self.claims.values()
                    if c["correct"]
                ]
                engine.accuse(state, claims)
                if state["ending"]["id"] != "truth_revealed":
                    raise ContentError("Canonical truth cannot be reached.")
                self.verification_path = path
                return
            actions = []
            for obj in self.objects.values():
                if obj["room_id"] != state["room"] or obj["id"] not in state["visible"]:
                    continue
                actions.append({"type": "inspect", "hotspot_id": obj["hotspot"]["id"]})
                for interaction in obj["hotspot"]["interactions"]:
                    if engine.permitted_operation(state, obj, interaction["operation"]):
                        actions.append(
                            {
                                "type": "interact_object",
                                "object_id": obj["id"],
                                "operation": interaction["operation"],
                            }
                        )
            for puzzle in self.puzzles.values():
                if (
                    puzzle["id"] not in state["solved"]
                    and puzzle["room_id"] == state["room"]
                    and engine.puzzle_available(state, puzzle)
                ):
                    actions.append(
                        {
                            "type": "submit_puzzle",
                            "puzzle_id": puzzle["id"],
                            "solution": puzzle["solution"],
                        }
                    )
            for d in self.deductions.values():
                if (
                    d["id"] not in state["insights"]
                    and set(d["evidence_ids"]) <= state["evidence"]
                    and engine.satisfied(state, d["requires"])
                ):
                    actions.append({"type": "connect_evidence", "evidence_ids": d["evidence_ids"]})
            for id in self.rooms[state["room"]]["adjacent_room_ids"]:
                if id in state["unlocked"]:
                    actions.append({"type": "navigate", "room_id": id})
            for action in actions:
                candidate = copy.deepcopy(state)
                try:
                    outcome, _ = engine.transition(candidate, action)
                except GameError:
                    continue
                if outcome != "no_change":
                    add(candidate, visited | {candidate["room"]}, path + [action])
        raise ContentError("No complete executable progression proof within 2048 states.")
