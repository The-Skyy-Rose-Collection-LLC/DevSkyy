# Suggested Commands

## Verification
```bash
ls wordpress-theme/skyyrose-flagship/assets/css/*.css | wc -l
ls wordpress-theme/skyyrose-flagship/assets/js/*.js | wc -l
find wordpress-theme/skyyrose-flagship -name "*.php" -exec php -l {} \;
```

## Git
```bash
git status
git diff --stat
git log --oneline -10
```
