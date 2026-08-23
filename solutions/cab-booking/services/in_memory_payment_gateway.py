from decimal import Decimal
from uuid import uuid4

from models.enums import PaymentMethod, PaymentStatus
from models.payment import Payment
from services.clock import Clock, SystemClock
from services.payment_gateway import PaymentGateway


class InMemoryPaymentGateway(PaymentGateway):
    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self.fail_next_charge = False
        self.payments: dict[str, Payment] = {}

    def charge(self, ride_id: str, amount: Decimal, method: PaymentMethod) -> Payment:
        status = PaymentStatus.COMPLETED
        failure_reason = None
        if self.fail_next_charge:
            self.fail_next_charge = False
            status = PaymentStatus.FAILED
            failure_reason = "Payment provider declined the transaction"
        payment = Payment(
            payment_id=str(uuid4()),
            ride_id=ride_id,
            amount=amount,
            method=method,
            status=status,
            created_at=self._clock.now(),
            failure_reason=failure_reason,
        )
        self.payments[payment.payment_id] = payment
        return payment
