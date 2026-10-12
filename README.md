# Scope Starter

Scope Starter is a dependency-free, browser-based tool that turns a rough project idea into a focused first-build brief.

## Current status

The tool runs entirely in the visitor's browser. It does not send or store ideas, call an AI model, provide accounts, or offer a hosted API.

## Local preview

Open `dist/index.html` in a browser, or serve `dist/` with any static-file server. No dependency installation or build step is required.

Run the structural verification:

```powershell
./scripts/verify-site.ps1
```

## Deployment

GitHub Pages deployment is configured in `.github/workflows/deploy-pages.yml`. Pull requests are validated; pushes to `main` deploy the static site once GitHub Pages is enabled in repository settings.

`dist/CNAME` records the intended custom hostname, `daddyszone.com`. It does not change DNS. Read [deployment instructions](docs/deployment.md) before enabling the domain.

## License

MIT. See `LICENSE`.

