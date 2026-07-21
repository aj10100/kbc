"""
KBC Game Logic Module
Pure game state management - no I/O, no AI, no UI.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal

LEVEL_RULES = {
    1: {
        "question_count": 2,
        "time_limit": 30,
        "amount_at_start": 0,
        "amount_if_complete": 500,
        "failure_behavior": "reset_to_start",
        "quit_timeout_behavior": "reset_to_start",
    },
    2: {
        "question_count": 2,
        "time_limit": 45,
        "amount_at_start": 500,
        "amount_if_complete": 1300,
        "failure_behavior": "keep_at_start",
        "quit_timeout_behavior": "keep_at_start",
    },
    3: {
        "question_count": 3,
        "time_limit": 60,
        "amount_at_start": 1300,
        "amount_if_complete": 2500,
        "failure_behavior": "reset_to_start",
        "quit_timeout_behavior": "keep_in_level",
    },
    4: {
        "question_count": 4,
        "time_limit": 60,
        "amount_at_start": 2500,
        "amount_if_complete": 4500,
        "failure_behavior": "keep_in_level",
        "quit_timeout_behavior": "keep_in_level",
    },
    5: {
        "question_count": 3,
        "time_limit": 90,
        "amount_at_start": 4000,
        "amount_if_complete": 7000,
        "failure_behavior": "reset_all",
        "quit_timeout_behavior": "keep_at_start",
    },
}

LEVEL_MAPPING = {
    1: {"difficulty": "medium", "region": "West Bengal, India"},
    2: {"difficulty": "medium-hard", "region": "India"},
    3: {"difficulty": "hard", "region": "worldwide"},
    4: {"difficulty": "expert", "region": "worldwide"},
    5: {"difficulty": "extreme", "region": "worldwide"},
}

DOMAINS = [
    "Science", "History", "Geography", "Sports",
    "Entertainment", "Technology", "Literature",
]


@dataclass
class GameState:
    current_level: int = 1
    question_index: int = 0
    amount_earned: int = 0
    status: Literal["in_progress", "completed", "quit", "timed_out", "game_over"] = "in_progress"
    domain: str = ""
    questions: list = field(default_factory=list)
    current_question_start_time: Optional[float] = None

    def get_current_question(self) -> Optional[dict]:
        if not self.questions:
            return None
        abs_index = sum(LEVEL_RULES[l]["question_count"] for l in range(1, self.current_level))
        abs_index += self.question_index
        if abs_index < len(self.questions):
            return self.questions[abs_index]
        return None

    def get_total_questions_answered(self) -> int:
        return sum(LEVEL_RULES[l]["question_count"] for l in range(1, self.current_level)) + self.question_index

    def get_level_progress(self) -> str:
        rules = LEVEL_RULES[self.current_level]
        return f"Question {self.question_index + 1}/{rules['question_count']}"


def process_answer(state: GameState, answer: str) -> GameState:
    if state.status != "in_progress":
        return state

    rules = LEVEL_RULES[state.current_level]
    current_q = state.get_current_question()

    if answer == "quit":
        if rules["quit_timeout_behavior"] == "reset_to_start":
            state.amount_earned = rules["amount_at_start"]
        elif rules["quit_timeout_behavior"] == "keep_at_start":
            state.amount_earned = rules["amount_at_start"]
        elif rules["quit_timeout_behavior"] == "keep_in_level":
            pass
        state.status = "quit"
        return state

    if answer == "timeout":
        if rules["quit_timeout_behavior"] == "reset_to_start":
            state.amount_earned = rules["amount_at_start"]
        elif rules["quit_timeout_behavior"] == "keep_at_start":
            state.amount_earned = rules["amount_at_start"]
        elif rules["quit_timeout_behavior"] == "keep_in_level":
            pass
        state.status = "timed_out"
        return state

    is_correct = (answer.lower() == current_q["correct"].lower())

    if is_correct:
        state.question_index += 1

        if state.current_level in [3, 4, 5]:
            per_q = (rules["amount_if_complete"] - rules["amount_at_start"]) / rules["question_count"]
            state.amount_earned = rules["amount_at_start"] + int(per_q * state.question_index)
        else:
            if state.question_index >= rules["question_count"]:
                state.amount_earned = rules["amount_if_complete"]

        if state.question_index >= rules["question_count"]:
            state.amount_earned = rules["amount_if_complete"]
            state.question_index = 0
            state.current_level += 1
            if state.current_level > 5:
                state.current_level = 5
                state.status = "completed"
    else:
        if rules["failure_behavior"] == "reset_to_start":
            state.amount_earned = rules["amount_at_start"]
        elif rules["failure_behavior"] == "keep_at_start":
            state.amount_earned = rules["amount_at_start"]
        elif rules["failure_behavior"] == "keep_in_level":
            state.question_index += 1
            if state.question_index >= rules["question_count"]:
                state.amount_earned = rules["amount_if_complete"]
                state.question_index = 0
                state.current_level += 1
                if state.current_level > 5:
                    state.current_level = 5
                    state.status = "completed"
            return state
        elif rules["failure_behavior"] == "reset_all":
            state.amount_earned = 0

        state.status = "game_over"

    return state


def evaluate_badge(state: GameState) -> Optional[str]:
    if state.status == "completed":
        return "🏆 Crorepati - Perfect Game!"

    amount = state.amount_earned
    level = state.current_level

    if amount >= 4000:
        return "🥇 Diamond Badge - Level 5 Master"
    elif amount >= 2500:
        return "🥈 Gold Badge - Level 4 Achiever"
    elif amount >= 1300:
        return "🥉 Silver Badge - Level 3 Survivor"
    elif amount >= 500:
        return "⭐ Bronze Badge - Level 2 Starter"
    elif level >= 2:
        return "🌟 Participant Badge - Good Try"

    return None


def get_money_tree() -> list:
    return [
        ("Level 1", "₹500", "Safe: ₹0"),
        ("Level 2", "₹1,300", "Safe: ₹500"),
        ("Level 3", "₹2,500", "Safe: ₹1,300"),
        ("Level 4", "₹4,500", "Safe: ₹2,500"),
        ("Level 5", "₹7,000", "Safe: ₹4,000"),
    ]


if __name__ == "__main__":
    print("Running game logic tests...\n")

    # Test 1: Full correct playthrough
    print("Test 1: Full correct playthrough")
    state = GameState()
    state.questions = [{"correct": "a"} for _ in range(14)]
    for i in range(14):
        state = process_answer(state, "a")
    print(f"  Final: Level={state.current_level}, Amount=₹{state.amount_earned}, Status={state.status}")
    assert state.status == "completed"
    assert state.amount_earned == 7000
    print("  ✓ PASSED\n")

    # Test 2: Wrong answer at Level 1
    print("Test 2: Wrong answer at Level 1")
    state = GameState()
    state.questions = [{"correct": "a"} for _ in range(14)]
    state = process_answer(state, "a")
    state = process_answer(state, "b")
    print(f"  Final: Level={state.current_level}, Amount=₹{state.amount_earned}, Status={state.status}")
    assert state.status == "game_over"
    assert state.amount_earned == 0
    print("  ✓ PASSED\n")

    # Test 3: Wrong answer at Level 3
    print("Test 3: Wrong answer at Level 3")
    state = GameState()
    state.questions = [{"correct": "a"} for _ in range(14)]
    for _ in range(5):
        state = process_answer(state, "a")
    state = process_answer(state, "b")
    print(f"  Final: Level={state.current_level}, Amount=₹{state.amount_earned}, Status={state.status}")
    assert state.status == "game_over"
    assert state.amount_earned == 1300
    print("  ✓ PASSED\n")

    # Test 4: Quit at Level 4
    print("Test 4: Quit at Level 4")
    state = GameState()
    state.questions = [{"correct": "a"} for _ in range(14)]
    for _ in range(7):
        state = process_answer(state, "a")
    state = process_answer(state, "quit")
    print(f"  Final: Level={state.current_level}, Amount=₹{state.amount_earned}, Status={state.status}")
    assert state.status == "quit"
    assert state.amount_earned == 2500
    print("  ✓ PASSED\n")

    # Test 5: Timeout at Level 5
    print("Test 5: Timeout at Level 5")
    state = GameState()
    state.questions = [{"correct": "a"} for _ in range(14)]
    for _ in range(11):
        state = process_answer(state, "a")
    state = process_answer(state, "timeout")
    print(f"  Final: Level={state.current_level}, Amount=₹{state.amount_earned}, Status={state.status}")
    assert state.status == "timed_out"
    assert state.amount_earned == 4000
    print("  ✓ PASSED\n")

    # Test 6: Wrong at Level 5 resets all
    print("Test 6: Wrong at Level 5 resets all")
    state = GameState()
    state.questions = [{"correct": "a"} for _ in range(14)]
    for _ in range(11):
        state = process_answer(state, "a")
    state = process_answer(state, "b")
    print(f"  Final: Level={state.current_level}, Amount=₹{state.amount_earned}, Status={state.status}")
    assert state.status == "game_over"
    assert state.amount_earned == 0
    print("  ✓ PASSED\n")

    # Test 7: Wrong in Level 4 keeps progress
    print("Test 7: Wrong in Level 4 keeps progress")
    state = GameState()
    state.questions = [{"correct": "a"} for _ in range(14)]
    for _ in range(7):
        state = process_answer(state, "a")
    # At L4 now (after completing L1, L2, L3 = 7 questions)
    state = process_answer(state, "a")  # L4Q1 correct -> index=1, amount=3000
    state = process_answer(state, "b")  # L4Q2 wrong -> index=2, amount=3000 (keep_in_level)
    print(f"  After wrong: Level={state.current_level}, index={state.question_index}, Amount=₹{state.amount_earned}, Status={state.status}")
    assert state.status == "in_progress"
    assert state.amount_earned == 3000
    assert state.current_level == 4
    state = process_answer(state, "a")  # L4Q3 -> index=3, amount=3500
    print(f"  After L4Q3: Level={state.current_level}, index={state.question_index}, Amount=₹{state.amount_earned}")
    state = process_answer(state, "a")  # L4Q4 -> index=4 >= 4, completes level, amount=4500, level=5
    print(f"  After L4Q4: Level={state.current_level}, index={state.question_index}, Amount=₹{state.amount_earned}")
    assert state.amount_earned == 4500
    assert state.current_level == 5
    print("  ✓ PASSED\n")

    print("All tests passed! ✓")
