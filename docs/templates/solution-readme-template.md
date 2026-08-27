# Solution Guide Template

Use this short shape for every problem.

    # <Problem>

    <One sentence describing the core design pressure.>

    ## Scope

    Core behavior and explicit exclusions.

    ## Model

    | Type | Responsibility |
    |---|---|

    State the key invariant.

    ## Critical flow

    Trace one command from input to result, including its main failure.

    ## Design choices

    Explain only abstractions that isolate a named change or boundary.

    ## Correctness

    Name the atomic check-and-change, failure ordering, and retry behavior.

    ## Run

    Add demonstration and test commands when code exists.

    ## Follow-ups

    List three realistic changes and where each belongs.

A guide is complete when a reader can answer: what is in scope, who owns each rule, what fails halfway through, and where the next change goes.
