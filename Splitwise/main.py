from models.enums import SplitType
from services.splitwise_service import SplitwiseService


def main() -> None:
    splitwise = SplitwiseService()

    alice = splitwise.create_user("Alice", "alice@example.com", "alice")
    bob = splitwise.create_user("Bob", "bob@example.com", "bob")
    charlie = splitwise.create_user("Charlie", "charlie@example.com", "charlie")

    trip = splitwise.create_group("Goa Trip", alice.user_id, "goa-trip")
    splitwise.add_group_member(trip.group_id, bob.user_id)
    splitwise.add_group_member(trip.group_id, charlie.user_id)

    splitwise.add_expense(
        description="Dinner",
        amount="1200",
        paid_by_id=alice.user_id,
        participant_ids=[alice.user_id, bob.user_id, charlie.user_id],
        split_type=SplitType.EQUAL,
        group_id=trip.group_id,
    )
    splitwise.add_expense(
        description="Airport taxi",
        amount="600",
        paid_by_id=bob.user_id,
        participant_ids=[alice.user_id, bob.user_id, charlie.user_id],
        split_type=SplitType.EXACT,
        split_values={alice.user_id: "100", bob.user_id: "200", charlie.user_id: "300"},
        group_id=trip.group_id,
    )
    splitwise.add_expense(
        description="Hotel",
        amount="3000",
        paid_by_id=charlie.user_id,
        participant_ids=[alice.user_id, bob.user_id, charlie.user_id],
        split_type=SplitType.PERCENTAGE,
        split_values={alice.user_id: "50", bob.user_id: "30", charlie.user_id: "20"},
        group_id=trip.group_id,
    )

    print("Balances before simplification:")
    for line in splitwise.format_balances():
        print(f"- {line}")

    splitwise.simplify_debts()
    print("\nSimplified balances:")
    for line in splitwise.format_balances():
        print(f"- {line}")


if __name__ == "__main__":
    main()
