"""
KBC Terminal Game
Command-line version of the KBC trivia quiz with REAL timer enforcement.
"""

import os
import sys
import time
import json
import threading
from datetime import datetime

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from game_logic import (
    GameState, process_answer, evaluate_badge, get_money_tree,
    LEVEL_RULES, LEVEL_MAPPING, DOMAINS
)
from questions import build_question_set_batch


# Global flag for timer timeout
timer_expired = False


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print the game header."""
    print("=" * 60)
    print("   🎯  KAUN BANEGA CROREPATI - TERMINAL EDITION  🎯")
    print("=" * 60)
    print()


def print_money_tree(highlight_level: int = None):
    """Print the money tree with current level highlighted."""
    tree = get_money_tree()
    print("\n  💰 MONEY TREE:")
    print("  " + "-" * 40)
    for i, (level, amount, safe) in enumerate(tree, 1):
        marker = "👉" if i == highlight_level else "  "
        print(f"  {marker} {level}: {amount:<10} | {safe}")
    print("  " + "-" * 40)
    print()


def print_question(question: dict, q_num: int, total: int, level: int, time_limit: int):
    """Print a question with options."""
    print(f"\n  📌 Question {q_num}/{total} | Level {level} | ⏱️  {time_limit}s")
    print("  " + "─" * 50)
    print(f"\n  ❓ {question['question']}\n")

    for key, value in question["options"].items():
        print(f"     {key.upper()}) {value}")
    print()


def get_domain_choice() -> str:
    """Let player choose a domain."""
    print("\n  📚 Choose your domain:\n")
    print("     1. Science")
    print("     2. History")
    print("     3. Geography")
    print("     4. Sports")
    print("     5. Entertainment")
    print("     6. Technology")
    print("     7. Literature")
    print("     8. No Particular Domain (Mixed)")
    print()

    while True:
        choice = input("  Enter your choice (1-8): ").strip()
        domains = DOMAINS + ["No Particular Domain"]
        if choice.isdigit() and 1 <= int(choice) <= 8:
            return domains[int(choice) - 1]
        print("  ❌ Invalid choice. Please enter 1-8.")


def get_answer_with_timer(time_limit: int) -> str:
    """
    Get player's answer with REAL timer enforcement.
    Uses threading to interrupt input after time_limit seconds.
    """
    global timer_expired
    timer_expired = False

    answer_container = {"value": None}

    def input_thread():
        """Thread that waits for user input."""
        while answer_container["value"] is None and not timer_expired:
            try:
                ans = input("  Your answer (A/B/C/D or Q to quit): ").strip().lower()
                if ans in ["a", "b", "c", "d", "q"]:
                    answer_container["value"] = ans if ans != "q" else "quit"
                    break
                else:
                    print("  ❌ Invalid input. Enter A, B, C, D, or Q.")
            except EOFError:
                break

    def timer_thread():
        """Thread that counts down and sets timeout flag."""
        global timer_expired
        for remaining in range(time_limit, 0, -1):
            if answer_container["value"] is not None:
                return
            time.sleep(1)
        timer_expired = True
        print("\n  ⏰ TIME'S UP! Press Enter to continue...")

    # Start input thread
    input_t = threading.Thread(target=input_thread, daemon=True)
    input_t.start()

    # Start timer thread
    timer_t = threading.Thread(target=timer_thread, daemon=True)
    timer_t.start()

    # Wait for either input or timeout
    input_t.join(timeout=time_limit + 2)

    if timer_expired and answer_container["value"] is None:
        return "timeout"

    return answer_container["value"] or "timeout"


def print_result(state: GameState):
    """Print game result."""
    print("\n" + "=" * 60)

    if state.status == "completed":
        print("  🎉 CONGRATULATIONS! YOU WON THE GAME! 🎉")
        print(f"  💰 Final Amount: ₹{state.amount_earned:,}")
    elif state.status == "game_over":
        print("  😔 GAME OVER - Wrong Answer!")
        print(f"  💰 You take home: ₹{state.amount_earned:,}")
    elif state.status == "quit":
        print("  🚪 You chose to quit.")
        print(f"  💰 You take home: ₹{state.amount_earned:,}")
    elif state.status == "timed_out":
        print("  ⏰ TIME'S UP!")
        print(f"  💰 You take home: ₹{state.amount_earned:,}")

    badge = evaluate_badge(state)
    if badge:
        print(f"  🏅 Badge Earned: {badge}")

    print("=" * 60)


def save_score(name: str, state: GameState):
    """Save score to local file."""
    try:
        scores = []
        if os.path.exists("scores.json"):
            with open("scores.json", "r") as f:
                scores = json.load(f)

        scores.append({
            "name": name,
            "amount": state.amount_earned,
            "status": state.status,
            "badge": evaluate_badge(state),
            "domain": state.domain,
            "date": datetime.now().isoformat(),
        })

        with open("scores.json", "w") as f:
            json.dump(scores, f, indent=2)

        print("  ✓ Score saved!\n")
    except Exception as e:
        print(f"  ⚠️  Could not save score: {e}\n")


def play_game():
    """Main game loop with REAL timer."""
    clear_screen()
    print_header()

    # Get player name
    name = input("  Enter your name: ").strip() or "Player"
    print(f"\n  Welcome, {name}!\n")

    # Get domain choice
    domain = get_domain_choice()
    print(f"\n  You chose: {domain}")

    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("\n  ⚠️  No GEMINI_API_KEY found in environment.")
        print("  Using hardcoded questions. Set GEMINI_API_KEY for AI-generated questions.")
    else:
        print("\n  🔄 Generating AI questions... (this may take a moment)")

    # Generate questions
    questions = build_question_set_batch(domain, api_key)

    if not questions or len(questions) < 14:
        print("\n  ❌ Failed to load questions. Exiting.")
        return

    print(f"  ✓ {len(questions)} questions loaded!\n")
    input("  Press Enter to start...")

    # Initialize game state
    state = GameState()
    state.domain = domain
    state.questions = questions

    total_questions = sum(LEVEL_RULES[l]["question_count"] for l in range(1, 6))

    # Game loop
    while state.status == "in_progress":
        clear_screen()
        print_header()
        print_money_tree(highlight_level=state.current_level)

        current_q = state.get_current_question()
        if not current_q:
            break

        q_num = state.get_total_questions_answered() + 1
        time_limit = LEVEL_RULES[state.current_level]["time_limit"]

        print_question(current_q, q_num, total_questions, state.current_level, time_limit)
        print(f"  💵 Current Winnings: ₹{state.amount_earned:,}")
        print(f"  ⏱️  You have {time_limit} seconds to answer!\n")

        # Get answer with REAL timer
        answer = get_answer_with_timer(time_limit)

        if answer == "quit":
            confirm = input("  Are you sure you want to quit? (y/n): ").strip().lower()
            if confirm != "y":
                continue

        # Process answer
        state = process_answer(state, answer)

        # Show feedback
        if state.status == "game_over":
            print("\n  ❌ Wrong Answer!")
            correct_opt = current_q["correct"].upper()
            correct_text = current_q["options"][current_q["correct"]]
            print(f"  The correct answer was {correct_opt}) {correct_text}")
            time.sleep(2)
        elif answer == "timeout":
            print("\n  ⏰ TIME'S UP! You ran out of time!")
            time.sleep(2)
        elif answer != "quit" and state.status == "in_progress":
            print("\n  ✅ Correct!")
            time.sleep(1)

        # Check level completion
        if state.status == "in_progress" and state.question_index == 0 and state.get_total_questions_answered() > 0:
            if state.current_level <= 5:
                prev_level = state.current_level - 1
                print(f"\n  🎊 Level {prev_level} Complete! You've reached ₹{state.amount_earned:,}!")
                time.sleep(2)

    # Game ended
    clear_screen()
    print_header()
    print_result(state)

    # Save score
    save_choice = input("  Save your score? (y/n): ").strip().lower()
    if save_choice == "y":
        save_score(name, state)

    # Show leaderboard
    if os.path.exists("scores.json"):
        print("\n  📊 LEADERBOARD:")
        print("  " + "-" * 50)
        try:
            with open("scores.json", "r") as f:
                scores = json.load(f)
            scores.sort(key=lambda x: x["amount"], reverse=True)
            for i, s in enumerate(scores[:10], 1):
                badge_str = f" | {s['badge']}" if s.get("badge") else ""
                print(f"  {i:2}. {s['name']:<15} ₹{s['amount']:<7,} {badge_str}")
        except:
            print("  Could not load leaderboard.")
        print("  " + "-" * 50)

    print("\n  Thanks for playing! 🙏\n")


def main():
    """Entry point with replay loop."""
    while True:
        play_game()
        again = input("  Play again? (y/n): ").strip().lower()
        if again != "y":
            print("\n  Goodbye! 👋\n")
            break


if __name__ == "__main__":
    main()


# """
# KBC Terminal Game
# Command-line version of the KBC trivia quiz.
# """


