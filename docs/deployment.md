# Deployment notes

This site is a dependency-free static page, so GitHub Pages is the simplest deployment target. The workflow in this repository uses the official GitHub Pages actions and deploys only after changes reach `main`.

## First deployment

1. Merge the reviewed pull request.
2. In GitHub, open **Settings → Pages** and select **GitHub Actions** as the source.
3. Open the Actions run named **Deploy GitHub Pages** and confirm it completes.
4. Open the URL reported by the deployment job and verify the page before considering any domain change.

GitHub Pages does not provide a built-in pull-request preview URL for this workflow. The pull-request job validates the static artifact. For a hosted preview URL, connect the same branch to Vercel or Netlify; do not change the production DNS until the preview is approved.

## Custom domain: daddyszone.com

The `dist/CNAME` file records the intended hostname, `daddyszone.com`, but does not alter DNS. With this repository's custom GitHub Actions workflow, GitHub Pages ignores a `CNAME` file; the domain must instead be entered manually in **Settings → Pages → Custom domain** after the deployment is verified. Do not do that until the preview is approved and you are ready to replace the website currently served at that exact hostname.

At cutover, set these four `A` records for host `@` / `daddyszone.com` to GitHub Pages:

| Type | Host | Value |
| --- | --- | --- |
| A | @ | `185.199.108.153` |
| A | @ | `185.199.109.153` |
| A | @ | `185.199.110.153` |
| A | @ | `185.199.111.153` |

For IPv6 support, also set `AAAA` records for `@` to `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, and `2606:50c0:8003::153`. If you also want `www`, create a `CNAME` for `www` to `daddyszone.github.io` (with no repository path). GitHub recommends configuring both the apex and `www` variants for HTTPS redirects.

Only replace web-serving `A`, `AAAA`, or web `CNAME` records for the hostname being moved. Keep all MX, SPF, DKIM, DMARC, MTA-STS, and any other email records unchanged. Keep the GitHub-provided domain-verification TXT record once you have verified the domain. DNS changes will cause `daddyszone.com` to stop resolving to the existing website and start resolving to GitHub Pages after propagation; they cannot make both sites serve the same hostname simultaneously.

## HTTPS and rollback

After DNS is correct, enable **Enforce HTTPS** in GitHub Pages. GitHub provisions the certificate after it verifies the domain.

To roll back, restore the previous website's web DNS records (not mail records) and wait for DNS propagation. For an application rollback while retaining GitHub Pages, revert the deployment commit and let the workflow redeploy the prior static artifact.

