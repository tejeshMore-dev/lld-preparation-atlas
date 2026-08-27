# Connect Four

Design a two-player game where pieces fall into columns and four aligned pieces win.

## Scope

Support a configurable board, two players, legal moves, win detection, draw detection, and move history. Networking, matchmaking, and persistence are optional boundaries.

## Model

| Type | Responsibility |
|---|---|
| Position | immutable row and column |
| Board | grid, valid placement, and capacity |
| Player | identity and piece |
| Game | turn order, lifecycle, history, and result |
| WinPolicy | decides whether the latest move wins |
| Move | player, position, and sequence number |

Key invariants: pieces occupy the lowest free row; turns alternate; no move is accepted after the game ends.

## Critical flow: drop a piece

1. Reject the move if the game is finished or the wrong player acts.
2. Ask Board to place the piece in the requested column.
3. Record the move.
4. Ask WinPolicy about lines through the new position.
5. Mark won, drawn, or switch the active player.

Only the latest position needs checking. Count equal pieces in both directions for horizontal, vertical, and two diagonals.

    length = 1 + count(direction) + count(opposite)

A length of at least four wins.

## Design decisions

- Board owns gravity and bounds because it owns the grid.
- Game owns turns and lifecycle.
- WinPolicy isolates variants such as different connect lengths.
- An enum is enough for game state; State classes would be unnecessary here.
- Store a move history if undo, replay, or audit is required.

## Correctness

A move is one state transition. If remote players can submit concurrently, serialize commands per game and optionally include the expected move number.

Validate configuration: positive dimensions, distinct pieces, and a connect length that can fit the board.

## Follow-ups

- NxM board with connect-K.
- Undo the last move.
- Add an AI PlayerStrategy.
- Save and replay games.
- Spectator event stream.

## Interview finish

Implement Board.place(), Game.play(), directional win checking, and tests for full columns, wrong turns, all four win directions, and draw.
