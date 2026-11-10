# Related knowledge sources (phase 1)

TeamOps AI chat now offers an expandable **Related knowledge sources** section below each assistant answer, including reopened historical conversations.

## Behavior

- Clicking the control retrieves up to five matching Knowledge Base chunks for the preceding user question using the authenticated `POST /knowledge` endpoint.
- Shows a human-readable document filename, S3 URI, retrieval score where available, and a bounded excerpt.
- Fetches **only on demand**, not on every model response, to avoid unnecessary retrieval costs.
- Never links S3 URIs directly (private S3 objects are not generally accessible in browsers).
- If the knowledge lookup fails, the model answer remains available and users can retry.
- No DynamoDB history schema change is required.

## Important provenance limitation

These are **independently retrieved related documents**, NOT trace-backed citations proving that the AgentCore Harness used these particular chunks when generating its answer. The UI explicitly discloses this. True answer-level citations require instrumenting the Harness tool calls, capturing the exact retrieval events/identifiers used in generation, and returning these in an authenticated structured response.

## Validation and rollout

From the feature branch checkout:

```bash
cd web && npm ci && npm run build && npm audit
```

Check that an approved Cognito user can sign in, ask an SOP question, expand the sources under the reply, view matching source excerpts, and reopen the conversation to repeat the lookup. Verify unavailable KB retrieval is gracefully handled. The knowledge endpoint remains restricted by the existing `teamops-users` backend group gate.

**Branch note:** Based on `feature/cognito-self-signup-and-approval`, which contains the signup work already deployed manually. Merge or bring those commits into main before merging this feature there.
