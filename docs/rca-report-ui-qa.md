# TeamOps AI — RCA presentation QA

## Scope
Frontend-only presentation of existing assistant messages. No new Lambda, DynamoDB, API Gateway, or tool-trace endpoint. **Source tags are based on displayed text, not proof of tool execution.** Recovery checkboxes are local UI notes only and never stored, approved or executed in AWS.

## Manual checks
1. Sign in through Cognito and open existing chat history. An ordinary greeting remains unchanged.
2. Ask for a structured Glue failure RCA with headings: Observed evidence, Confirmed root cause, Knowledge Base guidance, Recovery / next actions, Verification status. It renders collapsible cards.
3. Expand/collapse evidence and verify complete Glue run IDs, CloudWatch log excerpts, timestamps and Markdown tables remain visible.
4. Check a proposed recovery item. Confirm no AWS call runs, approval appears, or permanent state persists after refresh.
5. Expand 'View complete original response' and confirm no content was lost during heading extraction.
6. Confirm Related knowledge sources still opens separately and clearly states those sources are not citations.
7. Verify customer-ingestion dashboard, KB search, chat send/history/delete, Cognito sign-in/sign-out.
8. Test desktop and narrow mobile view.
9. If the assistant responds with unstructured prose or one matching heading, it should use the ordinary Markdown display.
10. Run `cd ~/teamops-signup/web && npm ci && npm run build` before deployment. The UI has not been live-tested by this PR.

## Deferred backend improvement
Reliable RCA proof requires structured Lambda/AgentCore trace metadata with a source provenance field, not text detection. Persistent recovery tracking requires authenticated, access-controlled storage and authorization checks. This PR deliberately does neither.