# import os
# import sys
# import time
# import json
# from datetime import datetime

# # Load .env file if present
# try:
#     from dotenv import load_dotenv
#     load_dotenv()
# except ImportError:
#     pass

# from game_logic import (
#     GameState, process_answer, evaluate_badge, get_money_tree,
#     LEVEL_RULES, LEVEL_MAPPING, DOMAINS
# )
# from questions import build_question_set_batch


# def clear_screen():
#     """Clear the terminal screen."""
#     os.system('cls' if os.name == 'nt' else 'clear')


# def print_header():
#     """Print the game header."""
#     print("=" * 60)
#     print("   🎯  KAUN BANEGA CROREPATI - TERMINAL EDITION  🎯")
#     print("=" * 60)
#     print()


# def print_money_tree(highlight_level: int = None):
#     """Print the money tree with current level highlighted."""
#     tree = get_money_tree()
#     print("\n  💰 MONEY TREE:")
#     print("  " + "-" * 40)
#     for i, (level, amount, safe) in enumerate(tree, 1):
#         marker = "👉" if i == highlight_level else "  "
#         print(f"  {marker} {level}: {amount:<10} | {safe}")
#     print("  " + "-" * 40)
#     print()


# def print_question(question: dict, q_num: int, total: int, level: int, time_limit: int):
#     """Print a question with options."""
#     print(f"\n  📌 Question {q_num}/{total} | Level {level} | ⏱️  {time_limit}s")
#     print("  " + "─" * 50)
#     print(f"\n  ❓ {question['question']}\n")

