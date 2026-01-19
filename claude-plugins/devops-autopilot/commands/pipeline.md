---
name: pipeline
description: Generate CI/CD pipeline for GitHub Actions, GitLab CI, or Jenkins
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
argument-hint: "[github|gitlab|jenkins] [--docker] [--deploy]"
---

# Pipeline Command

Generate a complete CI/CD pipeline configuration for your project.

## Execution Steps

1. **Detect project type**
   - Check package.json for framework
   - Identify build system
   - Check for existing workflows

2. **Determine platform**
   - If argument provided: Use specified platform
   - If `.github/` exists: GitHub Actions
   - If GitLab repo: GitLab CI
   - Otherwise: Ask or default to GitHub Actions

3. **Generate pipeline**
   - Create workflow file with appropriate stages
   - Include lint, test, build stages
   - Add Docker build if `--docker` flag or Dockerfile exists
   - Add deployment if `--deploy` flag

4. **Add supporting files**
   - Create necessary directories
   - Add caching configuration
   - Configure secrets handling

## Arguments

- `github`: Generate GitHub Actions workflow
- `gitlab`: Generate GitLab CI configuration
- `jenkins`: Generate Jenkinsfile
- `--docker`: Include Docker build and push stages
- `--deploy`: Include deployment stages

## Example Usage

```
/pipeline                    # Auto-detect and generate
/pipeline github             # GitHub Actions
/pipeline gitlab --docker    # GitLab CI with Docker
/pipeline jenkins --deploy   # Jenkins with deployment
```

## Output Files

- GitHub Actions: `.github/workflows/ci.yml`
- GitLab CI: `.gitlab-ci.yml`
- Jenkins: `Jenkinsfile`

## Post-Generation

After generating:
1. List secrets that need to be configured
2. Explain how to trigger the pipeline
3. Note any manual steps required
