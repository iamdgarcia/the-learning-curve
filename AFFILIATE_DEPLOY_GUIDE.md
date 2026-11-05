# Netlify Affiliate Link Integration Guide

## How Netlify Affiliate Tracking Works with Deploy Buttons

Netlify's affiliate program tracks referrals through URL parameters. When users click your affiliate link and sign up/deploy, you earn commission.

## Deploy Button with Affiliate Tracking

Replace `YOUR_AFFILIATE_ID` with your actual Netlify affiliate ID:

```markdown
[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://join.netlify.com/bxmfy8pxswau-w6zrwt)
```

## Template Implementation Examples

### 1. Documentation Site Template (MkDocs)
**README.md snippet:**
```markdown
# Agentic AI Course Documentation Template

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://join.netlify.com/bxmfy8pxswau-w6zrwt)

## Features
- MkDocs with Material theme
- Full course content structure
- Search & mobile responsiveness
- Automatic GitHub Actions deployment
```

### 2. Interactive Learning Platform Template
**README.md snippet:**
```markdown
# Agentic AI Interactive Learning Platform

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://join.netlify.com/bxmfy8pxswau-w6zrwt)

## Features
- Student progress tracking
- Embedded code executors
- Exercise submission system
- Video course integration
```

### 3. Agent Showcase Template
**README.md snippet:**
```markdown
# Agent Pattern Showcase & Demo

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://join.netlify.com/bxmfy8pxswau-w6zrwt)

## Features
- Live demos of all agent types (planning, reflective, router, etc.)
- Source code browser
- Interactive configuration playground
- Deployment templates for each agent pattern
```

## GitHub Actions Workflow (Unaffected)
Your existing GitHub Actions CI/CD remains unchanged - the affiliate tracking only affects the initial deployment trigger:

```yaml
# .github/workflows/netlify.yml
name: Deploy to Netlify

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Install Dependencies
      run: npm ci
    - name: Build Site
      run: npm run build
    - name: Deploy to Netlify
      uses: nwtgck/actions-netlify@v2
      with:
        publish-dir: ./public
        production-branch: main
        github-token: ${{ secrets.GITHUB_TOKEN }}
        deploy-message: "Deploy from GitHub Actions"
        enable-publish-commit: true
        overwrites-publish-commit: true
        netlify-auth-token: ${{ secrets.NETLIFY_AUTH_TOKEN }}
        netlify-site-id: ${{ secrets.NETLIFY_SITE_ID }}
        netlify-algorithm: rolling
```

## Implementation Steps

1. **Get Your Affiliate ID**
   - Log in to your Netlify affiliate dashboard
   - Find your unique affiliate ID

2. **Create Template Repositories**
   - Fork or create new repos for each template type
   - Add the affiliate-linked deploy button to README.md

3. **Set Up GitHub Secrets**
   - In each template repo, add Netlify credentials as secrets:
     - `NETLIFY_AUTH_TOKEN`
     - `NETLIFY_SITE_ID`

4. **Test the Flow**
   - Click the deploy button in your README
   - Verify it redirects through your affiliate link
   - Confirm GitHub Actions workflow triggers on deploy

## Tracking & Optimization

- Monitor affiliate conversions in Netlify affiliate dashboard
- A/B test different template presentations
- Consider creating template-specific landing pages that explain benefits before deployment
- Update affiliate ID in all templates if it changes

## Legal & Best Practices

- Disclose affiliate relationship if required by local regulations
- Ensure templates provide genuine value independent of affiliate incentive
- Keep template repos updated with latest course content
- Provide clear documentation for template customization