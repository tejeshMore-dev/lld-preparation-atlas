# Solution Guide Template

Use this structure for a complete problem walkthrough. Remove a section only
when it genuinely does not apply.

    # <Problem> Low-Level Design

    ## 1. Understanding the problem
    ## 2. Clarifying questions
    ## 3. Final requirements
    ## 4. Invariants
    ## 5. Core model and relationships
    ## 6. State and lifecycle
    ## 7. Class design
    ## 8. Critical workflow one
    ## 9. Critical workflow two
    ## 10. Patterns and principles
    ## 11. Failure handling
    ## 12. Concurrency and consistency
    ## 13. Complexity
    ## 14. Verification and tests
    ## 15. Code map or implementation contracts
    ## 16. Extensibility
    ## 17. Trade-offs
    ## 18. Interview expectations
    ## 19. Interview walkthrough

Every guide must answer:

1. What is in scope and explicitly excluded?
2. Which object owns each invariant and mutable fact?
3. What happens when a critical workflow fails halfway through?
4. Which check-and-change must be atomic?
5. How does a likely follow-up fit without rewriting the core?
6. Which tests prove the design?

Explain patterns only when they isolate a named variation or boundary. Tie
examples to the repository's actual implementation when runnable code exists.
