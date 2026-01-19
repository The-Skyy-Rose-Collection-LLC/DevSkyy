---
name: deploy-infra
description: Deploy infrastructure using Terraform with autonomous error handling
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - Task
argument-hint: "[plan|apply|destroy] [--auto-approve]"
---

# Deploy Infrastructure Command

Deploy or manage Terraform infrastructure with autonomous error handling.

## Execution Steps

1. **Validate Terraform configuration**
   ```bash
   terraform validate
   terraform fmt -check
   ```

2. **Execute Terraform command**
   - `plan`: Show planned changes
   - `apply`: Apply infrastructure changes
   - `destroy`: Destroy infrastructure

3. **Handle errors autonomously**
   - Capture any errors
   - Fetch documentation if needed
   - Apply fixes
   - Retry operation

4. **Verify deployment**
   - Check Terraform state
   - Verify resources created
   - Test connectivity if possible

## Arguments

- `plan`: Show what will change (default)
- `apply`: Apply the changes
- `destroy`: Destroy all resources
- `--auto-approve`: Skip confirmation prompt

## Example Usage

```
/deploy-infra                # Plan only
/deploy-infra plan           # Explicit plan
/deploy-infra apply          # Apply with confirmation
/deploy-infra apply --auto-approve  # Apply without confirmation
/deploy-infra destroy        # Destroy with confirmation
```

## Safety Checks

Before applying:
1. Validate configuration
2. Show plan summary
3. Check for destructive changes
4. Warn about production resources

## Error Handling

Common errors handled:
- State lock errors → Force unlock if safe
- Resource conflicts → Import or recreate
- Permission errors → Check IAM policy
- Provider errors → Update provider version

## Output

After execution:
1. Summary of changes
2. Resource IDs created
3. Output values
4. Next steps