#     for key, value in question["options"].items():
#         print(f"     {key.upper()}) {value}")
#     print()


# def get_domain_choice() -> str:
#     """Let player choose a domain."""
#     print("\n  📚 Choose your domain:\n")
#     print("     1. Science")
#     print("     2. History")
#     print("     3. Geography")
#     print("     4. Sports")
#     print("     5. Entertainment")
#     print("     6. Technology")
#     print("     7. Literature")
#     print("     8. No Particular Domain (Mixed)")
#     print()

#     while True:
#         choice = input("  Enter your choice (1-8): ").strip()
#         domains = DOMAINS + ["No Particular Domain"]
#         if choice.isdigit() and 1 <= int(choice) <= 8:
#             return domains[int(choice) - 1]
#         print("  ❌ Invalid choice. Please enter 1-8.")


# def get_answer() -> str:
#     """Get player's answer."""
#     while True:
#         answer = input("  Your answer (A/B/C/D or Q to quit): ").strip().lower()
#         if answer in ["a", "b", "c", "d", "q"]:
#             return answer if answer != "q" else "quit"
#         print("  ❌ Invalid input. Enter A, B, C, D, or Q.")


# def print_result(state: GameState):
#     """Print game result."""
#     print("\n" + "=" * 60)

#     if state.status == "completed":
#         print("  🎉 CONGRATULATIONS! YOU WON THE GAME! 🎉")
#         print(f"  💰 Final Amount: ₹{state.amount_earned:,}")
#     elif state.status == "game_over":
#         print("  😔 GAME OVER - Wrong Answer!")
#         print(f"  💰 You take home: ₹{state.amount_earned:,}")
#     elif state.status == "quit":
#         print("  🚪 You chose to quit.")
#         print(f"  💰 You take home: ₹{state.amount_earned:,}")
#     elif state.status == "timed_out":
#         print("  ⏰ TIME'S UP!")
#         print(f"  💰 You take home: ₹{state.amount_earned:,}")

#     badge = evaluate_badge(state)
#     if badge:
#         print(f"  🏅 Badge Earned: {badge}")

#     print("=" * 60)


# def save_score(name: str, state: GameState):
#     """Save score to local file."""
#     try:
#         scores = []
#         if os.path.exists("scores.json"):
#             with open("scores.json", "r") as f:
#                 scores = json.load(f)

#         scores.append({
#             "name": name,
#             "amount": state.amount_earned,
#             "status": state.status,
#             "badge": evaluate_badge(state),
#             "domain": state.domain,
#             "date": datetime.now().isoformat(),
#         })

