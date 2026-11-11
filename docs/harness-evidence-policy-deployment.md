# Updating AgentCore Harness safely

This PR contributes **prompt guidance plus a manual acceptance matrix**, not live AWS changes. No Lambda or CloudWatch IAM changes are included.

## Copy/paste workflow
1. In the Bedrock AgentCore Console, open the existing TeamOps Harness and **back up the current system prompt** (including authorization, memory and Gateway behavior).
2. Review `prompts/evidence-grounded-rca-system.md`. It is below the 20,000-character limit; merge its evidence-specific rules into your existing prompt if your current instructions contain additional essential policies.
3. Save/update the Harness prompt. Retain all existing Gateway targets and tool schemas.
4. Start a new conversation and run the cases in `docs/evidence-grounded-rca-qa.md`.
5. Compare actual tool traces against answers and verify that the known demo failure is attributed to `--demo-mode fail`.

## Local static check (single-line CloudShell command)
```bash
cd ~/teamops-signup && python3 -m unittest -v tests/test_evidence_prompt_contract.py
```

## Known limitations
- System prompting is advisory, not a deterministic proof of evidence. The app currently does not have a structured evidence pipeline or a machine-enforced RCA validator.
- Robust enforcement would require collecting verified tool outputs into structured records, applying schema validation and provenance checks before presenting operational claims.
- Never assume an AgentCore update is active simply because a GitHub branch was pushed.
