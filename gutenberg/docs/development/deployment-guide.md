---
sidebar_position: 4
---

# GitHub Pages Deployment

Learn how to deploy the Varga AI documentation site to GitHub Pages using automated GitHub Actions workflow.

## Overview

This guide explains how to set up automated deployment of the Docusaurus documentation site to GitHub Pages. The setup includes automated builds, pull request validation, and seamless deployment on every push to the main branch.

## Quick Setup

### 1. Update Repository Configuration

Update your Docusaurus configuration for GitHub Pages deployment:

1. **Edit Docusaurus Config**: Open `gutenberg/docusaurus.config.ts` and update these values:
   
   ```typescript title="gutenberg/docusaurus.config.ts"
   const config: Config = {
     // ... other config
     url: 'https://YOUR_GITHUB_USERNAME.github.io',
     baseUrl: '/varga-ai/',
     organizationName: 'YOUR_GITHUB_USERNAME',
     projectName: 'varga-ai',
     // ... rest of config
   };
   ```

2. **Replace placeholder values**:
   - Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username
   - Replace `varga-ai` with your repository name if different
   - Ensure the `baseUrl` matches your repository name with leading and trailing slashes

### 2. Enable GitHub Pages

1. Navigate to your repository on GitHub
2. Go to **Settings** > **Pages**
3. Under **Source**, select **GitHub Actions**
4. The workflow will automatically deploy when you push to the main branch

:::tip
No additional configuration is needed once you select "GitHub Actions" as the source. The workflow file handles all the deployment logic.
:::

### 3. Deployment Workflow

The GitHub Actions workflow (`.github/workflows/deploy-docs.yml`) provides:

**Trigger Conditions:**
- Push to main/master branch (only when `gutenberg/` folder changes)
- Manual workflow dispatch from Actions tab
- Pull requests (build validation only, no deployment)

**Build Process:**
- Sets up Node.js 20 environment
- Installs dependencies with `npm ci` for consistent builds
- Builds the Docusaurus site with `npm run build`
- Deploys to GitHub Pages using official GitHub Pages action

**Advanced Features:**
- **Smart triggering**: Only runs when documentation files change
- **Pull request validation**: Builds PRs to catch issues before merge
- **Concurrent deployment protection**: Prevents simultaneous deployments
- **Automatic comments**: Posts build status on pull requests

### 4. First Deployment

Follow these steps for your initial deployment:

1. **Commit and push your changes**:
   
   ```bash
   git add .
   git commit -m "feat: configure GitHub Pages deployment"
   git push origin main
   ```

2. **Monitor the deployment**:
   - Go to the **Actions** tab in your GitHub repository
   - Look for the "Deploy Docusaurus to GitHub Pages" workflow
   - First deployment typically takes 2-3 minutes

3. **Access your deployed site**:
   - Your documentation will be available at:
   - `https://YOUR_USERNAME.github.io/varga-ai/`

:::info Build Time
The first deployment may take longer as GitHub sets up the Pages environment. Subsequent deployments are typically faster (30-60 seconds).
:::

## Manual Deployment

For development or troubleshooting, you can deploy manually:

```bash title="Manual deployment commands"
cd gutenberg

# Build the site locally
npm run build

# Deploy using gh-pages (requires gh-pages package)
npx gh-pages -d build
```

:::warning
Manual deployment may conflict with the automated workflow. Use this only for testing or when the automated workflow is unavailable.
:::

## Development Workflow

The recommended workflow for documentation updates:

1. **Create feature branch**:
   ```bash
   git checkout -b docs/update-deployment-guide
   ```

2. **Make changes** to documentation in `gutenberg/docs/`

3. **Push to feature branch**:
   ```bash
   git push origin docs/update-deployment-guide
   ```

4. **Create pull request**:
   - The workflow will automatically build and validate
   - Check for build status in PR comments
   - Review changes in the PR preview

5. **Merge when ready**:
   - Merge to main branch
   - Automatic deployment to GitHub Pages begins
   - Site updates within 2-3 minutes

## Troubleshooting

### Common Build Failures

**Missing Dependencies**
```bash
# Solution: Ensure package-lock.json is committed
git add gutenberg/package-lock.json
git commit -m "fix: add package-lock.json"
```

**Broken Links**
- Check the Actions tab for specific broken link errors
- Use Docusaurus link checker: `npm run build -- --verbose`
- Ensure all internal links use relative paths

