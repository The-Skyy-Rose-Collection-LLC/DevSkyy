# DevSkyy Code Review Checklist

## Overview

This checklist ensures consistent, high-quality code reviews for the DevSkyy Enterprise Platform. Use this as a guide for both pull request authors and reviewers.

## Pre-Review (Author Checklist)

Before requesting a review, ensure:

### Code Quality
- [ ] All linting checks pass locally (`pre-commit run --all-files`)
- [ ] Code follows PEP 8 standards
- [ ] No unused imports or variables
- [ ] Proper operator spacing
- [ ] No trailing whitespace
- [ ] Functions are under 50 lines (guideline)
- [ ] Cyclomatic complexity under 12

### Testing
- [ ] New code has corresponding tests
- [ ] All tests pass locally (`pytest`)
- [ ] Test coverage is maintained or improved
- [ ] Edge cases are tested
- [ ] Error conditions are tested

### Documentation
- [ ] All public functions/classes have docstrings
- [ ] Docstrings follow Google style guide
- [ ] Type hints are present
- [ ] README/docs updated if needed
- [ ] CHANGELOG updated if applicable

### Security
- [ ] No hardcoded secrets or credentials
- [ ] Input validation is present
- [ ] Proper exception handling
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (input sanitization)

### Performance
- [ ] No obvious performance bottlenecks
- [ ] Database queries are optimized
- [ ] Appropriate caching is used
- [ ] No N+1 query problems

### Git Hygiene
- [ ] Commits are atomic and well-described
- [ ] No merge commits (rebase if needed)
- [ ] Branch is up-to-date with base branch
- [ ] No WIP or debugging commits

## Review Process (Reviewer Checklist)

### 1. High-Level Review

#### Architecture & Design
- [ ] Changes align with overall architecture
- [ ] Design patterns are used appropriately
- [ ] SOLID principles are followed
- [ ] No code duplication (DRY principle)
- [ ] Separation of concerns is maintained

#### Business Logic
- [ ] Code solves the stated problem
- [ ] Requirements are met completely
- [ ] Edge cases are handled
- [ ] Error conditions are handled gracefully

### 2. Code Quality Review

#### Style & Formatting
- [ ] Code follows PEP 8 standards
- [ ] Consistent naming conventions
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
- [ ] Proper indentation (4 spaces)
- [ ] Line length under 119 characters
- [ ] No trailing whitespace

#### Code Structure
- [ ] Functions have single responsibility
- [ ] Functions are appropriately sized
- [ ] Classes are cohesive
- [ ] Proper use of abstractions
- [ ] Avoid deep nesting (max 4 levels)

#### Imports
- [ ] No unused imports
- [ ] Imports are organized (stdlib, third-party, local)
- [ ] No circular imports
- [ ] Imports are specific (not `import *`)

### 3. Functionality Review

#### Correctness
- [ ] Logic is correct
- [ ] Algorithm efficiency is appropriate
- [ ] Data structures are appropriate
- [ ] Type conversions are safe
- [ ] Off-by-one errors are avoided

#### Error Handling
- [ ] Exceptions are specific (no bare `except:`)
- [ ] Error messages are descriptive
- [ ] Errors are logged appropriately
- [ ] User-facing errors are user-friendly
- [ ] Resources are cleaned up (files, connections)

#### Async Operations
- [ ] Proper use of `async`/`await`
- [ ] No blocking operations in async code
- [ ] Proper handling of concurrent operations
- [ ] Race conditions are avoided

### 4. Security Review

#### Authentication & Authorization
- [ ] Proper authentication checks
- [ ] Authorization is enforced
- [ ] No hardcoded credentials
- [ ] Secrets are in environment variables

#### Input Validation
- [ ] All inputs are validated
- [ ] SQL injection is prevented
- [ ] XSS is prevented
- [ ] Path traversal is prevented
- [ ] File upload validation is present

#### Data Protection
- [ ] Sensitive data is encrypted
- [ ] Passwords are hashed (not encrypted)
- [ ] No sensitive data in logs
- [ ] GDPR compliance where applicable

#### Dependencies
- [ ] No known vulnerable dependencies
- [ ] Dependencies are necessary
- [ ] Versions are pinned appropriately

### 5. Testing Review

#### Test Coverage
- [ ] New code has tests
- [ ] Tests are meaningful
- [ ] Edge cases are tested
- [ ] Error cases are tested
- [ ] Tests are not too brittle

#### Test Quality
- [ ] Tests are readable
- [ ] Tests are maintainable
- [ ] Tests are isolated
- [ ] No test interdependencies
- [ ] Mock/fixtures used appropriately

#### Test Types
- [ ] Unit tests for business logic
- [ ] Integration tests for workflows
- [ ] API tests for endpoints
- [ ] Performance tests if needed

### 6. Performance Review

#### Efficiency
- [ ] No unnecessary computations
- [ ] Appropriate data structures
- [ ] No redundant database queries
- [ ] Caching used where beneficial
- [ ] Lazy loading where appropriate

#### Database
- [ ] Queries are optimized
- [ ] Indexes are used appropriately
- [ ] No N+1 query problems
- [ ] Transactions are used correctly
- [ ] Connection pooling is used

#### API Design
- [ ] Pagination for large datasets
- [ ] Rate limiting considered
- [ ] Bulk operations where possible
- [ ] Appropriate HTTP methods
- [ ] Proper status codes

### 7. Documentation Review

#### Code Comments
- [ ] Comments explain "why", not "what"
- [ ] Complex logic has comments
- [ ] No commented-out code
- [ ] TODOs have owner and date

#### Docstrings
- [ ] All public functions have docstrings
- [ ] Docstrings follow Google style
- [ ] Type hints are present
- [ ] Examples provided where helpful
- [ ] Parameters documented
- [ ] Return values documented
- [ ] Exceptions documented

