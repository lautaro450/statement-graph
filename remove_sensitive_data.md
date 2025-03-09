# How to Remove Sensitive Data from Git History

GitHub has detected sensitive credentials in your commit history. Here's how to fix this:

## Option 1: Using git filter-branch

```bash
# First, make sure you have a backup of your repository
# Then run the following command to remove the API key from all files in history
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all

# Force push the changes
git push origin --force --all
```

## Option 2: Using BFG Repo Cleaner (recommended, faster)

1. Download BFG Repo Cleaner from: https://rtyley.github.io/bfg-repo-cleaner/
2. Create a text file called `passwords.txt` with the API key to remove
3. Run the following command:

```bash
# Assuming you downloaded bfg.jar to your downloads folder
java -jar path/to/bfg.jar --replace-text passwords.txt my-repo.git

# Then clean up and push
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force
```

## Alternative: Allow the Secret

If this is a test API key or not a concern:
- Use the link GitHub provided to allow this specific secret: https://github.com/lautaro450/statement-graph/security/secret-scanning/unblock-secret/2u5ZSh7aIClYqwEZub61MT9OkOB

## Best Practice Going Forward

1. NEVER commit sensitive information to Git
2. Always use .env files for secrets and ensure they're in .gitignore
3. Use environment variables or secret management systems in production
4. Consider using a pre-commit hook to check for accidental secrets before commits
