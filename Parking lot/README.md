# Parking Lot System Design (Python)

## Overview

This project is a production-style Low-Level Design (LLD) implementation
of a Parking Lot system using Object-Oriented Programming, SOLID
principles, and Design Patterns.

It demonstrates how to design software by separating **data**,
**behavior**, and **workflow orchestration**.

------------------------------------------------------------------------

# Architecture

    main.py
       │
       ▼
    ParkingLot (Orchestrator)
       ├── ParkingFloor
       │      └── ParkingSpot
       ├── SpotAllocationStrategy
       ├── PricingStrategy
       ├── PaymentProcessor
       ├── Ticket
       └── Receipt

------------------------------------------------------------------------

# Core OOP Concepts

## 1. Classes & Objects

-   Vehicle
-   ParkingSpot
-   ParkingFloor
-   Ticket
-   Receipt
-   ParkingLot

## 2. Encapsulation

Objects manage their own state. Examples: - `ParkingSpot.assign()` -
`ParkingSpot.vacate()`

## 3. Abstraction

High-level modules work with interfaces (`PricingStrategy`,
`PaymentProcessor`) instead of implementation details.

## 4. Composition

Examples: - ParkingSpot has a Vehicle - Ticket has a Vehicle and
ParkingSpot

## 5. Aggregation

ParkingFloor contains many ParkingSpots.

## 6. Polymorphism

ParkingLot calls: - `strategy.select()` - `pricing.compute_fee()` -
`payment_processor.pay()`

without knowing the concrete implementation.

------------------------------------------------------------------------

# SOLID Principles

## S --- Single Responsibility Principle

Every class has one responsibility.

## O --- Open/Closed Principle

New pricing and allocation algorithms can be added without modifying
existing code.

## L --- Liskov Substitution Principle

Any implementation of the strategy interfaces can replace another.

## I --- Interface Segregation Principle

Small focused interfaces: - `select()` - `compute_fee()` - `pay()`

## D --- Dependency Inversion Principle

ParkingLot depends on abstractions, not concrete classes.

------------------------------------------------------------------------

# Design Patterns Used

## Strategy Pattern

Used for: - Spot Allocation - Pricing

Benefit: - Easily swap algorithms.

Examples: - NearestFirstStrategy - BestFitStrategy - HourlySlabStrategy

------------------------------------------------------------------------

## Decorator Pattern

Used to add pricing behavior dynamically.

Example:

    HourlyPricing
          ↓
    WeekendDecorator
          ↓
    HolidayDecorator

Benefit: - Avoids class explosion.

------------------------------------------------------------------------

## Dependency Injection

Dependencies are created in `main.py` and injected into `ParkingLot`.

Benefit: - Loose coupling - Easier testing - Easy replacement of
implementations

------------------------------------------------------------------------

## Orchestrator Pattern

ParkingLot coordinates the workflow but delegates business logic.

------------------------------------------------------------------------

# Thread Safety

Uses:

-   `threading.Lock`

Purpose: - Prevent race conditions when multiple vehicles enter or exit
simultaneously.

------------------------------------------------------------------------

# Workflow

## Vehicle Entry

    Vehicle
       ↓
    ParkingLot
       ↓
    ParkingFloor
       ↓
    Allocation Strategy
       ↓
    ParkingSpot
       ↓
    Ticket

## Vehicle Exit

    Ticket
       ↓
    Pricing Strategy
       ↓
    Payment Processor
       ↓
    Receipt
       ↓
    Spot Vacated

------------------------------------------------------------------------

# Data Structures

-   List → Floors, Parking Spots
-   Dictionary → Ticket lookup (O(1))
-   Enum → VehicleType, SpotType, PaymentMethod, Statuses
-   Dataclass → Domain models

------------------------------------------------------------------------

# Python Features Used

-   dataclasses
-   Enum
-   ABC & @abstractmethod
-   Optional
-   Type hints
-   UUID
-   datetime
-   math.ceil
-   threading.Lock

------------------------------------------------------------------------

# Folder Structure

    parking_lot/
    │
    ├── models/
    ├── strategies/
    ├── services/
    ├── exceptions/
    ├── tests/
    └── main.py

------------------------------------------------------------------------

# Key Interview Takeaways

-   Model the domain before writing code.
-   Prefer Composition over Inheritance.
-   Separate business rules using Strategy Pattern.
-   Add optional behavior using Decorator Pattern.
-   Inject dependencies instead of creating them internally.
-   Keep orchestration separate from business logic.
-   Program to interfaces, not implementations.
-   Make classes follow SRP.
-   Design for extension, not modification.

------------------------------------------------------------------------

# Possible Enhancements

-   Observer Pattern
-   Factory Pattern
-   State Pattern
-   Custom Exceptions
-   Logging
-   REST API (FastAPI)
-   Database Persistence
-   Unit Tests (pytest)
-   Authentication & Authorization
-   Multi-level Reservations

------------------------------------------------------------------------

# Learning Outcomes

After completing this project, you should understand:

-   Object-Oriented Programming
-   SOLID Principles
-   Layered Architecture
-   Strategy Pattern
-   Decorator Pattern
-   Dependency Injection
-   Thread Safety
-   Domain-Driven Design Basics
-   Low-Level System Design Fundamentals
