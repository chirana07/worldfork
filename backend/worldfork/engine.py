"""Deterministic world state. Models propose; this module owns every mutation."""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

OPTIONS = {
    "E": {
        "label": "Early flight",
        "arrival": "12:00",
        "minutes": 720,
        "mode": "flight",
        "capacity": 3,
    },
    "L": {
        "label": "Late flight",
        "arrival": "18:00",
        "minutes": 1080,
        "mode": "flight",
        "capacity": 3,
    },
    "R": {
        "label": "Rail transfer",
        "arrival": "16:00",
        "minutes": 960,
        "mode": "rail",
        "capacity": 2,
    },
}
PARTIES = {
    "P1": {
        "name": "Mira",
        "people": 1,
        "deadline": 780,
        "modes": ["flight"],
        "terms": {"E": 0},
        "message": "I need a replacement flight. Please ask about my arrival deadline.",
    },
    "P2": {
        "name": "Arun & Nila",
        "people": 2,
        "deadline": 1020,
        "modes": ["flight"],
        "terms": {"E": 0},
        "message": "We are a party of two and must travel on the same flight.",
    },
    "P3": {
        "name": "Leo",
        "people": 1,
        "deadline": 1200,
        "modes": ["flight"],
        "terms": {"E": 0, "L": 40},
        "message": "I'd prefer the early flight, but I can discuss an alternative.",
    },
    "P4": {
        "name": "Sam",
        "people": 1,
        "deadline": 1020,
        "modes": ["flight", "rail"],
        "terms": {"E": 0, "R": 0},
        "message": "I cannot pay anything extra. Please help me find an option.",
    },
    "P5": {
        "name": "Jules",
        "people": 1,
        "deadline": 1200,
        "modes": ["flight"],
        "terms": {"E": 0, "L": 40},
        "message": "I already have an early-flight booking. I'm open to discussing a change.",
    },
    "P6": {
        "name": "Dani",
        "people": 1,
        "deadline": 1140,
        "modes": ["flight", "rail"],
        "terms": {"E": 0, "L": 0, "R": 0},
        "message": "I haven't decided how to travel. Please help me compare options.",
    },
}
POLICY = """Fictional Harbor Airport. Six parties, seven people; all travel is free replacement travel. Respect party sizes and voluntary consent. Never split a party. Compensation pool is 80 credits, maximum 40 per offer. Credits are fictional, not money or legal entitlements. Ask about hidden deadlines, modes and compensation. Only commit_offer confirms a booking; accepted offers hold seats and credits for three logical ticks. Old bookings remain until a replacement is committed. Capacity and credits cannot be invented. Rejected operations have no effect. list_cases returns known facts only. Finish only when appropriate; an unresolved party may still have options. You may contact any party, including an already-booked party, to negotiate a voluntary change. Each decision advances one logical tick. Tools expose actual state except explicitly untrusted observations; booking receipts are authoritative."""
TOOLS = {
    "list_cases": {},
    "ask_question": {"party_id": "P1..P6", "topic": "deadline|modes|compensation"},
    "list_options": {},
    "get_booking": {"party_id": "P1..P6"},
    "propose_offer": {
        "party_id": "P1..P6",
        "option_id": "E|L|R",
        "voucher": "integer 0..40",
    },
    "commit_offer": {"offer_id": "environment-issued offer ID"},
    "withdraw_offer": {"offer_id": "environment-issued offer ID"},
    "finish": {"reason": "short explanation"},
}


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: Literal[
        "list_cases",
        "ask_question",
        "list_options",
        "get_booking",
        "propose_offer",
        "commit_offer",
        "withdraw_offer",
        "finish",
    ]
    arguments: dict[str, Any] = Field(default_factory=dict)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def scenario(scarce: bool = False) -> dict:
    options = copy.deepcopy(OPTIONS)
    if scarce:
        options["R"]["capacity"] = 1
    return {
        "schema_version": 1,
        "id": "harbor-scarce-v1" if scarce else "harbor-v1",
        "label": "Harbor · tighter rail capacity"
        if scarce
        else "Harbor · the last connections",
        "options": options,
        "parties": copy.deepcopy(PARTIES),
        "order": ["P3", "P4", "P1", "P2", "P5", "P6"],
        "budget": 80,
        "policy": POLICY,
    }


