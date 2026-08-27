# Food Delivery

Build a cart, place an order, coordinate restaurant acceptance, assign a courier, deliver, and settle payment.

## Scope

Support restaurants, menus, carts, orders, payment, restaurant decisions, courier assignment, pickup, delivery, cancellation, and refund. Search ranking, maps, and notifications are external.

## Model

| Type | Responsibility |
|---|---|
| MenuItem and Cart | selected items and quantities |
| Order | immutable line snapshot and lifecycle |
| Restaurant | menu and acceptance |
| Courier | availability and assignment |
| Delivery | pickup/drop-off lifecycle |
| PricingStrategy | subtotal, fees, and adjustments |
| AssignmentStrategy | chooses an eligible courier |
| OrderService | checkout and subsequent commands |

Cart prices are provisional; Order stores the accepted item and price snapshot.

## Checkout flow

1. Validate one restaurant and currently available menu items.
2. Create an order snapshot and exact quote.
3. Authorize or charge payment according to the chosen policy.
4. Submit to the restaurant.
5. On acceptance, assign a courier and progress delivery.
6. On rejection or eligible cancellation, refund/void payment.

## Design choices

- Order and Delivery have separate lifecycles.
- Pricing and courier selection are strategies.
- PaymentGateway and Clock are injected boundaries.
- OrderService coordinates; entities guard transitions.
- Events can drive optional notifications after state changes.

## Correctness

A courier must not be assigned twice; assignment is a conditional state change. Payment and order state span systems, so retries need idempotency and failures need explicit refund/reconciliation.

## Run

    python "solutions/food-delivery/main.py"
    python -m unittest discover -s "solutions/food-delivery/tests" -t "solutions/food-delivery" -v

## Follow-ups

Add scheduled orders, substitutions, batching, tips, split settlement, live tracking, and restaurant preparation estimates.
