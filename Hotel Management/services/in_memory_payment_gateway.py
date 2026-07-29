from decimal import Decimal
from uuid import uuid4

from models.enums import PaymentMethod, PaymentStatus
from models.payment import Payment
from services.clock import Clock, SystemClock
from services.payment_gateway import PaymentGateway


class InMemoryPaymentGateway(PaymentGateway):
    """Controllable fake provider for demonstrations and deterministic tests."""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self.fail_next_charge = False
        self.payments: dict[str, Payment] = {}

    def charge(self, booking_id: str, amount: Decimal, method: PaymentMethod) -> Payment:
        status = PaymentStatus.COMPLETED
        failure_reason = None
        if self.fail_next_charge:
            self.fail_next_charge = False
            status = PaymentStatus.FAILED
            failure_reason = "Payment provider declined the transaction"
        payment = Payment(
            payment_id=str(uuid4()),
            booking_id=booking_id,
            amount=amount,
            method=method,
            status=status,
            created_at=self._clock.now(),
            failure_reason=failure_reason,
        )
        self.payments[payment.payment_id] = payment
        return payment

    def refund(self, payment: Payment) -> Payment:
        if payment.status is PaymentStatus.REFUNDED:
            return payment
        if payment.status is not PaymentStatus.COMPLETED:
            raise ValueError("Only completed payments can be refunded")
        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = self._clock.now()
        return payment
