"""Validate PRIVATE Blackthorn content and construct a concrete no-AI play witness.

The traversal is a content verification oracle, not the authoritative game server.
It executes typed actions and FIFO rules with real object/prerequisite state.
No network, inference, trust gain, or frontend import is needed.
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "contracts" / "v1"
ROOMS = {"entrance_hall", "library", "study", "laboratory", "grand_ballroom", "hidden_passage"}
EVIDENCE = {"damaged_notebook", "torn_letter", "servant_log", "memory_crystal", "maintenance_record", "gathering_photograph", "sealed_report", "final_recording"}
INSIGHTS = {"deduction_hidden_route", "deduction_protective_sabotage", "deduction_partial_restart", "deduction_fatal_instability"}
PUZZLES = {"letter_reconstruction", "machine_calibration"}
SUPPORT = {
    "eleanor_disconnected_stabilizer": {"torn_letter", "maintenance_record"},
    "eleanor_protected_clara": {"torn_letter", "sealed_report"},
    "thomas_restored_power": {"servant_log", "maintenance_record"},
    "thomas_protected_reputation": {"maintenance_record"},
    "unstable_run_killed_elias": {"damaged_notebook", "final_recording"},
}


class ContentError(ValueError):
    """Invalid schema, reference, narrative gate or verification action."""


def require(ok, message):
    if not ok:
        raise ContentError(message)


def indexed(rows, label):
    result = {x["id"]: x for x in rows}
    require(len(result) == len(rows), f"duplicate {label} IDs")
    return result


def validate(data, *, schema=True, reachability=True):
    """Fail closed; schema dependency is explicit and never silently skipped."""
    if schema:
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource
        schemas = [json.loads((CONTRACT / name).read_text()) for name in ("api.schema.json", "game-data.schema.json")]
        registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
        errors = list(Draft202012Validator(schemas[1], registry=registry, format_checker=FormatChecker()).iter_errors(data))
        require(not errors, "schema: " + "; ".join(e.message for e in errors[:5]))
    tables = {key: indexed(data[key], key) for key in ("rooms", "objects", "evidence", "puzzles", "deductions", "ghosts", "knowledge", "rules", "claims", "endings", "timeline", "events", "assets", "attributions")}
    for key, expected in [("rooms", ROOMS), ("evidence", EVIDENCE), ("puzzles", PUZZLES), ("deductions", INSIGHTS), ("ghosts", {"eleanor", "thomas", "clara"}), ("endings", {"truth_revealed", "partial_truth", "false_accusation"})]:
        require(set(tables[key]) == expected, f"canonical {key} inventory mismatch")
    hotspots = indexed([o["hotspot"] for o in data["objects"]], "hotspot")
    def ref(kind, value):
        require(value in tables[kind], f"unknown {kind} reference: {value}")
    def refs(kind, values):
        for value in values: ref(kind, value)
    attainable_states = {o["id"]: {o["initial_state"]} for o in data["objects"]}
    for source in data["rules"] + data["puzzles"] + data["deductions"]:
        for effect in source["effects"]:
            if effect["kind"] == "set_object_state" and effect["target_id"] in attainable_states:
                attainable_states[effect["target_id"]].add(effect["state"])
    def predicate(p):
        refs("evidence", p["all_evidence"])
        refs("deductions", p["all_insights"])
        refs("puzzles", p["all_puzzles"])
        seen = set()
        for item in p["object_states"]:
            ref("objects", item["object_id"])
            require(item["object_id"] not in seen, "duplicate/conflicting object predicate")
            seen.add(item["object_id"])
            require(item["state"] in attainable_states[item["object_id"]], "unattainable object state in predicate")
    targets = dict(grant_evidence="evidence", grant_insight="deductions", unlock_room="rooms", reveal_object="objects", set_object_state="objects", emit_event="events", enable_puzzle="puzzles")
    def effects(items):
        for e in items:
            ref(targets[e["kind"]], e["target_id"])
            require((e["state"] is not None) == (e["kind"] == "set_object_state"), "effect state must be nonnull only for set_object_state")
    ref("rooms", data["initial_room_id"])
    require(tables["rooms"][data["initial_room_id"]]["initially_unlocked"], "initial room is locked")
    for room in data["rooms"]:
        refs("rooms", room["adjacent_room_ids"])
        require(room["id"] not in room["adjacent_room_ids"], "self-adjacent room")
        for adjacent in room["adjacent_room_ids"]:
            require(room["id"] in tables["rooms"][adjacent]["adjacent_room_ids"], "asymmetric room adjacency")
        indexed(room["layers"], "layer")
        for layer in room["layers"]:
            ref("assets", layer["asset_id"])
            asset = tables["assets"][layer["asset_id"]]
            require(asset["kind"] == "image" and asset["width"] * 9 == asset["height"] * 16, "room layer must be 16:9 image")
        if room["ambient_audio_asset_id"] is not None:
            ref("assets", room["ambient_audio_asset_id"])
            require(tables["assets"][room["ambient_audio_asset_id"]]["kind"] == "audio", "ambient asset is not audio")
    for obj in data["objects"]:
        ref("rooms", obj["room_id"])
        require(obj["hotspot"]["object_id"] == obj["id"], "hotspot object mismatch")
        b = obj["hotspot"]["bounds"]
        require(b["width"] > 0 and b["height"] > 0 and b["x"] >= 0 and b["y"] >= 0 and b["x"] + b["width"] <= 1 and b["y"] + b["height"] <= 1, "invalid hotspot geometry")
        ops = [x["operation"] for x in obj["hotspot"]["interactions"]]
        require(len(ops) == len(set(ops)), "duplicate object operation")
    for asset in data["assets"]:
        ref("attributions", asset["attribution_id"])
        path = PurePosixPath(asset["src"])
        require(bool(asset["src"]) and not path.is_absolute() and ".." not in path.parts and ":" not in asset["src"] and "\\" not in asset["src"], "unsafe asset path")
    for ev in data["evidence"]:
        ref("rooms", ev["room_id"]); ref("attributions", ev["attribution_id"])
        if ev["asset_id"] is not None: ref("assets", ev["asset_id"])
    for puzzle in data["puzzles"]:
        ref("rooms", puzzle["room_id"]); predicate(puzzle["requires"]); effects(puzzle["effects"])
        if puzzle["id"] == "letter_reconstruction":
            pieces = indexed(puzzle["presentation"]["pieces"], "letter piece")
            slots = indexed(puzzle["presentation"]["slots"], "letter slot")
            placements = puzzle["solution"]["placements"]
            require({p["piece_id"] for p in placements} == set(pieces) and {p["slot_id"] for p in placements} == set(slots), "letter solution must be a bijection")
            for piece in pieces.values():
                if piece["asset_id"] is not None: ref("assets", piece["asset_id"])
    recipes = set()
    for deduction in data["deductions"]:
        refs("evidence", deduction["evidence_ids"]); predicate(deduction["requires"]); effects(deduction["effects"])
        pair = tuple(sorted(deduction["evidence_ids"]))
        require(pair not in recipes, "ambiguous deduction recipe")
        recipes.add(pair)
    for rule in data["rules"]:
        t=rule["trigger"]
        if t["type"] == "inspect":
            require(t["target_id"] in hotspots, "unknown inspect hotspot reference")
        else: ref({"interact_object":"objects", "puzzle_solved":"puzzles", "insight_earned":"deductions"}[t["type"]], t["target_id"])
        require((t["operation"] is not None) == (t["type"] == "interact_object"), "rule trigger operation mismatch")
        if t["type"] == "interact_object":
            require(t["operation"] in [x["operation"] for x in tables["objects"][t["target_id"]]["hotspot"]["interactions"]], "rule uses undeclared object operation")
        predicate(rule["requires"]); effects(rule["effects"])
    # Reject insight-grant dependency cycles; runtime per-action bounds are additional defense.
    edges = {x:set() for x in tables["deductions"]}
    for deduction in data["deductions"]:
        edges[deduction["id"]].update(e["target_id"] for e in deduction["effects"] if e["kind"] == "grant_insight")
    for rule in data["rules"]:
        if rule["trigger"]["type"] == "insight_earned":
            edges[rule["trigger"]["target_id"]].update(e["target_id"] for e in rule["effects"] if e["kind"] == "grant_insight")
    def visit(node, stack):
        require(node not in stack, "unsupported insight event cycle")
        for child in edges[node]: visit(child, stack | {node})
    for node in edges: visit(node, set())
    for ghost in data["ghosts"]:
        ref("rooms", ghost["room_id"]); refs("evidence", ghost["relevant_evidence_ids"])
        if ghost["portrait_asset_id"] is not None: ref("assets", ghost["portrait_asset_id"])
        require(bool(ghost["generic_fallback"].strip()), "empty generic fallback")
    for fact in data["knowledge"]:
        ref("ghosts", fact["ghost_id"]); predicate(fact["requires"]); refs("knowledge", fact["supersedes_ids"])
        require(bool(fact["text"].strip()) and bool(fact["fallback_text"].strip()), "empty knowledge/fallback")
        for old in fact["supersedes_ids"]:
            require(old != fact["id"] and tables["knowledge"][old]["ghost_id"] == fact["ghost_id"], "invalid knowledge supersession")
        if fact["critical"]:
            require(fact["minimum_trust"] in (None, 0) and fact["maximum_suspicion"] in (None, 100), "critical knowledge gated by relationship")
    def visit_knowledge(node, stack):
        require(node not in stack, "knowledge supersession cycle")
        for old in tables["knowledge"][node]["supersedes_ids"]:
            visit_knowledge(old, stack | {node})
    for node in tables["knowledge"]:
        visit_knowledge(node, set())
    sequences = [x["sequence"] for x in data["timeline"]]
    require(len(set(sequences)) == len(sequences), "duplicate timeline sequence")
    for event in data["timeline"]: refs("evidence", event["support_evidence_ids"])
    groups = {}
    for claim in data["claims"]:
        refs("evidence", claim["support_evidence_ids"])
        groups.setdefault(claim["group"], []).append(claim)
        if claim["correct"]:
            require(claim["id"] in SUPPORT and set(claim["support_evidence_ids"]) == SUPPORT[claim["id"]], "canonical claim support mismatch")
        else: require(not claim["support_evidence_ids"], "incorrect claim cannot have scoring support")
    require({c["id"] for c in data["claims"] if c["correct"]} == set(SUPPORT), "missing canonical claims")
    for rows in groups.values():
        require(sum(x["correct"] for x in rows) == 1 and any(not x["correct"] for x in rows), "claim group needs one correct and wrong/unknown alternatives")
    if reachability:
        proof = prove_reachability(data)
        for fact in data["knowledge"]:
            if fact["critical"]:
                require(any(satisfies(fact["requires"], state) for state in proof.history),
                        "unreachable critical disclosure: " + fact["id"])
    return True


@dataclass(eq=True)
class State:
    room: str
    unlocked: set = field(default_factory=set)
    visited: set = field(default_factory=set)
    visible: set = field(default_factory=set)
    objects: dict = field(default_factory=dict)
    evidence: set = field(default_factory=set)
    enabled: set = field(default_factory=set)
    solved: set = field(default_factory=set)
    insights: set = field(default_factory=set)
    events: set = field(default_factory=set)
    fired: set = field(default_factory=set)


def satisfies(p, state):
    return (set(p["all_evidence"]) <= state.evidence and set(p["all_insights"]) <= state.insights
            and set(p["all_puzzles"]) <= state.solved
            and all(state.objects[x["object_id"]] == x["state"] for x in p["object_states"]))


class Traversal:
    """Small content-action oracle; deliberately has no talk/provider/trust action."""
    def __init__(self, data):
        self.data = data
        self.tables = {k:{x["id"]: x for x in data[k]} for k in ("rooms", "objects", "puzzles", "deductions", "claims")}
        self.hotspots = {x["hotspot"]["id"]:x for x in data["objects"]}
        self.state = State(room=data["initial_room_id"], unlocked={r["id"] for r in data["rooms"] if r["initially_unlocked"]}, visited={data["initial_room_id"]}, visible={o["id"] for o in data["objects"] if o["initially_visible"]}, objects={o["id"]:o["initial_state"] for o in data["objects"]})
        self.actions = []
        self.history = [copy.deepcopy(self.state)]
        self.ending_inputs = {}

    def act(self, action):
        before = copy.deepcopy(self.state)
        try:
            result = self._act(action)
        except Exception:
            self.state = before
            raise
        if before != self.state:
            self.actions.append(copy.deepcopy(action))
            self.history.append(copy.deepcopy(self.state))
        return result

    def _act(self, a):
        s = self.state; kind = a["type"]
        if kind == "navigate":
            require(a["room_id"] in s.unlocked and a["room_id"] in self.tables["rooms"][s.room]["adjacent_room_ids"], "room unavailable")
            s.room = a["room_id"]; s.visited.add(s.room)
            return "applied"
        queue = deque()
        if kind in ("inspect", "interact_object"):
            obj = self.hotspots.get(a.get("hotspot_id")) if kind == "inspect" else self.tables["objects"].get(a.get("object_id"))
            require(obj is not None and obj["id"] in s.visible and obj["room_id"] == s.room, "object is hidden or outside current room")
            op = a.get("operation")
            target = a["hotspot_id"] if kind == "inspect" else obj["id"]
            trigger = (kind,target,op)
            if kind == "interact_object":
                require(any(x["operation"]==op and x["enabled"] for x in obj["hotspot"]["interactions"]), "operation unavailable")
                matching=[r for r in self.data["rules"] if (r["trigger"]["type"],r["trigger"]["target_id"],r["trigger"]["operation"])==trigger]
                if matching and all(r["id"] in s.fired for r in matching): return "no_change"
                require(any(satisfies(r["requires"],s) for r in matching), "operation prerequisites unmet")
            queue.append(trigger)
        elif kind == "submit_puzzle":
            p=self.tables["puzzles"].get(a["puzzle_id"])
            require(p is not None and p["room_id"]==s.room and p["id"] in s.enabled and satisfies(p["requires"],s), "puzzle prerequisites unmet")
            if p["id"] in s.solved: return "no_change"
            solution=a["solution"]
            if p["id"]=="letter_reconstruction":
                pairs=solution.get("placements",[])
                require(len(pairs)==4 and len({x["slot_id"] for x in pairs})==4 and len({x["piece_id"] for x in pairs})==4, "invalid letter membership")
                require({x["slot_id"] for x in pairs}=={x["id"] for x in p["presentation"]["slots"]} and {x["piece_id"] for x in pairs}=={x["id"] for x in p["presentation"]["pieces"]}, "unknown letter member")
                correct={x["slot_id"]:x["piece_id"] for x in pairs}=={x["slot_id"]:x["piece_id"] for x in p["solution"]["placements"]}
            else: correct=solution==p["solution"]
            if not correct: return "incorrect"
            s.solved.add(p["id"]); self._effects(p["effects"],queue)
            queue.append(("puzzle_solved",p["id"],None))
        elif kind == "connect_evidence":
            pair=a["evidence_ids"]
            require(len(pair)==2 and len(set(pair))==2 and set(pair)<=s.evidence, "board needs two collected clues")
            d=next((d for d in self.data["deductions"] if set(d["evidence_ids"])==set(pair) and satisfies(d["requires"],s)),None)
            if not d: return "incorrect"
            if d["id"] in s.insights: return "no_change"
            s.insights.add(d["id"]); self._effects(d["effects"],queue)
            queue.append(("insight_earned",d["id"],None))
        else: raise ContentError("unsupported verification action")
        fired=set()
        while queue:
            trigger=queue.popleft()
            for r in sorted(self.data["rules"],key=lambda r:r["id"]):
                t=r["trigger"]
                if (t["type"],t["target_id"],t["operation"])!=trigger: continue
                if r["id"] in fired or (r["once"] and r["id"] in s.fired): continue
                if not satisfies(r["requires"],s): continue
                fired.add(r["id"])
                if r["once"]: s.fired.add(r["id"])
                self._effects(r["effects"],queue)
        return "applied"

    def _effects(self, effects, queue):
        s=self.state
        for e in effects:
            k=e["kind"]; target=e["target_id"]
            if k=="set_object_state": s.objects[target]=e["state"]
            else:
                field_name={"grant_evidence":"evidence", "grant_insight":"insights", "unlock_room":"unlocked", "reveal_object":"visible", "emit_event":"events", "enable_puzzle":"enabled"}[k]
                values=getattr(s,field_name)
                if k=="grant_insight" and target not in values: queue.append(("insight_earned",target,None))
                values.add(target)

    def go(self, target):
        """Find an unlocked route, then execute each actual navigation step."""
        queue=deque([(self.state.room,[])])
        seen={self.state.room}
        while queue:
            node,path=queue.popleft()
            if node==target:
                for room in path: self.act({"type":"navigate","room_id":room})
                return True
            for child in self.tables["rooms"][node]["adjacent_room_ids"]:
                if child in self.state.unlocked and child not in seen:
                    seen.add(child); queue.append((child,path+[child]))
        return False

    def evaluate(self, claims):
        require(bool(self.state.evidence) and 1<=len(claims)<=5, "accusation unavailable")
        score=0; groups=set()
        for item in claims:
            c=self.tables["claims"].get(item["claim_id"])
            require(c is not None and c["group"] not in groups, "invalid claim/group")
            require(set(item["evidence_ids"])<=self.state.evidence, "uncollected support")
            groups.add(c["group"])
            score+=int(c["correct"] and set(c["support_evidence_ids"])<=set(item["evidence_ids"]))
        if score==5 and self.state.solved==PUZZLES and self.state.insights==INSIGHTS: return "truth_revealed"
        return "partial_truth" if score else "false_accusation"


def prove_reachability(data):
    """Construct one concrete legal witness, not an exhaustive all-paths proof.

    Revisit available objects until the fixed point stops. Fail if any required
    milestone is still absent. Object transitions and rule predicates, not just
    adjacency, determine discoveries. No relationship or AI state exists here.
    """
    t=Traversal(data)
    for _ in range(20):
        before=copy.deepcopy(t.state)
        for room in data["rooms"]:
            if not t.go(room["id"]): continue
            for obj in data["objects"]:
                if obj["room_id"]!=t.state.room or obj["id"] not in t.state.visible: continue
                for interaction in obj["hotspot"]["interactions"]:
                    try: t.act({"type":"interact_object","object_id":obj["id"],"operation":interaction["operation"]})
                    except ContentError: pass  # Gate may become satisfiable on a later visit.
                t.act({"type":"inspect","hotspot_id":obj["hotspot"]["id"]})
            for p in data["puzzles"]:
                if p["room_id"]==t.state.room and p["id"] in t.state.enabled and p["id"] not in t.state.solved and satisfies(p["requires"],t.state):
                    t.act({"type":"submit_puzzle","puzzle_id":p["id"],"solution":p["solution"]})
            for d in data["deductions"]:
                if set(d["evidence_ids"])<=t.state.evidence and satisfies(d["requires"],t.state):
                    t.act({"type":"connect_evidence","evidence_ids":d["evidence_ids"]})
        if t.state.evidence==EVIDENCE and t.state.solved==PUZZLES and t.state.insights==INSIGHTS and t.state.visited==ROOMS: break
        # Ignore room movement for convergence; it cannot itself unlock a gate.
        before.room=t.state.room
        if before==t.state: break
    require(t.state.evidence==EVIDENCE and t.state.solved==PUZZLES and t.state.insights==INSIGHTS and t.state.visited==ROOMS, "unreachable required gameplay milestone (check object states/prerequisites)")
    correct=[{"claim_id":c["id"],"evidence_ids":c["support_evidence_ids"]} for c in data["claims"] if c["correct"]]
    wrong=next(c for c in data["claims"] if not c["correct"])
    t.ending_inputs={"truth_revealed":correct,"partial_truth":correct[:1],"false_accusation":[{"claim_id":wrong["id"],"evidence_ids":["gathering_photograph"]}]}
    require(all(t.evaluate(c)==e for e,c in t.ending_inputs.items()), "unreachable ending inputs")
    return t


def permitted_knowledge(data, state, ghost_id, trust=0, suspicion=100):
    eligible=[k for k in data["knowledge"] if k["ghost_id"]==ghost_id and satisfies(k["requires"],state)
              and (k["minimum_trust"] is None or trust>=k["minimum_trust"])
              and (k["maximum_suspicion"] is None or suspicion<=k["maximum_suspicion"])]
    superseded={x for k in eligible for x in k["supersedes_ids"]}
    return [k for k in eligible if k["id"] not in superseded]


def public_view(data, state):
    """Allowlisted content-only view for privacy tests, NOT a full API snapshot."""
    room=next(r for r in data["rooms"] if r["id"]==state.room)
    return {"scene":{k:copy.deepcopy(room[k]) for k in ("id","title","description","layers","canvas")},
            "objects":[{"id":o["id"],"description":o["description"],"hotspot":copy.deepcopy(o["hotspot"])} for o in data["objects"] if o["room_id"]==state.room and o["id"] in state.visible],
            "evidence":[copy.deepcopy(e) for e in data["evidence"] if e["id"] in state.evidence],
            "puzzles":[{"id":p["id"],"presentation":copy.deepcopy(p["presentation"])} for p in data["puzzles"] if p["id"] in state.enabled and p["room_id"]==state.room],
            "claim_options":[{k:c[k] for k in ("id","group","label")} for c in data["claims"]]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path",nargs="?",type=Path,default=HERE/"blackthorn_manor.json")
    parser.add_argument("--witness",action="store_true",help="print PRIVATE action/answer witness; never ship to browser")
    args=parser.parse_args()
    try:
        data=json.loads(args.path.read_text()); validate(data)
        proof=prove_reachability(data)
    except (ContentError, OSError, json.JSONDecodeError) as error:
        parser.exit(1,f"FAIL: {error}\n")
    print(f"PASS: schema, unique IDs, typed references, predicates, geometry; {len(proof.actions)}-action no-AI witness reaches 6 rooms, 8 evidence, 2 puzzles, 4 insights and 3 ending inputs")
    if args.witness: print(json.dumps({"actions":proof.actions,"ending_inputs":proof.ending_inputs},indent=2))


if __name__=="__main__": main()
