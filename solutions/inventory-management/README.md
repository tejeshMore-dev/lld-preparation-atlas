# Inventory Management

Design stock tracking across warehouses without overselling reserved units.

## Scope

Support products, warehouses, stock receipt, reservation, release, shipment, and adjustment. Purchasing, forecasting, and carrier integration are outside the core.

## Model

| Type | Responsibility |
|---|---|
| SKU | stable product identity |
| StockItem | on-hand and reserved quantity for one SKU/location |
| Reservation | requested lines, expiry, and lifecycle |
| Warehouse | owns its stock items |
| AllocationPolicy | chooses locations for requested quantity |
| InventoryService | coordinates multi-item workflows |
| StockMovement | immutable audit entry |

For every stock item:

    available = on_hand - reserved
    0 <= reserved <= on_hand

Do not store available separately; derive it.

## Critical flow: reserve

1. Validate positive requested quantities.
2. Load candidate stock items.
3. Ask the allocation policy for a plan.
4. Atomically increase reserved quantities.
5. Create an expiring reservation and movement records.
6. Return the allocation or an insufficient-stock error.

Shipment reduces both on-hand and reserved. Release reduces only reserved. Adjustments record a reason.

## Design decisions

- StockItem owns quantity invariants.
- Reservation owns lifecycle and line allocations.
- AllocationPolicy isolates single-warehouse versus split fulfillment.
- A ledger provides auditability; current balance remains optimized state.
- Clock and ID generation are injected.

## Correctness

Each conditional reservation should update only when available quantity is sufficient. A version column or conditional database statement prevents lost updates. Multi-SKU all-or-nothing reservation needs one transaction or explicit compensation.

Expiry workers must be idempotent: releasing an already closed reservation changes nothing.

## Follow-ups

- Lots, batches, and expiry dates.
- Safety stock and backorders.
- Transfers between warehouses.
- Event-driven replenishment.
- Reconciliation of ledger and balance.

## Interview finish

Implement StockItem.reserve/release/ship, Reservation transitions, one allocation policy, and tests for oversell, repeated release, partial fulfillment, and expiry.
