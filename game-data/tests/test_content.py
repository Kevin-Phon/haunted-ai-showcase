"""Content consumer tests. These are not receipts for the gameplay backend."""
import copy
import json
import sys
import unittest
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DATA_DIR))
from validate_content import ContentError, validate, Traversal, prove_reachability, public_view, permitted_knowledge


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((DATA_DIR / "blackthorn_manor.json").read_text())

    def test_canonical_content_and_all_milestones(self):
        validate(self.data)
        proof = prove_reachability(self.data)
        self.assertEqual(len(proof.state.evidence), 8)
        self.assertEqual(len(proof.state.insights), 4)
        self.assertEqual(len(proof.state.solved), 2)
        self.assertEqual(len(proof.state.visited), 6)
        self.assertLess(len(proof.actions), 100)
        self.assertEqual(proof.ending_inputs["truth_revealed"][0]["claim_id"], "eleanor_disconnected_stabilizer")
        for ending, claims in proof.ending_inputs.items():
            self.assertEqual(proof.evaluate(claims), ending)

    def test_schema_rejects_wrong_type_and_unknown_field(self):
        for change in [lambda d: d.update(unexpected=True), lambda d: d["ghosts"][0].update(initial_trust="30")]:
            d = copy.deepcopy(self.data); change(d)
            with self.assertRaises(ContentError): validate(d)

    def test_duplicate_ids_and_wrong_typed_references(self):
        for change in [lambda d: d["objects"][1].update(id=d["objects"][0]["id"]),
                       lambda d: d["rules"][0]["trigger"].update(target_id="eleanor"),
                       lambda d: d["objects"][0]["hotspot"].update(object_id="thomas"),
                       lambda d: d["claims"][0].update(support_evidence_ids=["entrance_hall"])]:
            d = copy.deepcopy(self.data); change(d)
            with self.assertRaises(ContentError): validate(d)

    def test_geometry_and_asset_traversal(self):
        d = copy.deepcopy(self.data); d["objects"][0]["hotspot"]["bounds"].update(x=0.9,width=0.5)
        with self.assertRaises(ContentError): validate(d)
        d = copy.deepcopy(self.data)
        d["assets"] = [{"id":"bad_asset","kind":"image","src":"../secret.png","alt":"test","attribution_id":d["attributions"][0]["id"],"width":1600,"height":900}]
        with self.assertRaises(ContentError): validate(d)

    def test_circular_gate_fails_despite_connected_rooms(self):
        d = copy.deepcopy(self.data)
        next(p for p in d["puzzles"] if p["id"] == "machine_calibration")["requires"]["all_evidence"].append("final_recording")
        with self.assertRaisesRegex(ContentError, "unreachable"): validate(d)

    def test_hidden_objects_and_puzzle_prerequisites(self):
        t = Traversal(self.data)
        with self.assertRaises(ContentError): t.act({"type":"inspect","hotspot_id":"hs_study_desk_compartment"})
        t.act({"type":"navigate","room_id":"laboratory"})
        with self.assertRaises(ContentError): t.act({"type":"submit_puzzle","puzzle_id":"machine_calibration","solution":{"power_level":2,"phase":"cyan","stabilizer":"engaged"}})
        self.assertFalse(t.state.evidence)

    def test_wrong_puzzle_then_retry_and_duplicate_no_awards(self):
        t = Traversal(self.data)
        t.act({"type":"navigate","room_id":"library"})
        t.act({"type":"interact_object","object_id":"library_letter_drawer","operation":"open"})
        puzzle = next(p for p in self.data["puzzles"] if p["id"] == "letter_reconstruction")
        wrong = copy.deepcopy(puzzle["solution"])
        wrong["placements"][0]["piece_id"], wrong["placements"][1]["piece_id"] = wrong["placements"][1]["piece_id"], wrong["placements"][0]["piece_id"]
        self.assertEqual(t.act({"type":"submit_puzzle","puzzle_id":puzzle["id"],"solution":wrong}), "incorrect")
        action = {"type":"submit_puzzle","puzzle_id":puzzle["id"],"solution":puzzle["solution"]}
        self.assertEqual(t.act(action), "applied")
        before = copy.deepcopy(t.state)
        self.assertEqual(t.act(action), "no_change")
        self.assertEqual(t.state, before)
        self.assertIn("torn_letter", t.state.evidence)
        self.assertIn("study_desk_compartment", t.state.visible)
        self.assertEqual(t.state.events, {"event_letter_whisper"})

    def test_invalid_board_pair_never_unlocks_passage(self):
        t = Traversal(self.data)
        with self.assertRaises(ContentError): t.act({"type":"connect_evidence","evidence_ids":["servant_log","gathering_photograph"]})
        self.assertNotIn("hidden_passage",t.state.unlocked)

    def test_low_trust_knowledge_and_corrected_alibi(self):
        t=prove_reachability(self.data)
        facts=permitted_knowledge(self.data,t.state,"thomas",trust=0,suspicion=100)
        self.assertIn("thomas_restart_admission", {x["id"] for x in facts})
        self.assertNotIn("thomas_initial_alibi", {x["id"] for x in facts})
        self.assertTrue(all(x["fallback_text"] for x in facts))
        self.assertTrue(any(x["minimum_trust"] == 50 for x in self.data["knowledge"]))

    def test_private_projection_has_no_answers_or_locked_content(self):
        t=Traversal(self.data)
        view=public_view(self.data,t.state)
        text=json.dumps(view)
        for key in ["solution", "timeline", "correct", "support_evidence_ids", "fallback_text", "requires", "knowledge"]:
            self.assertNotIn('"'+key+'"',text)
        self.assertNotIn("study_desk_compartment",text)
        self.assertNotIn("passage_report_box",text)
        self.assertEqual(view["evidence"],[])
        self.assertEqual(view["puzzles"],[])

    def test_letter_solution_is_bijection(self):
        d=copy.deepcopy(self.data)
        p=next(p for p in d["puzzles"] if p["id"]=="letter_reconstruction")
        p["solution"]["placements"][0]=copy.deepcopy(p["solution"]["placements"][1])
        with self.assertRaises(ContentError): validate(d)

    def test_critical_knowledge_cannot_require_good_relationship(self):
        d=copy.deepcopy(self.data)
        next(x for x in d["knowledge"] if x["critical"])["minimum_trust"]=50
        with self.assertRaises(ContentError): validate(d)


    def test_knowledge_supersession_cycles_rejected(self):
        d=copy.deepcopy(self.data)
        facts=[k for k in d["knowledge"] if k["ghost_id"]=="eleanor"][:2]
        facts[0]["supersedes_ids"]=[facts[1]["id"]]
        facts[1]["supersedes_ids"]=[facts[0]["id"]]
        with self.assertRaisesRegex(ContentError,"supersession cycle"): validate(d)

    def test_wrong_machine_settings_can_retry_and_no_duplicate_event(self):
        t=prove_reachability(self.data)
        # Replay the witness prefix up to calibration, retaining real state gates.
        fresh=Traversal(self.data)
        for action in t.actions:
            if action["type"]=="submit_puzzle" and action["puzzle_id"]=="machine_calibration": break
            fresh.act(action)
        bad={"type":"submit_puzzle","puzzle_id":"machine_calibration","solution":{"power_level":1,"phase":"amber","stabilizer":"bypass"}}
        before=copy.deepcopy(fresh.state)
        self.assertEqual(fresh.act(bad),"incorrect")
        self.assertEqual(fresh.state,before)
        good=copy.deepcopy(bad); good["solution"]={"power_level":2,"phase":"cyan","stabilizer":"engaged"}
        self.assertEqual(fresh.act(good),"applied")
        after=copy.deepcopy(fresh.state)
        self.assertEqual(fresh.act(good),"no_change")
        self.assertEqual(fresh.state,after)
        self.assertIn("event_machine_echo",fresh.state.events)

    def test_collected_but_incompatible_board_pair_has_no_effect(self):
        t=prove_reachability(self.data)
        before=copy.deepcopy(t.state)
        self.assertEqual(t.act({"type":"connect_evidence","evidence_ids":["memory_crystal","gathering_photograph"]}),"incorrect")
        self.assertEqual(t.state,before)

    def test_insight_event_cycles_and_bad_effect_state_rejected(self):
        d=copy.deepcopy(self.data)
        d["deductions"][0]["effects"]=[{"kind":"grant_insight","target_id":d["deductions"][0]["id"],"state":None}]
        with self.assertRaisesRegex(ContentError,"cycle"): validate(d)
        d=copy.deepcopy(self.data); d["rules"][0]["effects"][0]["state"]="open"
        with self.assertRaises(ContentError): validate(d)

    def test_fifo_direct_effects_then_cascade_and_atomic_rollback(self):
        t=Traversal(self.data)
        t.act({"type":"navigate","room_id":"study"})
        rule={"id":"cascade_test","trigger":{"type":"inspect","target_id":"hs_study_notebook","operation":None},
              "requires":{"all_evidence":[],"all_insights":[],"all_puzzles":[],"object_states":[]},
              "effects":[{"kind":"grant_insight","target_id":"deduction_hidden_route","state":None}],"once":True}
        t.data=copy.deepcopy(self.data); t.data["rules"].append(rule)
        t.act({"type":"inspect","hotspot_id":"hs_study_notebook"})
        self.assertIn("hall_wall_panel",t.state.visible)
        # Runtime failure after a tentative reward must not leave the reward behind.
        t=Traversal(copy.deepcopy(self.data)); t.go("study")
        t.data["rules"][0]["effects"].append({"kind":"invalid_kind","target_id":"bad","state":None})
        before=copy.deepcopy(t.state)
        with self.assertRaises(KeyError): t.act({"type":"inspect","hotspot_id":"hs_study_notebook"})
        self.assertEqual(t.state,before)

    def test_accusation_support_is_claim_specific(self):
        t=prove_reachability(self.data)
        self.assertEqual(t.evaluate([{"claim_id":"eleanor_disconnected_stabilizer","evidence_ids":["gathering_photograph"]}]),"false_accusation")
        with self.assertRaises(ContentError): t.evaluate([{"claim_id":"eleanor_disconnected_stabilizer","evidence_ids":["not_collected"]}])
        with self.assertRaises(ContentError): t.evaluate([{"claim_id":"eleanor_disconnected_stabilizer","evidence_ids":[]},{"claim_id":"eleanor_no_intervention","evidence_ids":[]}])


    def test_impossible_object_state_in_critical_knowledge_rejected(self):
        d=copy.deepcopy(self.data)
        next(k for k in d["knowledge"] if k["id"]=="eleanor_admission")["requires"]["object_states"]=[{"object_id":"hall_case_plaque","state":"calibrated"}]
        with self.assertRaisesRegex(ContentError,"unattainable object state"): validate(d)

    def test_critical_disclosure_gate_must_occur_on_concrete_witness(self):
        d=copy.deepcopy(self.data)
        # Drawer closed is individually possible, but not after its letter is earned.
        next(k for k in d["knowledge"] if k["id"]=="eleanor_admission")["requires"]["object_states"]=[{"object_id":"library_letter_drawer","state":"closed"}]
        with self.assertRaisesRegex(ContentError,"unreachable critical disclosure"): validate(d)


if __name__ == "__main__": unittest.main()