#         with open("scores.json", "w") as f:
#             json.dump(scores, f, indent=2)

#         print("  ✓ Score saved!\n")
#     except Exception as e:
#         print(f"  ⚠️  Could not save score: {e}\n")


# def play_game():
#     """Main game loop."""
#     clear_screen()
#     print_header()

#     # Get player name
#     name = input("  Enter your name: ").strip() or "Player"
#     print(f"\n  Welcome, {name}!\n")

#     # Get domain choice
#     domain = get_domain_choice()
#     print(f"\n  You chose: {domain}")

#     # Get API key
#     api_key = os.environ.get("GEMINI_API_KEY", "")
#     if not api_key:
#         print("\n  ⚠️  No GEMINI_API_KEY found in environment.")
#         print("  Using hardcoded questions. Set GEMINI_API_KEY for AI-generated questions.")
#     else:
#         print("\n  🔄 Generating AI questions... (this may take a moment)")

#     # Generate questions
#     questions = build_question_set_batch(domain, api_key)

#     if not questions or len(questions) < 14:
#         print("\n  ❌ Failed to load questions. Exiting.")
#         return

#     print(f"  ✓ {len(questions)} questions loaded!\n")
#     input("  Press Enter to start...")

#     # Initialize game state
#     state = GameState()
#     state.domain = domain
#     state.questions = questions

#     total_questions = sum(LEVEL_RULES[l]["question_count"] for l in range(1, 6))

#     # Game loop
#     while state.status == "in_progress":
#         clear_screen()
#         print_header()
#         print_money_tree(highlight_level=state.current_level)

#         current_q = state.get_current_question()
#         if not current_q:
#             break

#         q_num = state.get_total_questions_answered() + 1
#         time_limit = LEVEL_RULES[state.current_level]["time_limit"]

#         print_question(current_q, q_num, total_questions, state.current_level, time_limit)

#         # Timer display (informational only in terminal)
#         print(f"  💵 Current Winnings: ₹{state.amount_earned:,}")
#         print(f"  ⏱️  Time Limit: {time_limit} seconds")
#         print()

#         # Get answer
#         answer = get_answer()

#         if answer == "quit":
#             confirm = input("  Are you sure you want to quit? (y/n): ").strip().lower()
#             if confirm != "y":
#                 continue

#         # Process answer
#         state = process_answer(state, answer)

#         # Show feedback
#         if state.status == "game_over":
#             print("\n  ❌ Wrong Answer!")
#             correct_opt = current_q["correct"].upper()
#             correct_text = current_q["options"][current_q["correct"]]
#             print(f"  The correct answer was {correct_opt}) {correct_text}")
#             time.sleep(2)
#         elif answer != "quit" and state.status == "in_progress":
#             print("\n  ✅ Correct!")
#             time.sleep(1)

#         # Check level completion
#         if state.status == "in_progress" and state.question_index == 0 and state.get_total_questions_answered() > 0:
#             if state.current_level <= 5:
#                 prev_level = state.current_level - 1
#                 print(f"\n  🎊 Level {prev_level} Complete! You've reached ₹{state.amount_earned:,}!")
#                 time.sleep(2)

#     # Game ended
#     clear_screen()
#     print_header()
#     print_result(state)

#     # Save score
#     save_choice = input("  Save your score? (y/n): ").strip().lower()
#     if save_choice == "y":
#         save_score(name, state)

#     # Show leaderboard
#     if os.path.exists("scores.json"):
#         print("\n  📊 LEADERBOARD:")
#         print("  " + "-" * 50)
#         try:
#             with open("scores.json", "r") as f:
#                 scores = json.load(f)
#             # Sort by amount descending
#             scores.sort(key=lambda x: x["amount"], reverse=True)
#             for i, s in enumerate(scores[:10], 1):
#                 badge_str = f" | {s['badge']}" if s.get("badge") else ""
#                 print(f"  {i:2}. {s['name']:<15} ₹{s['amount']:<7,} {badge_str}")
#         except:
#             print("  Could not load leaderboard.")
#         print("  " + "-" * 50)

#     print("\n  Thanks for playing! 🙏\n")


# def main():
#     """Entry point with replay loop."""
#     while True:
#         play_game()
#         again = input("  Play again? (y/n): ").strip().lower()
#         if again != "y":
#             print("\n  Goodbye! 👋\n")
#             break


# if __name__ == "__main__":
#     main()
