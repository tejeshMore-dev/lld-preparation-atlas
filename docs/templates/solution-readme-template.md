# Solution Guide Template

Use this public-style teaching flow for every complete problem walkthrough.
Remove a subsection only when it genuinely does not apply.

    # <Problem> Low-Level Design

    ## Understanding the Problem
    ## Requirements
    ### Clarifying Questions
    ### Final Requirements
    ## Core Entities and Relationships
    ## Class Design
    ### Good Solution
    ### Great Solution
    ### Final Class Design
    ## Implementation
    ### Complete Code Implementation
    ## Verification
    ## Extensibility
    ## What Is Expected at Each Level?
    ### Junior
    ### Mid-level
    ### Senior
    ## Interview Walkthrough
    ## Detailed Design Reference

Every guide must answer:

1. What is in scope and explicitly excluded?
2. Which object owns each invariant and mutable fact?
3. What happens when a critical workflow fails halfway through?
4. Which check-and-change must be atomic?
5. How does a likely follow-up fit without rewriting the core?
6. Which tests prove the design?

Explain patterns only when they isolate a named variation or boundary. Tie
examples to the repository's actual implementation when runnable code exists.
