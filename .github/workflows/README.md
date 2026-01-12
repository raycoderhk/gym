# GitHub Actions Workflows

## Automated Workout Backup

The `backup.yml` workflow automatically backs up your workout data on a schedule.

### Features

- **Scheduled backups**: Runs daily at 2 AM UTC (configurable)
- **Manual trigger**: Can be triggered manually from the GitHub Actions tab
- **Artifact storage**: Backups are stored as GitHub Actions artifacts (90-day retention)
- **Private repository**: Backups are committed to a separate private repository for version control
- **Simple filenames**: Uses `workouts.csv` and `exercises.csv` (Git tracks versions automatically)

### Setup Instructions

1. **Create Private Backup Repository** (required):
   - Create a new **private** repository (e.g., `gym-data` or `gym-backups`)
   - Repository can be empty or initialized with a README
   - This keeps your workout data private while the main repo stays public

2. **Create Personal Access Token (PAT)** (required):
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Name it (e.g., "Gym Backup Workflow")
   - Select scope: `repo` (full control of private repositories)
   - Generate token and **copy it immediately** (you won't see it again)

3. **Add GitHub Secrets** (required):
   - Go to your **public** repository → Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `SUPABASE_URL`: Your Supabase project URL
     - `SUPABASE_KEY`: Your Supabase anon/service role key
     - `BACKUP_REPO`: Your private backup repository name (e.g., `raycoderhk/gym-data`)
     - `BACKUP_REPO_TOKEN`: The PAT you created in step 2
     - (Optional) `USER_ID`: Your user UUID if you have multiple users

4. **Configure Schedule** (optional):
   - Edit `.github/workflows/backup.yml`
   - Modify the cron schedule: `cron: '0 2 * * *'` (currently 2 AM UTC daily)
   - Cron format: `minute hour day month weekday`
   - Example: `'0 6 * * 1'` = Every Monday at 6 AM UTC

5. **Manual Trigger**:
   - Go to Actions tab → "Automated Workout Backup" → "Run workflow"

### Backup Storage

Backups are stored in two places:

1. **GitHub Actions Artifacts**:
   - Accessible from the Actions tab
   - 90-day retention period
   - Downloadable as ZIP files
   - Always private (even if repository is public)

2. **Private Backup Repository**:
   - Committed to your private repository (e.g., `gym-data`)
   - Version history maintained via Git
   - Simple filenames: `workouts.csv` and `exercises.csv`
   - Git commit timestamps track when backups were created
   - View history: `git log workouts.csv` in the backup repository

### Security Notes

- ✅ **Main repository stays public**: Perfect for Streamlit Cloud deployment
- ✅ **Backup data is private**: Stored in separate private repository
- ✅ **Secrets are encrypted**: Only accessible during workflow execution
- ✅ **PAT stored securely**: Personal Access Token stored as encrypted secret
- ✅ **Artifacts are private**: Always private, even in public repositories

### Troubleshooting

**Workflow fails with "No users found":**
- Ensure `SUPABASE_URL` and `SUPABASE_KEY` secrets are set correctly
- If you have multiple users, set the `USER_ID` secret

**Backups not appearing:**
- Check the Actions tab for workflow run status
- Verify secrets are set correctly (`SUPABASE_URL`, `SUPABASE_KEY`, `BACKUP_REPO`, `BACKUP_REPO_TOKEN`)
- Verify the private backup repository exists and PAT has access
- Check workflow logs for error messages

**Backup repository commit fails:**
- Verify `BACKUP_REPO` secret is set correctly (format: `username/repo-name`)
- Verify `BACKUP_REPO_TOKEN` is a valid PAT with `repo` scope
- Ensure the PAT has access to the private repository
- Check that the private repository exists and is accessible

**Schedule not running:**
- GitHub Actions schedules require at least one commit in the last 60 days
- Ensure the workflow file is in the default branch (usually `main` or `master`)
