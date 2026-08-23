$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$solutions = @(
    "airline-reservation",
    "atm",
    "cab-booking",
    "coupon-management-and-distribution-platform",
    "elevator",
    "food-delivery",
    "hotel-management",
    "library-management",
    "movie-ticket-booking",
    "parking-lot",
    "splitwise"
)

Push-Location $repositoryRoot
try {
    foreach ($solution in $solutions) {
        $solutionRoot = "solutions/$solution"
        $testRoot = "$solutionRoot/tests"

        Write-Host "Testing $solution"
        & python -m unittest discover -s $testRoot -t $solutionRoot -v
        if ($LASTEXITCODE -ne 0) {
            throw "Test suite failed: $solution"
        }
    }
}
finally {
    Pop-Location
}

Write-Host "All solution test suites passed."