#### External Documentation
- [ ] README updated if needed
- [ ] API documentation updated
- [ ] Architecture docs updated
- [ ] CHANGELOG updated

### 8. Maintainability Review

#### Readability
- [ ] Code is easy to understand
- [ ] Variable names are descriptive
- [ ] Magic numbers are avoided
- [ ] Constants are named
- [ ] Logic is clear

#### Modularity
- [ ] Code is modular
- [ ] Functions are reusable
- [ ] Coupling is minimized
- [ ] Cohesion is maximized

#### Future-Proofing
- [ ] Code is extensible
- [ ] Configuration is externalized
- [ ] Feature flags used appropriately
- [ ] Backwards compatibility maintained

## Review Comments Guide

### Categorizing Comments

Use these prefixes for clarity:

- **[BLOCKER]**: Must be fixed before merge
- **[CRITICAL]**: Should be fixed before merge
- **[SUGGESTION]**: Nice to have, not required
- **[QUESTION]**: Asking for clarification
- **[PRAISE]**: Positive feedback

### Examples

#### Good Comments

✅ **[BLOCKER] Security Issue**
```
This SQL query is vulnerable to injection attacks. Please use 
parameterized queries:
```python
# Instead of:
query = f"SELECT * FROM users WHERE id = {user_id}"

# Use:
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

✅ **[SUGGESTION] Performance**
```
Consider caching this calculation since it's called in a loop:
```python
# Cache expensive calculation
cached_value = expensive_calculation()
for item in items:
    result = item.value * cached_value
```

✅ **[PRAISE]**
```
Great use of the decorator pattern here! This makes the code much 
more maintainable than the previous approach.
```

#### Comments to Avoid

❌ **Too Vague**
```
This doesn't look right.
```

✅ **Better**
```
[CRITICAL] This function returns None when the product is not found,
but the calling code expects a dict. This will cause an AttributeError.
```

❌ **Overly Prescriptive**
```
Change line 45 to use a list comprehension instead of a for loop.
```

✅ **Better**
```
[SUGGESTION] A list comprehension might be more Pythonic here:
`results = [process(item) for item in items]`
```

## Response Guidelines

### For Authors

- **Don't take it personally** - Reviews are about code, not you
- **Ask for clarification** - If feedback is unclear
- **Explain your reasoning** - If you disagree with feedback
- **Be grateful** - Reviewers are helping improve your code
- **Respond to all comments** - Even if just to acknowledge

### For Reviewers

- **Be respectful** - Use "we" language, not "you"
- **Be specific** - Point to exact lines and provide examples
- **Explain why** - Don't just say what's wrong, explain why
- **Praise good code** - Recognize good practices
- **Prioritize feedback** - Use categories ([BLOCKER], [SUGGESTION], etc.)
- **Be timely** - Review within 24 hours if possible

## Common Review Patterns

### Security Issues

Always mark as **[BLOCKER]**:
- Hardcoded credentials
- SQL injection vulnerabilities
- XSS vulnerabilities
- Missing authentication/authorization
- Insecure cryptography

### Performance Issues

Mark as **[CRITICAL]** if severe:
- N+1 queries
- Missing database indexes
- Unbounded loops
- Memory leaks
- Blocking operations in async code

### Code Quality Issues

Usually **[SUGGESTION]**:
- Long functions (>50 lines)
- High complexity (>12)
- Code duplication
- Unclear variable names
- Missing type hints

### Documentation Issues

**[CRITICAL]** for public APIs:
- Missing docstrings on public functions
- Incorrect/outdated documentation
- Missing type hints

**[SUGGESTION]** for internal code:
- Missing comments on complex logic
- Could use better variable names

## Approval Criteria

### Minimum Requirements for Approval

- [ ] All **[BLOCKER]** issues resolved
- [ ] All **[CRITICAL]** issues resolved or have plan
- [ ] CI/CD checks pass
- [ ] Tests pass
- [ ] No merge conflicts
- [ ] Approved by at least one reviewer

### When to Request Changes

Request changes if:
- Security vulnerabilities exist
- Tests are failing
- Code doesn't meet requirements
- Critical bugs are present
- Multiple [CRITICAL] issues unresolved

### When to Approve with Comments

Approve with comments if:
- Only [SUGGESTION] items remain
- Minor issues that can be fixed later
- Questions that don't affect functionality
- All critical issues resolved

## Tools & Automation

### Automated Checks (CI/CD)
- Linting (Ruff, Flake8)
- Formatting (Black, isort)
- Type checking (MyPy)
- Security scanning (Bandit)
- Test coverage
- Performance benchmarks

### Manual Review Focus
- Business logic correctness
- Architecture decisions
- Security implications
- User experience
- Edge cases
- Error handling

## Review Checklist Quick Reference

```
High-Level:
□ Solves stated problem
□ Follows architecture
□ No code duplication
□ Handles edge cases

Code Quality:
□ PEP 8 compliant
□ No unused imports
□ Proper naming
□ Functions < 50 lines
□ Complexity < 12

Functionality:
□ Logic is correct
□ Error handling present
□ Resources cleaned up
□ Async used properly

Security:
□ No hardcoded secrets
□ Input validation
□ Proper authentication
□ No injection vulnerabilities

Testing:
□ New code has tests
□ Tests pass
□ Edge cases tested
□ Good coverage

Performance:
□ No obvious bottlenecks
□ Queries optimized
□ Appropriate caching
□ No N+1 queries

Documentation:
□ Public functions documented
□ Type hints present
□ Comments on complex logic
□ Docs updated
```

---

**Last Updated**: 2025-11-11  
**Version**: 1.0  
**Maintained by**: DevSkyy Platform Team
