# Spec changes log

Every change to the original project spec, with the reason. Honest method notes like
this are part of what makes the project credible.

| ID | Change | Reason | Status |
|----|--------|--------|--------|
| A1 | Add the action outcome `success` as a Stage 2 model feature | The original feature list did not let the model see whether an action worked, so a failed and a successful pass with identical coordinates looked identical and "intercepted pass = large negative Value" could not happen. Standard "result" feature in VAEP. | Approved |
| A2 | Allow the `requests` library for the data pipeline (Stage 1b) | Needed to fetch the data over HTTP directly. | Approved |
| A3 | Permission to add other necessary libraries, announced each time and logged here | Keeps the work smooth while keeping the method section accurate. | Approved |
| A4 | Keep the yes/no "shot in next 10 events" label; also run it with 5 and 15 events | Shows the findings do not depend on one arbitrary window length. | Approved |
| A5 | Also test the gamble threshold at 5 and 15 pitch units (main definition stays 10) | Robustness check on the 10-unit definition. | PENDING approval |

## Points to settle at Stage 2 (spec is ambiguous)
- Does "next 10 events" count events after filtering to the kept types, or in the full event stream?
- Exact definition of the goal-difference feature.
- Handling of V_prev for the first event of a possession.
