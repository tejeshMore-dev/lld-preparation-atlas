from datetime import date

from services.atm import ATM
from services.cash_dispenser import CashDispenser
from services.in_memory_bank_service import InMemoryBankService
from strategies.exact_cash_strategy import ExactCashStrategy


def main() -> None:
    bank = InMemoryBankService()
    account = bank.create_account("ACC-001", "Aarav", "10000")
    bank.create_account("ACC-002", "Meera", "2500")
    card = bank.issue_card(
        card_number="4111111111111111",
        account_id=account.account_id,
        pin="1234",
        expiry_date=date(2030, 12, 31),
    )

    atm = ATM(
        atm_id="ATM-01",
        bank_gateway=bank,
        cash_dispenser=CashDispenser(
            inventory={500: 20, 200: 20, 100: 20},
            selection_strategy=ExactCashStrategy(),
        ),
        withdrawal_limit="20000",
    )

    atm.insert_card(card.card_number)
    atm.enter_pin("1234")
    print(f"Opening balance: INR {atm.check_balance():.2f}")

    withdrawal = atm.withdraw("1300")
    print(
        f"Withdrawal: {withdrawal.status.name}, "
        f"notes={withdrawal.cash_breakdown}"
    )

    transfer = atm.transfer("ACC-002", "750")
    print(f"Transfer: {transfer.status.name}")

    deposit = atm.deposit({500: 1, 200: 1})
    print(f"Deposit: {deposit.status.name}")
    print(f"Closing balance: INR {atm.check_balance():.2f}")
    atm.eject_card()


if __name__ == "__main__":
    main()
