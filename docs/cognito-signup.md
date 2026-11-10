# Cognito self-registration and admin approval

This feature adds a custom signup flow to TeamOps AI while keeping operational endpoints private.

## User experience

1. **Create account:** Register an email and password using Amazon Cognito public SignUp API.
2. **Verify email:** Confirm the signup using the emailed code, with resend support.
3. **Sign in:** Both existing username-based Cognito accounts and newly created email-named accounts are supported.
4. **Request access:** Confirmed but unapproved accounts see a pending-approval screen; they are not auto-enrolled in the teamops-users group.
5. **Forgot password:** Request an email reset code and set a new password.
6. **First-time sign in:** Existing administrator-created accounts can complete the NEW_PASSWORD_REQUIRED challenge.

## Security boundary

- The Chat API and history routes now **require** a Cognito ID-token group claim containing `teamops-users`, in addition to a valid HTTP API JWT authorizer identity. Previously the Chat API only checked `sub`.
- Dashboard API already requires `teamops-users`.
- The frontend also checks group membership, but backend checks are authoritative.
- **Sign-up never adds users to the group.** An admin must grant access after verifying the requester.
- Cognito self-registration is public: anyone who discovers the public client can create *unapproved* user-pool accounts when enabled. Monitor abuse, signup quotas, and email costs; consider invitation-only onboarding instead if appropriate.
- Do not place AWS credentials or client secrets in the browser.
- The UI does not currently support MFA challenges. Do not enable required MFA before adding the associated UI support.

## Configuration before testing signup

AWS Console -> Cognito -> User pools -> `ap-southeast-2_m2kScaTa8` (region `ap-southeast-2`):

- **Sign-up** -> **Self-service sign-up** -> **Enable self-registration** (only after reviewing public registration implications).
- **Sign-up** -> **Attribute verification and user account confirmation** -> configure Cognito-assisted email verification and ensure that `email` is a required / readable attribute.
- Confirm the existing app client `1r0se3b4uieonrfnqj30lt3kd7` is a public app client with no secret, accepts password sign-in, and permits self-registration.
- Check Cognito email delivery / sending quotas and password policy.
- Check whether email values are valid usernames in the configured pool. The UI creates new accounts with username=email; changing existing pool sign-in identifiers may not be possible in place.

**Do not enable self-registration until the backend group authorization change is deployed**. Otherwise any newly confirmed user could access the old Chat API using their Cognito token.

## Deploy order

1. `sam validate --lint && sam build` and `sam deploy` the backend first, with the existing stack name, region, Harness ARN and Knowledge Base ID.
2. Verify that an existing `teamops-users` member can chat and retrieve history and that a newly confirmed, non-member test account gets HTTP 403 from `POST /chat` and `GET /conversations`.
3. Check `cd web && npm ci && npm run build && npm audit` against this feature branch.
4. Deploy web/dist to the existing CloudFront-backed frontend bucket, invalidate CDN; test existing demo account login.
5. Enable Cognito self-registration and test create -> verify email -> pending approval.
6. After manual review, an admin grants group membership using a privileged terminal:

```bash
aws cognito-idp admin-add-user-to-group \
  --region ap-southeast-2 \
  --user-pool-id ap-southeast-2_m2kScaTa8 \
  --username 'NEW_USER_EMAIL' \
  --group-name teamops-users
```

The user signs out and signs back in to refresh their ID token after approval.

## Limitations and follow-ups

- Email verification uses Cognito-confirmed account state, not administrator approval. They are separate steps.
- Public registration requires anti-abuse monitoring. Consider AWS WAF / Cognito threat protection and account creation restrictions.
- Reset flow requires a verified recovery email.
- Existing users retain username-based login; new users use email as username.
- This feature does not build an admin approval dashboard or send approval notifications; admins review and approve in the Cognito console/CLI.
- Use a separate test account to validate complete end-to-end flows before enabling general registration.