**Node.js Version Issues**
- Workflow uses Node.js 20
- Test locally with same version: `nvm use 20`

### Configuration Issues

**Incorrect Base URL**
```typescript title="Common baseUrl mistakes"
// ❌ Wrong
baseUrl: 'varga-ai',        // Missing slashes
baseUrl: '/varga-ai',       // Missing trailing slash

// ✅ Correct  
baseUrl: '/varga-ai/',      // Proper format
```

**Repository Name Mismatch**
```typescript title="Ensure consistency"
// Repository name: my-awesome-docs
projectName: 'my-awesome-docs',     // Must match exactly
baseUrl: '/my-awesome-docs/',       // Must match exactly
```

### Permissions and Access

**GitHub Token Issues**
- The workflow uses `GITHUB_TOKEN` automatically provided by GitHub
- No manual token configuration required
- Ensure repository has Actions enabled in Settings

**Pages Access**
- Verify GitHub Pages is enabled in repository Settings > Pages
- Check that the repository is public (or GitHub Pro for private repos)

## Advanced Configuration

### Custom Domain Setup

1. **Add CNAME file**:
   ```bash title="gutenberg/static/CNAME"
   docs.yourdomain.com
   ```

2. **Update Docusaurus config**:
   ```typescript title="gutenberg/docusaurus.config.ts"
   url: 'https://docs.yourdomain.com',
   baseUrl: '/',
   ```

3. **Configure DNS**:
   - Add CNAME record pointing to `YOUR_USERNAME.github.io`

### Branch Protection

Recommended branch protection rules for main branch:

1. Go to Settings > Branches
2. Add rule for `main` branch:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators

### Workflow Customization

Modify `.github/workflows/deploy-docs.yml` for specific needs:

```yaml title="Custom workflow modifications"
# Deploy only on specific paths
on:
  push:
    branches: [main]
    paths: 
      - 'gutenberg/**'
      - 'docs/**'          # Add additional paths
      
# Custom build commands
- name: Build
  run: |
    cd gutenberg
    npm ci
    npm run build
    npm run test         # Add testing step
```

## Site Structure

After successful deployment, your documentation site will include:

- **Home Page** (`/`): Project overview and quick start guide
- **Project Overview** (`/project/`): Complete project specifications
- **Development** (`/development/`): Implementation guides and tool documentation
- **Architecture** (`/architecture/`): System design and technical architecture
- **API Reference** (`/api/`): Complete API documentation
- **User Guides** (`/guides/`): Getting started tutorials and user documentation

## Monitoring and Analytics

### Build Monitoring

- **Actions Tab**: Monitor all deployments and build status
- **Pages Tab**: View deployment history and status
- **Email Notifications**: Configure in GitHub notification settings

### Site Analytics

Consider adding analytics to track documentation usage:

```typescript title="gutenberg/docusaurus.config.ts"
const config: Config = {
  // ... other config
  themeConfig: {
    // ... other theme config
    googleAnalytics: {
      trackingID: 'UA-YOUR-TRACKING-ID',
    },
  },
};
```

## Best Practices

### Documentation Maintenance

1. **Regular Updates**: Keep documentation current with code changes
2. **Link Validation**: Regularly check for broken links
3. **Content Review**: Periodic review of content accuracy and clarity
4. **User Feedback**: Collect and address user feedback on documentation

### Performance Optimization

1. **Image Optimization**: Compress images and use appropriate formats
2. **Bundle Analysis**: Use `npm run build -- --bundle-analyzer`
3. **Caching Strategy**: Leverage GitHub CDN for static assets

### Security Considerations

1. **Dependency Updates**: Regularly update Node.js dependencies
2. **Access Control**: Use branch protection and required reviews
3. **Secrets Management**: Never commit API keys or secrets

## Next Steps

1. **Customize Branding**: Update site title, logo, and colors in `docusaurus.config.ts`
2. **Add Custom Content**: Create comprehensive documentation for your specific project
3. **Configure Analytics**: Add Google Analytics or similar tracking
4. **Set Up Monitoring**: Configure uptime monitoring for your documentation site
5. **Custom Domain**: Configure a custom domain if desired

Your Varga AI documentation site is now ready for professional deployment! 🚀

:::success Congratulations!
You've successfully configured automated GitHub Pages deployment for your documentation. Your site will now automatically update whenever you push changes to the main branch.
:::