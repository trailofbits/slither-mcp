# GitHub Repository Setup Guide

This document provides a checklist for configuring the GitHub repository after initial publication.

## Repository Settings

### Basic Information

- [ ] Add repository description: "MCP server for Slither static analysis of Solidity smart contracts"
- [ ] Add repository topics/tags:
  - `mcp`
  - `model-context-protocol`
  - `slither`
  - `solidity`
  - `static-analysis`
  - `smart-contracts`
  - `ethereum`
  - `security`
  - `python`

### Features

- [ ] Enable Issues
- [ ] Enable Discussions (recommended for Q&A and community support)
- [ ] Disable Wiki (documentation is in-repo)
- [ ] Disable Projects (unless planning to use GitHub Projects)

### Branch Protection Rules

Configure protection for `main` branch:

- [ ] Require pull request reviews before merging
  - [ ] Required approvals: 1
- [ ] Require status checks to pass before merging
  - [ ] Require branches to be up to date before merging
  - [ ] Status checks: `test` workflow
- [ ] Require conversation resolution before merging
- [ ] Do not allow bypassing the above settings

### GitHub Pages (Optional)

If you want to host documentation:

- [ ] Enable GitHub Pages
- [ ] Source: Deploy from a branch
- [ ] Branch: `gh-pages` or `docs/` folder on main
- [ ] Configure custom domain (if applicable)

## Release Process

### Creating a Release

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Commit changes: `git commit -m "Release v0.x.0"`
4. Create and push tag: `git tag v0.x.0 && git push origin v0.x.0`
5. Create GitHub release from tag
6. Add release notes from CHANGELOG
7. Publish to PyPI (if configured)

### GitHub Release Configuration

- [ ] Set up release automation (optional)
- [ ] Configure release notes template
- [ ] Enable automatic changelog generation

## Integrations

### GitHub Actions Secrets

If publishing to PyPI:

- [ ] Add `PYPI_API_TOKEN` secret for package publishing
- [ ] Add `TEST_PYPI_API_TOKEN` for testing releases

### Security

- [ ] Enable Dependabot security updates
- [ ] Enable Dependabot version updates
- [ ] Configure security policy (SECURITY.md already exists)
- [ ] Enable private vulnerability reporting

### Community Health Files

Current status:
- [x] LICENSE (MIT)
- [x] README.md
- [ ] CONTRIBUTING.md (create if needed)
- [ ] CODE_OF_CONDUCT.md (create if needed)
- [x] Issue templates
- [x] Pull request template

## Monitoring

### Insights to Review Regularly

- [ ] Check "Traffic" for visitor analytics
- [ ] Monitor "Issues" and "Pull Requests" activity
- [ ] Review "Community" health metrics
- [ ] Track "Security" advisories and Dependabot alerts

## Additional Considerations

### Sponsorship (Optional)

- [ ] Set up GitHub Sponsors
- [ ] Add FUNDING.yml with sponsor links

### Social

- [ ] Share release on relevant platforms (Twitter, Reddit, etc.)
- [ ] Add to awesome lists (e.g., awesome-ethereum-security)
- [ ] Submit to MCP server directory (when available)

### Documentation

- [ ] Ensure all links in README work
- [ ] Verify installation instructions are accurate
- [ ] Add examples and tutorials (if needed)
- [ ] Create video demo or walkthrough (optional)

## Post-Publication Checklist

After pushing to GitHub:

1. [ ] Verify GitHub Actions workflows run successfully
2. [ ] Test installation from GitHub: `uvx --from git+https://github.com/trailofbits/slither-mcp slither-mcp`
3. [ ] Verify badges in README render correctly
4. [ ] Check that issue templates appear correctly
5. [ ] Test PR template by creating a draft PR
6. [ ] Review repository on mobile/different browsers
7. [ ] Announce release to relevant communities

## Maintenance

### Regular Tasks

- [ ] Respond to issues within 48 hours
- [ ] Review and merge PRs promptly
- [ ] Update dependencies quarterly
- [ ] Release new versions following semantic versioning
- [ ] Keep documentation up to date
- [ ] Monitor Sentry metrics (if metrics enabled)

### Long-term Goals

- [ ] Achieve 100+ stars
- [ ] Build contributor community
- [ ] Integrate with popular MCP clients
- [ ] Expand test coverage
- [ ] Performance benchmarking and optimization

