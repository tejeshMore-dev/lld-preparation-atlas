# Connect Four Low-Level Design

Design a two-player game where pieces fall to the lowest free cell and four aligned pieces end the game.

## 1. Understanding the problem

Connect Four is a compact state-machine problem. A good design separates:

- board rules such as gravity and bounds;
- game rules such as turns and lifecycle;
- win evaluation;
- player input and display.

The primary mistakes are allowing illegal moves, checking wins incorrectly, and mixing UI behavior into the domain model.

## 2. Clarifying questions

- Is the board always 6 rows by 7 columns?
- Is the target always four?
- Are exactly two players supported?
- Can players use arbitrary piece symbols?
- Is undo required?
- Should games be persisted or replayed?
- Can commands arrive concurrently from remote clients?
- Is an AI player in scope?

## 3. Final requirements

Version one supports:

1. Configurable rows, columns, and connect length.
2. Exactly two players with distinct pieces.
3. Alternating turns.
4. Gravity-based placement by column.
5. Horizontal, vertical, and diagonal wins.
6. Draw detection when the board is full.
7. Rejection of invalid columns, full columns, wrong turns, and moves after completion.
8. Move history suitable for replay or undo extension.

Networking, matchmaking, persistence, and AI remain optional boundaries.

## 4. Invariants

1. Every piece occupies the lowest free row available at placement time.
2. A cell changes from empty to occupied at most once.
3. Players alternate after each accepted move.
4. Rejected moves do not change the turn.
5. Players use distinct non-empty pieces.
6. A finished game accepts no further moves.
7. The winner is the player whose accepted move first forms the target line.
8. Move-history length equals occupied-cell count.

## 5. Core model

| Type | Important state | Responsibility |
|---|---|---|
| Position | row and column | immutable board coordinate |
| Player | ID/name and piece | game participant |
| Board | dimensions and cells | gravity, placement, capacity, read-only views |
| Move | player, position, sequence | immutable accepted action |
| Game | players, active player, status, history | turn and lifecycle coordinator |
| WinPolicy | target length | evaluates the latest move |
| Renderer | none | presentation outside the domain |

Relationships:

    Game *-- Board
    Game o-- Player
    Game *-- Move
    Game --> WinPolicy
    Renderer --> GameSnapshot

## 6. State model

    NOT_STARTED -> IN_PROGRESS -> WON
                              \-> DRAW
                              \-> ABANDONED

For a small lifecycle, an enum plus guarded methods is clearer than one class per state.

## 7. Board design

Board owns the grid because it has the state needed to enforce gravity.

Useful contract:

    can_play(column) -> bool
    place(piece, column) -> Position
    piece_at(position) -> Piece | None
    is_full() -> bool
    snapshot() -> immutable view

place() validates column bounds and capacity, finds the lowest empty row, mutates exactly one cell, and returns that position.

Do not let Game scan and write Board.cells directly.

### Efficient column lookup

A simple board scans a column from bottom to top: O(rows) per move.

An optional next_open_row[column] index makes placement O(1). The index must change atomically with the cell.

## 8. Win policy

Only lines through the latest move can become winning lines.

Check four direction pairs:

- horizontal: (0, 1) and (0, -1);
- vertical: (1, 0) and (-1, 0);
- rising diagonal: (1, 1) and (-1, -1);
- falling diagonal: (1, -1) and (-1, 1).

For each pair:

    line_length =
        1
        + count_same_piece(forward)
        + count_same_piece(backward)

A line wins when length >= connect_length.

This costs O(K) in each direction for target K, bounded by board dimensions. It is simpler and less error-prone than rescanning the entire board.

## 9. Game design

Game owns:

- the ordered players;
- current turn;
- game status;
- winner;
- move history;
- the play(player_id, column) use case.

play() should either complete one valid state transition or make no change.

Suggested flow:

1. Require IN_PROGRESS.
2. Require the active player.
3. Ask Board to place the player’s piece.
4. Append a Move.
5. Ask WinPolicy whether the position wins.
6. Mark WON, mark DRAW, or advance the turn.
7. Return an immutable MoveResult.

## 10. Move workflow

    Player -> Game: play(playerId, column)
    Game -> Game: validate state and turn
    Game -> Board: place(piece, column)
    Board -> Game: Position
    Game -> WinPolicy: is_winning(board, position, piece)
    WinPolicy -> Game: true/false
    Game -> Game: finish or switch player
    Game -> Player: MoveResult

