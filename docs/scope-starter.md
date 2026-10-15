# Scope Starter

Scope Starter is a dependency-free browser tool that turns a rough project idea into a focused first-build brief.

It runs entirely in the visitor's browser. It does not send or store ideas, call an AI model, provide accounts, or offer a hosted API.

## Local preview

Open `dist/index.html` in a browser, or serve `dist/` with a static-file server. No dependency installation or build step is required.

Run the structural verification with PowerShell:

```powershell
./scripts/verify-site.ps1
```

## Deployment

GitHub Pages deployment is configured in `.github/workflows/deploy-pages.yml`. Pull requests are validated; pushes to `main` deploy the site when Pages is enabled.

`dist/CNAME` records the intended custom hostname. It does not change DNS. See [deployment instructions](deployment.md) before enabling the domain.

## License

MIT. See [LICENSE](../LICENSE).