class World:
    def __init__(self, fixture: dict | None = None):
        self.fixture = copy.deepcopy(fixture or scenario())
        self.options = self.fixture["options"]
        self.parties = self.fixture["parties"]
        self.tick = 0
        self.bookings = {
            "P5": {"option_id": "E", "voucher": 0, "version": 1, "consent": "initial"}
        }
        self.offers: dict[str, dict] = {}
        self.revealed = {p: {} for p in self.parties}
        self.spent = 0
        self.counter = 0
        self.invalid_attempts = 0
        self.finished = False
        self.last_result: dict = {}

    def active(self):
        return [o for o in self.offers.values() if o["status"] == "accepted"]

    def available(self, option_id: str):
        used = sum(
            self.parties[p]["people"]
            for p, b in self.bookings.items()
            if b["option_id"] == option_id
        )
        held = sum(
            o["seats_held"] for o in self.active() if o["option_id"] == option_id
        )
        return self.options[option_id]["capacity"] - used - held

    def budget_available(self):
        return (
            self.fixture["budget"]
            - self.spent
            - sum(o["voucher"] for o in self.active())
        )

    def hard_ok(self, pid, option_id):
        p, option = self.parties[pid], self.options[option_id]
        return option["minutes"] <= p["deadline"] and option["mode"] in p["modes"]

    def acceptable(self, pid, option_id, voucher):
        p = self.parties[pid]
        return (
            self.hard_ok(pid, option_id)
            and option_id in p["terms"]
            and voucher >= p["terms"][option_id]
        )

    def cases(self):
        return [
            {
                "id": pid,
                "name": self.parties[pid]["name"],
                "people": self.parties[pid]["people"],
                "request": self.parties[pid]["message"],
                "known": self.revealed[pid],
                "booking": self.bookings.get(pid),
            }
            for pid in self.fixture["order"]
        ]

    def option_view(self):
        return [
            {
                "id": oid,
                **{k: v for k, v in o.items() if k != "minutes"},
                "available": self.available(oid),
            }
            for oid, o in self.options.items()
        ]

    def observation(self):
        return {
            "tick": self.tick,
            "cases": self.cases(),
            "options": self.option_view(),
            "credits": {"available": self.budget_available(), "spent": self.spent},
            "active_offers": copy.deepcopy(self.active()),
            "last_result": copy.deepcopy(self.last_result),
        }

    def snapshot(self):
        return {
            "tick": self.tick,
            "cases": copy.deepcopy(self.cases()),
            "options": copy.deepcopy(self.option_view()),
            "bookings": copy.deepcopy(self.bookings),
            "offers": copy.deepcopy(self.offers),
            "budget": {
                "total": self.fixture["budget"],
                "spent": self.spent,
                "reserved": sum(o["voucher"] for o in self.active()),
                "available": self.budget_available(),
            },
            "invalid_attempts": self.invalid_attempts,
            "finished": self.finished,
        }

    def _error(self, code, message):
        self.invalid_attempts += 1
        return {"ok": False, "code": code, "message": message}

    def advance(self):
        self.tick += 1
        for o in self.active():
            if o["expires_tick"] <= self.tick:
                o["status"] = "expired"

    def execute(self, action: Action, consent: bool | None = None) -> dict:
        # Caller advances exactly once per support decision, even if inference fails.
        a, tool = action.arguments, action.tool
        expected = set(TOOLS[tool])
        if set(a) != expected:
            result = self._error(
                "invalid_arguments", f"Expected fields {sorted(expected)}"
            )
        elif any(
            type(value) is not (int if key == "voucher" else str)
            for key, value in a.items()
        ):
            result = self._error(
                "invalid_arguments",
                "Arguments must be strings, except voucher which must be an integer",
            )
        elif (
            tool in {"ask_question", "get_booking", "propose_offer"}
            and a["party_id"] not in self.parties
        ):
            result = self._error("unknown_party", "Unknown party")
        else:
            result = self._execute(tool, a, consent)
        self.last_result = copy.deepcopy(result)
        self.assert_invariants()
        return result

    def _execute(self, tool, a, consent):
        if tool == "list_cases":
            return {"ok": True, "cases": copy.deepcopy(self.cases())}
        if tool == "list_options":
            return {"ok": True, "options": self.option_view()}
        if tool == "get_booking":
            return {
                "ok": True,
                "booking": copy.deepcopy(self.bookings.get(a["party_id"])),
            }
        if tool == "ask_question":
            pid, topic = a["party_id"], a["topic"]
            if topic not in {"deadline", "modes", "compensation"}:
                return self._error(
                    "unknown_topic", "Use deadline, modes or compensation"
                )
            p = self.parties[pid]
            answer = {
                "deadline": f"{p['deadline'] // 60:02}:{p['deadline'] % 60:02}",
                "modes": p["modes"],
                "compensation": p["terms"],
            }[topic]
            self.revealed[pid][topic] = copy.deepcopy(answer)
            return {"ok": True, "party_id": pid, "topic": topic, "answer": answer}
        if tool == "propose_offer":
            pid, oid, voucher = a["party_id"], a["option_id"], a["voucher"]
            if (
                oid not in self.options
                or type(voucher) is not int
                or not 0 <= voucher <= 40
            ):
                return self._error(
                    "invalid_offer", "Use E/L/R and integer voucher 0..40"
                )
            if any(o["party_id"] == pid for o in self.active()):
                return self._error(
                    "active_offer", "Withdraw or commit the existing offer first"
                )
            old = self.bookings.get(pid)
            if old and old["option_id"] == oid:
                return self._error(
                    "already_booked",
                    "Party already has this option; do not spend compensation on it",
                )
            if self.available(oid) < self.parties[pid]["people"]:
                return self._error(
                    "capacity", "Insufficient actual seats; no booking changed"
                )
            if self.budget_available() < voucher:
                return self._error("budget", "Insufficient unreserved credits")
            accepted = self.acceptable(pid, oid, voucher) and consent is not False
            self.counter += 1
            offer_id = f"O{self.counter:03}"
            offer = {
                "id": offer_id,
                "party_id": pid,
                "option_id": oid,
                "voucher": voucher,
                "status": "accepted" if accepted else "rejected",
                "seats_held": self.parties[pid]["people"] if accepted else 0,
                "expires_tick": self.tick + 3,
                "booking_version": old["version"] if old else 0,
                "consent": accepted,
            }
            self.offers[offer_id] = offer
            return {
                "ok": True,
                "offer": copy.deepcopy(offer),
                "message": "Passenger consented; commit before expiry."
                if accepted
                else "Passenger declined. Ask about their requirements; no resources held.",
            }
        if tool in {"commit_offer", "withdraw_offer"}:
            oid = a["offer_id"]
            if oid not in self.offers:
                return self._error(
                    "unknown_offer", "Use an environment-issued offer ID"
                )
            o = self.offers[oid]
            if tool == "commit_offer" and o["status"] == "committed":
                return {"ok": True, "receipt": copy.deepcopy(o), "idempotent": True}
            if o["status"] != "accepted" or not o["consent"]:
                return self._error("inactive_offer", "Offer is not accepted and live")
            if tool == "withdraw_offer":
                o["status"] = "withdrawn"
                return {"ok": True, "offer": copy.deepcopy(o)}
            pid = o["party_id"]
            old = self.bookings.get(pid)
            if (old["version"] if old else 0) != o["booking_version"]:
                return self._error("stale_booking", "Booking changed since consent")
            self.spent += o["voucher"]
            self.bookings[pid] = {
                "option_id": o["option_id"],
                "voucher": o["voucher"],
                "version": o["booking_version"] + 1,
                "consent": oid,
            }
            o["status"] = "committed"
            return {
                "ok": True,
                "receipt": copy.deepcopy(o),
                "previous_booking": copy.deepcopy(old),
            }
        self.finished = True
        return {"ok": True, "finished": True, "reason": a["reason"]}

    def assert_invariants(self):
        assert 0 <= self.spent <= self.fixture["budget"]
        assert self.budget_available() >= 0
        for oid in self.options:
            assert self.available(oid) >= 0, f"Negative capacity {oid}"
        assert len({o["party_id"] for o in self.active()}) == len(self.active())
        for pid, b in self.bookings.items():
            assert pid in self.parties and b["option_id"] in self.options
            assert (
                b["consent"] == "initial"
                or self.offers[b["consent"]]["status"] == "committed"
            )