Validate everything possible before mutation. The only post-placement work should be deterministic state completion that cannot fail under a valid Board contract.

## 11. Invalid operations

| Operation | Result |
|---|---|
| column below zero or beyond width | InvalidColumn |
| column has no empty cell | ColumnFull |
| non-active player moves | WrongTurn |
| move after won/drawn | GameAlreadyFinished |
| duplicate player piece | invalid game construction |
| impossible dimensions/target | invalid game construction |

Domain-specific errors make UI and API translation clearer than generic ValueError.

## 12. Patterns and principles

| Technique | Purpose |
|---|---|
| Strategy | standard, variant, or optimized WinPolicy |
| Value object | Position and Move |
| Encapsulation | Board protects cells; Game protects turns |
| Dependency injection | WinPolicy, ID source, event publisher |
| Snapshot/DTO | expose game state without mutable grid leakage |
| Command | useful only if moves are queued, persisted, or undone |

Visitor, Observer, and State classes are unnecessary for the core game. Events become useful for remote spectators or persistence.

## 13. Undo and replay

If undo is required:

1. pop the last Move;
2. ask Board to clear exactly that position;
3. restore the previous player;
4. recompute or restore status and winner.

Undo is easiest when Move is immutable and Board exposes a controlled revert(move) operation. Do not allow arbitrary cell clearing.

Replay builds a fresh game and reapplies recorded commands, verifying history validity.

## 14. Concurrency

A local two-player UI naturally serializes moves.

For a server:

- serialize commands per game with one lock or actor/queue;
- include expected_move_number in each command;
- reject stale duplicate commands;
- persist game version with optimistic concurrency;
- publish spectator events after the move commits.

The check-turn, place-piece, record-move, and switch/finish sequence is one atomic transition.

## 15. Complexity

For R rows, C columns, and target K:

| Operation | Simple implementation |
|---|---:|
| place piece | O(R), or O(1) with height index |
| win check from latest move | O(R + C), usually O(K) bounded scans |
| full-board check | O(RC), or O(1) with move count |
| render snapshot | O(RC) |
| move-history append | O(1) |

Space is O(RC + M), where M is accepted moves. History can reference positions rather than duplicate board snapshots.

## 16. Verification

Test:

- first piece lands on bottom row;
- pieces stack in one column;
- invalid and full columns;
- wrong player does not lose a turn;
- horizontal win;
- vertical win;
- both diagonal wins;
- moves that contain gaps do not win;
- draw on a small configured board;
- no move after finish;
- connect-K and board configuration validation;
- move history matches the board;
- two simultaneous commands with one expected version produce one winner.

## 17. Extensibility

- **Connect-K:** configure target length in WinPolicy.
- **Different board dimensions:** Board constructor validation already isolates it.
- **AI:** add a PlayerStrategy that selects a command from an immutable snapshot.
- **Network play:** place an application service and repository around Game.
- **Spectators:** publish GameMoved and GameFinished events.
- **Timers:** inject Clock and add per-turn deadlines to Game.
- **Variants:** swap gravity/placement policy only if the placement rule truly varies.

## 18. Trade-offs

- A 2D list is easy to explain; bitboards are faster but obscure an interview design.
- Scanning columns is sufficient for small boards; a height index is an optimization.
- Keeping history duplicates some information but enables replay, audit, and undo.
- Enum state is simpler than State classes at this lifecycle size.
- Returning a copied snapshot costs O(RC) but protects encapsulation.

## 19. Interview expectations

### Junior

Produce Board, Player, and Game with legal placement, turns, and at least horizontal/vertical win checks.

### Mid-level

Separate Board and Game invariants, cover all directions, return clear errors, and write focused tests.

### Senior

Discuss configurable rules, atomic command processing, optimistic versions, replay/undo, and why a simple model is preferable to premature optimization.

## 20. Interview walkthrough

1. Fix board size, connect length, and player count.
2. State gravity, alternating-turn, and terminal-state invariants.
3. Put placement inside Board and turn lifecycle inside Game.
4. Explain latest-move directional win checking.
5. Implement play() as one transition.
6. Test every win direction and an invalid move.
7. Add concurrency or AI only as a follow-up seam.
