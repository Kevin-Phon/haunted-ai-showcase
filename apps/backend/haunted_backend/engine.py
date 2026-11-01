"""Deterministic session engine. All changes commit together after validation/generation."""

import asyncio
import copy
import json
from collections import deque
from dataclasses import dataclass, field
from uuid import uuid4

from .ai import DialogueAdapter, clean_text
from .errors import GameError
from .schemas import validate


def require(condition, code="ACTION_NOT_ALLOWED", status=409):
    if not condition:
        raise GameError(code, status)


def canonical(route, body):
    return json.dumps([route, body], sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass
class Session:
    state: dict
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    cache: dict = field(default_factory=dict)
    mutations: int = 0


class Engine:
    def __init__(self, content, adapter=None):
        self.content, self.adapter = content, adapter or DialogueAdapter()
        self.sessions, self.creations = {}, {}
        self.creation_lock = asyncio.Lock()

    def initial(self, id, mode, revision=0, run=1):
        c = self.content
        return {
            "id": id,
            "mode": mode,
            "revision": revision,
            "run": run,
            "room": c.data["initial_room_id"],
            "evidence": set(),
            "insights": set(),
            "solved": set(),
            "enabled": set(),
            "unlocked": {id for id, r in c.rooms.items() if r["initially_unlocked"]},
            "visible": {id for id, o in c.objects.items() if o["initially_visible"]},
            "objects": {id: o["initial_state"] for id, o in c.objects.items()},
            "relationships": {
                id: {
                    "trust": g["initial_trust"],
                    "suspicion": g["initial_suspicion"],
                    "emotion": "guarded",
                }
                for id, g in c.ghosts.items()
            },
            "respectful": set(),
            "presentations": set(),
            "fired": set(),
            "emitted": set(),
            "events": [],
            "history": {id: [] for id in c.ghosts},
            "ending": None,
        }

    def satisfied(self, s, p):
        return (
            set(p["all_evidence"]) <= s["evidence"]
            and set(p["all_insights"]) <= s["insights"]
            and set(p["all_puzzles"]) <= s["solved"]
            and all(s["objects"][o["object_id"]] == o["state"] for o in p["object_states"])
        )

    def rules_for(self, kind, target, operation=None):
        return sorted(
            (
                r
                for r in self.content.rules.values()
                if r["trigger"] == {"type": kind, "target_id": target, "operation": operation}
            ),
            key=lambda x: x["id"],
        )

    def permitted_operation(self, s, obj, operation):
        if obj["id"] not in s["visible"] or obj["room_id"] != s["room"]:
            return False
        declared = any(
            x["operation"] == operation and x["enabled"] for x in obj["hotspot"]["interactions"]
        )
        rules = self.rules_for("interact_object", obj["id"], operation)
        return declared and any(self.satisfied(s, r["requires"]) for r in rules)

    def puzzle_available(self, s, p):
        return self.satisfied(s, p["requires"]) and (
            p["id"] not in self.content.gated_puzzles or p["id"] in s["enabled"]
        )

    def projection(self, s):
        c = self.content
        room = c.rooms[s["room"]]
        objects = [
            o for id, o in c.objects.items() if id in s["visible"] and o["room_id"] == s["room"]
        ]
        hotspots = []
        for o in objects:
            h = copy.deepcopy(o["hotspot"])
            for interaction in h["interactions"]:
                enabled = self.permitted_operation(s, o, interaction["operation"])
                interaction.update(
                    enabled=enabled, disabled_reason=None if enabled else "Continue investigating."
                )
            hotspots.append(h)
        puzzles = [
            {
                "id": id,
                "status": "solved" if id in s["solved"] else "available",
                "presentation": copy.deepcopy(p["presentation"]),
            }
            for id, p in c.puzzles.items()
            if id in s["solved"] or (p["room_id"] == s["room"] and self.puzzle_available(s, p))
        ]
        evidence = [
            {
                k: copy.deepcopy(e[k])
                for k in ("id", "title", "description", "room_id", "asset_id", "annotations")
            }
            for id, e in c.evidence.items()
            if id in s["evidence"]
        ]
        insights = [
            {k: copy.deepcopy(d[k]) for k in ("id", "title", "description", "evidence_ids")}
            for id, d in c.deductions.items()
            if id in s["insights"]
        ]
        ghosts = [
            dict(
                id=id,
                display_name=g["name"],
                available=g["room_id"] == s["room"],
                **s["relationships"][id],
                portrait_asset_id=g["portrait_asset_id"],
            )
            for id, g in c.ghosts.items()
        ]
        scene = {
            "room_id": room["id"],
            "title": room["title"],
            "description": room["description"],
            "layers": copy.deepcopy(room["layers"]),
            "hotspots": hotspots,
            "objects": [
                {"id": o["id"], "state": s["objects"][o["id"]], "description": o["description"]}
                for o in objects
            ],
            "ambient_audio_asset_id": room["ambient_audio_asset_id"],
            "canvas": {"width": 1600, "height": 900},
        }
        asset_ids = {x["asset_id"] for x in scene["layers"]}
        # Optional global presentation cue; never broaden this to all unreferenced assets.
        discovery_sound = c.assets.get("audio_discovery")
        if discovery_sound is not None and discovery_sound["kind"] == "audio":
            asset_ids.add("audio_discovery")
        asset_ids.add(scene["ambient_audio_asset_id"])
        asset_ids.update(x["asset_id"] for x in evidence)
        asset_ids.update(x["portrait_asset_id"] for x in ghosts)
        for p in puzzles:
            if p["id"] == "letter_reconstruction":
                asset_ids.update(x["asset_id"] for x in p["presentation"]["pieces"])
        descriptors = []

        def descriptor(type, target, label):
            descriptors.append({"type": type, "target_id": target, "label": label})

        for id in room["adjacent_room_ids"]:
            if id in s["unlocked"]:
                descriptor("navigate", id, "Enter " + c.rooms[id]["title"])
        for h in hotspots:
            descriptor("inspect", h["id"], "Inspect " + h["label"])
            if any(x["enabled"] for x in h["interactions"]):
                descriptor("interact_object", h["object_id"], h["label"])
        for p in puzzles:
            if p["status"] != "solved":
                descriptor("submit_puzzle", p["id"], "Solve puzzle")
        for g in ghosts:
            if g["available"]:
                descriptor("talk", g["id"], "Question " + g["display_name"])
        if len(evidence) >= 2:
            descriptor("connect_evidence", None, "Connect clues")
        if evidence:
            descriptor("accuse", None, "Submit theory")
        earned = len(evidence) + len(insights) + len(s["solved"])
        state = {
            "contract_version": "1.0.0",
            "content_version": c.data["content_version"],
            "session_id": s["id"],
            "revision": s["revision"],
            "mode": s["mode"],
            "phase": "ended" if s["ending"] else "investigating",
            "current_room_id": s["room"],
            "rooms": [
                {
                    "id": id,
                    "title": r["title"],
                    "unlocked": id in s["unlocked"],
                    "hint": None if id in s["unlocked"] else "Continue investigating.",
                }
                for id, r in c.rooms.items()
            ],
            "scene": scene,
            "assets": [copy.deepcopy(a) for id, a in c.assets.items() if id in asset_ids],
            "evidence": evidence,
            "insights": insights,
            "puzzles": puzzles,
            "ghosts": ghosts,
            "dialogue": [copy.deepcopy(t) for turns in s["history"].values() for t in turns],
            "available_actions": [] if s["ending"] else descriptors,
            "events": copy.deepcopy(s["events"]),
            "progress": {"earned": earned, "total": 14, "label": "Investigation progress"},
            "accusation": {
                "eligible": bool(evidence) and not bool(s["ending"]),
                "hint": None if evidence else "Discover evidence before submitting a theory.",
                "options": [{k: x[k] for k in ("id", "group", "label")} for x in c.claims.values()]
                if evidence
                else [],
            },
            "ending": copy.deepcopy(s["ending"]),
        }
        validate("State", state)
        return state

    async def create(self, body):
        async with self.creation_lock:
            key, fingerprint = body["request_id"], canonical("create", body)
            if key in self.creations:
                previous, result = self.creations[key]
                require(previous == fingerprint, "IDEMPOTENCY_CONFLICT")
                return copy.deepcopy(result)
            if len(self.sessions) >= 8:
                raise GameError(
                    "CONTENT_UNAVAILABLE",
                    503,
                    "Process session capacity reached. Restart the backend to begin a new investigation.",
                )
            id = str(uuid4())
            s = self.initial(id, body["mode"])
            response = {"request_id": key, "state": self.projection(s)}
            self.sessions[id] = Session(s)
            self.creations[key] = (fingerprint, copy.deepcopy(response))
            return response

    def session(self, id):
        if id not in self.sessions:
            raise GameError(
                "SESSION_NOT_FOUND", 404, "Investigation no longer exists. Start a new session."
            )
        return self.sessions[id]

    async def get(self, id):
        session = self.session(id)
        async with session.lock:
            return {"request_id": None, "state": self.projection(session.state)}

    async def mutate(self, id, body, restart=False):
        session = self.session(id)
        async with session.lock:
            s = session.state
            key = body["request_id"]
            fp = canonical("restart" if restart else "action", body)
            try:
                if key in session.cache:
                    previous, result = session.cache[key]
                    require(previous == fp, "IDEMPOTENCY_CONFLICT")
                    return copy.deepcopy(result)
                require(body["expected_revision"] == s["revision"], "REVISION_CONFLICT")
                require(session.mutations < 500, "SESSION_ACTION_LIMIT")
                if restart:
                    candidate = self.initial(id, s["mode"], s["revision"] + 1, s["run"] + 1)
                    result = {"request_id": key, "state": self.projection(candidate)}
                else:
                    require(s["ending"] is None, "SESSION_ENDED")
                    candidate = copy.deepcopy(s)
                    count = len(candidate["events"])
                    outcome, turn = await self.apply(candidate, body["action"])
                    candidate["revision"] += 1
                    result = {
                        "request_id": key,
                        "accepted": True,
                        "outcome": outcome,
                        "state": self.projection(candidate),
                        "feedback": {
                            "code": outcome,
                            "message": {
                                "applied": "Investigation updated.",
                                "no_change": "Already recorded.",
                                "incorrect": "That combination does not resolve it.",
                            }[outcome],
                        },
                        "new_events": copy.deepcopy(candidate["events"][count:]),
                        "dialogue_turn": turn,
                    }
                validate("SessionResponse" if restart else "ActionResponse", result)
                session.state = candidate
                session.mutations += 1
                session.cache[key] = (fp, copy.deepcopy(result))
                return result
            except GameError as exc:
                exc.revision = s["revision"]
                if exc.code == "SESSION_ACTION_LIMIT":
                    exc.message = "Investigation capacity reached. Explicitly create a new session, or restart the backend if all session slots are occupied."
                raise

    async def apply(self, s, a):
        if a["type"] == "talk":
            return "applied", await self.talk(s, a)
        return self.transition(s, a)

    def transition(self, s, a):
        c = self.content
        kind = a["type"]
        queue = deque()
        turn = None
        before = copy.deepcopy(s)
        if kind == "navigate":
            id = a["room_id"]
            require(id in c.rooms, "INVALID_ACTION", 400)
            require(id in s["unlocked"] and id in c.rooms[s["room"]]["adjacent_room_ids"])
            s["room"] = id
        elif kind == "inspect":
            id = a["hotspot_id"]
            require(id in c.hotspots, "INVALID_ACTION", 400)
            o = c.hotspots[id]
            require(o["room_id"] == s["room"] and o["id"] in s["visible"])
            queue.append(("inspect", id, None))
        elif kind == "interact_object":
            id = a["object_id"]
            require(id in c.objects, "INVALID_ACTION", 400)
            require(self.permitted_operation(s, c.objects[id], a["operation"]))
            queue.append(("interact_object", id, a["operation"]))
        elif kind == "submit_puzzle":
            id = a["puzzle_id"]
            p = c.puzzles[id]
            require(p["room_id"] == s["room"] and self.puzzle_available(s, p))
            if id in s["solved"]:
                return "no_change", None
            if id == "letter_reconstruction":
                placements = a["solution"]["placements"]
                require(
                    len({x["piece_id"] for x in placements}) == 4
                    and len({x["slot_id"] for x in placements}) == 4,
                    "VALIDATION_ERROR",
                    422,
                )
                require(
                    {x["piece_id"] for x in placements}
                    == {x["id"] for x in p["presentation"]["pieces"]}
                    and {x["slot_id"] for x in placements}
                    == {x["id"] for x in p["presentation"]["slots"]},
                    "VALIDATION_ERROR",
                    422,
                )
                correct = {x["slot_id"]: x["piece_id"] for x in placements} == {
                    x["slot_id"]: x["piece_id"] for x in p["solution"]["placements"]
                }
            else:
                correct = a["solution"] == p["solution"]
            if not correct:
                return "incorrect", None
            s["solved"].add(id)
            self.effects(s, p["effects"], queue)
            queue.append(("puzzle_solved", id, None))
        elif kind == "connect_evidence":
            pair = set(a["evidence_ids"])
            require(pair <= set(c.evidence), "INVALID_ACTION", 400)
            require(pair <= s["evidence"])
            d = next((d for d in c.deductions.values() if set(d["evidence_ids"]) == pair), None)
            if d is None:
                return "incorrect", None
            require(self.satisfied(s, d["requires"]))
            if d["id"] in s["insights"]:
                return "no_change", None
            s["insights"].add(d["id"])
            self.effects(s, d["effects"], queue)
            queue.append(("insight_earned", d["id"], None))
        elif kind == "accuse":
            self.accuse(s, a["claims"])
        fired = set()
        while queue:
            trigger = queue.popleft()
            for r in self.rules_for(*trigger):
                id = r["id"]
                if (
                    id in fired
                    or (r["once"] and id in s["fired"])
                    or not self.satisfied(s, r["requires"])
                ):
                    continue
                fired.add(id)
                if r["once"]:
                    s["fired"].add(id)
                self.effects(s, r["effects"], queue)
        return ("no_change" if s == before else "applied"), turn

    def effects(self, s, effects, queue):
        for e in effects:
            k, id = e["kind"], e["target_id"]
            if k == "grant_evidence":
                s["evidence"].add(id)
            elif k == "grant_insight":
                if id not in s["insights"]:
                    s["insights"].add(id)
                    queue.append(("insight_earned", id, None))
            elif k == "unlock_room":
                s["unlocked"].add(id)
            elif k == "reveal_object":
                s["visible"].add(id)
            elif k == "set_object_state":
                s["objects"][id] = e["state"]
            elif k == "enable_puzzle":
                s["enabled"].add(id)
            elif k == "emit_event" and id not in s["emitted"]:
                s["emitted"].add(id)
                event = self.content.events[id]
                s["events"].append(
                    {
                        "id": f"{s['id']}_run_{s['run']}_{id}",
                        "sequence": len(s["events"]) + 1,
                        "cue_id": event["cue_id"],
                        "summary": event["summary"],
                    }
                )

    async def talk(self, s, a):
        c = self.content
        id = a["ghost_id"]
        ghost = c.ghosts[id]
        require(ghost["room_id"] == s["room"])
        message = a["message"].strip()
        require(bool(message) and clean_text(message), "VALIDATION_ERROR", 422)
        presented = set(a["presented_evidence_ids"])
        require(presented <= set(c.evidence), "INVALID_ACTION", 400)
        require(presented <= s["evidence"])
        meters = s["relationships"][id]
        if a["tone"] == "respectful" and id not in s["respectful"]:
            meters["trust"] += 5
            s["respectful"].add(id)
        if a["tone"] == "accusatory":
            meters["suspicion"] += 10
        for e in presented & set(ghost["relevant_evidence_ids"]):
            if (id, e) not in s["presentations"]:
                meters["trust"] += 10
                meters["suspicion"] -= 5
                s["presentations"].add((id, e))
        meters["trust"] = max(0, min(100, meters["trust"]))
        meters["suspicion"] = max(0, min(100, meters["suspicion"]))
        meters["emotion"] = (
            "distressed"
            if meters["suspicion"] > 60
            else "receptive"
            if meters["trust"] >= 50
            else "nervous"
            if id == "thomas"
            else "guarded"
        )
        permitted = [
            k
            for k in c.knowledge.values()
            if k["ghost_id"] == id
            and self.satisfied(s, k["requires"])
            and (k["minimum_trust"] is None or meters["trust"] >= k["minimum_trust"])
            and (k["maximum_suspicion"] is None or meters["suspicion"] <= k["maximum_suspicion"])
        ]
        superseded = {key for k in permitted for key in k["supersedes_ids"]}
        permitted = [k for k in permitted if k["id"] not in superseded]
        # Relevant facts first; cap context even for large future content packages.
        words = set(message.lower().split())
        permitted.sort(key=lambda k: (-len(words & set(k["text"].lower().split())), k["id"]))
        facts = []
        size = 0
        for k in permitted:
            if len(facts) < 12 and size + len(k["text"]) + len(k["fallback_text"]) <= 8000:
                facts.append({key: k[key] for key in ("id", "text", "fallback_text")})
                size += len(k["text"]) + len(k["fallback_text"])
        context = {
            "personality": ghost["personality"],
            "emotion": meters["emotion"],
            "message": message,
            "facts": facts,
            "fallback": ghost["generic_fallback"],
            "history": [
                {"player": t["player_message"], "response": t["response_text"]}
                for t in s["history"][id][-12:]
            ],
        }
        text, ai = await self.adapter.respond(context, s["mode"])
        turn = {
            "id": str(uuid4()),
            "ghost_id": id,
            "player_message": message,
            "response_text": text,
            "ai": ai,
        }
        s["history"][id].append(turn)
        s["history"][id] = s["history"][id][-12:]
        return turn

    def accuse(self, s, claims):
        c = self.content
        require(bool(s["evidence"]))
        groups = set()
        supported = []
        for item in claims:
            id = item["claim_id"]
            require(id in c.claims, "INVALID_ACTION", 400)
            claim = c.claims[id]
            require(claim["group"] not in groups, "VALIDATION_ERROR", 422)
            groups.add(claim["group"])
            evidence = set(item["evidence_ids"])
            require(evidence <= set(c.evidence), "INVALID_ACTION", 400)
            require(evidence <= s["evidence"])
            if claim["correct"] and set(claim["support_evidence_ids"]) <= evidence:
                supported.append(id)
        complete = (
            len(supported) == 5
            and set(c.puzzles) <= s["solved"]
            and set(c.deductions) <= s["insights"]
        )
        id = "truth_revealed" if complete else "partial_truth" if supported else "false_accusation"
        rule = c.endings[id]
        s["ending"] = {
            "id": id,
            "title": rule["title"],
            "explanation": rule["explanation"],
            "supported_claim_ids": supported,
            "missing_summary": "All required reasoning is supported."
            if complete
            else "Some responsibility, motive or causal reasoning remains unsupported.",
        }
