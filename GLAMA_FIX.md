# Glama "Cannot be installed" — Root cause and fix

## Root cause

On [Glama’s score page](https://glama.ai/mcp/servers/@MichaelWeed/atlas-g-protocol/score) the blocker is:

- **"Server not inspectable"** → "Claim this server to enable inspection and installation."
- **"Only inspectable servers can be installed."**

So the listing and sync work (README, repo link, glama.json are fine). Installation is disabled until the server is **claimed** and becomes **inspectable**.

Lemon Squeezy is under **IntrepidServicesLLC** and was set up with create → add repo → sync; the account that created it was almost certainly used to **claim** it (or the org flow was completed). For Atlas-G under **MichaelWeed**, the server was never fully claimed, so it never became installable.

## Fix (claim the server)

1. **Claim via GitHub (recommended)**  
   Open this link **while logged out of Glama** (or in an incognito window), then sign in with **MichaelWeed** when prompted:
   - https://glama.ai/oauth/github/auth?returnPath=%2Fmcp%2Fservers%2F%40MichaelWeed%2Fatlas-g-protocol  

   Complete the GitHub OAuth flow. That should mark the server as claimed and trigger inspection.

2. **If the server is under an org**  
   Glama says: add `glama.json` with a `maintainers` array, then authenticate. Atlas-G already has `glama.json` with `"maintainers": ["MichaelWeed"]` and is under your user, so the org flow does not apply; step 1 is enough.

3. **After claiming**  
   - Use **Sync Server** in the [admin interface](https://glama.ai/mcp/servers/@MichaelWeed/atlas-g-protocol/admin) so Glama re-scans the repo.  
   - Recheck the [score page](https://glama.ai/mcp/servers/@MichaelWeed/atlas-g-protocol/score). When the server becomes **inspectable**, "Install Server" should work.

## What was changed in the repo

- **package.json**  
  - Added `repository`: `{ "type": "git", "url": "https://github.com/MichaelWeed/atlas-g-protocol.git" }` so the repo is explicit for Glama/npm-style tooling (same idea as Lemon Squeezy). No other format or structural changes.

## Summary

| Item              | Lemon Squeezy              | Atlas-G (before fix)     |
|-------------------|----------------------------|---------------------------|
| Glama listing     | Yes                        | Yes                       |
| Sync / README     | Works                      | Works                     |
| package.json repo | Has `repository`           | Was missing → **added**   |
| Claimed / inspectable | Yes (so install works) | No → **claim via OAuth**  |

**Action:** Claim the server with the link in step 1, then sync. No further repo changes required for “cannot be installed” once Glama marks it inspectable.