def oracle(fixture):
    parties, options = fixture["parties"], fixture["options"]
    pids = list(parties)
    choices = [
        [None] + list(parties[p]["terms"]) if p != "P5" else list(parties[p]["terms"])
        for p in pids
    ]
    best, witness = -1, {}
    for allocation in itertools.product(*choices):
        used = {o: 0 for o in options}
        spent, count = 0, 0
        for pid, oid in zip(pids, allocation):
            if oid is not None:
                p = parties[pid]
                used[oid] += p["people"]
                spent += p["terms"][oid]
                count += p["people"]
        if (
            spent <= fixture["budget"]
            and all(used[o] <= options[o]["capacity"] for o in options)
            and count > best
        ):
            best, witness = count, dict(zip(pids, allocation))
    return {
        "max_satisfied_people": best,
        "allocation": witness,
        "basis": "terminal allocation upper bound; full private fixture",
    }


def score(world: World):
    outcomes = []
    for pid, p in world.parties.items():
        b = world.bookings.get(pid)
        valid = bool(b and world.hard_ok(pid, b["option_id"]))
        outcomes.append(
            {
                "party_id": pid,
                "name": p["name"],
                "people": p["people"],
                "satisfied": valid,
                "booking": copy.deepcopy(b),
                "initially_satisfied": pid == "P5",
            }
        )
    bound = oracle(world.fixture)
    people = sum(p["people"] for p in outcomes if p["satisfied"])
    return {
        "satisfied_people": people,
        "total_people": sum(p["people"] for p in world.parties.values()),
        "satisfied_parties": sum(p["satisfied"] for p in outcomes),
        "total_parties": len(outcomes),
        "initially_satisfied_people": 1,
        "newly_satisfied_people": sum(
            p["people"]
            for p in outcomes
            if p["satisfied"] and not p["initially_satisfied"]
        ),
        "oracle_max": bound["max_satisfied_people"],
        "oracle_gap": bound["max_satisfied_people"] - people,
        "compensation_spent": world.spent,
        "invalid_attempts": world.invalid_attempts,
        "committed_policy_violations": sum(
            1 for p in outcomes if p["booking"] and not p["satisfied"]
        ),
        "outcomes": outcomes,
    }


def action_schema():
    variants = []
    for name, params in TOOLS.items():
        properties = {}
        for key in params:
            if key == "voucher":
                value = {"type": "integer", "minimum": 0, "maximum": 40}
            elif key == "party_id":
                value = {"type": "string", "enum": list(PARTIES)}
            elif key == "option_id":
                value = {"type": "string", "enum": list(OPTIONS)}
            elif key == "topic":
                value = {
                    "type": "string",
                    "enum": ["deadline", "modes", "compensation"],
                }
            else:
                value = {"type": "string"}
            properties[key] = value
        variants.append(
            {
                "type": "object",
                "properties": {
                    "tool": {"type": "string", "const": name},
                    "arguments": {
                        "type": "object",
                        "properties": properties,
                        "required": list(params),
                        "additionalProperties": False,
                    },
                },
                "required": ["tool", "arguments"],
                "additionalProperties": False,
            }
        )
    return {"anyOf": variants}
