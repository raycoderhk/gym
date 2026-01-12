# GitHub Actions Workflows

## Automated Workout Backup

The `backup.yml` workflow automatically backs up your workout data on a schedule.

### Features

- **Scheduled backups**: Runs daily at 2 AM UTC (configurable)
- **Manual trigger**: Can be triggered manually from the GitHub Actions tab
- **Artifact storage**: Backups are stored as GitHub Actions artifacts (90-day retention)
- **Repository commits**: Backups are also committed to the `backups/` directory for version history

### Setup Instructions

1. **Add GitHub Secrets** (required):
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `SUPABASE_URL`: Your Supabase project URL
     - `SUPABASE_KEY`: Your Supabase anon/service role key
     - (Optional) `USER_ID`: Your user UUID if you have multiple users

2. **Configure Schedule** (optional):
   - Edit `.github/workflows/backup.yml`
   - Modify the cron schedule: `cron: '0 2 * * *'` (currently 2 AM UTC daily)
   - Cron format: `minute hour day month weekday`
   - Example: `'0 6 * * 1'` = Every Monday at 6 AM UTC

3. **Manual Trigger**:
   - Go to Actions tab → "Automated Workout Backup" → "Run workflow"

### Backup Storage

Backups are stored in two places:

1. **GitHub Actions Artifacts**:
   - Accessible from the Actions tab
   - 90-day retention period
   - Downloadable as ZIP files

2. **Repository `backups/` directory**:
   - Committed to the repository
   - Version history maintained
   - Files named with timestamp: `workouts_YYYYMMDD_HHMMSS.csv`

### Security Notes

- ⚠️ **Private Repository Recommended**: Since backups contain personal workout data, use a private repository
- ✅ Secrets are encrypted and only accessible during workflow execution
- ✅ Backup files in `backups/` directory are tracked in Git history

### Troubleshooting

**Workflow fails with "No users found":**
- Ensure `SUPABASE_URL` and `SUPABASE_KEY` secrets are set correctly
- If you have multiple users, set the `USER_ID` secret

**Backups not appearing:**
- Check the Actions tab for workflow run status
- Verify secrets are set correctly
- Check workflow logs for error messages

**Schedule not running:**
- GitHub Actions schedules require at least one commit in the last 60 days
- Ensure the workflow file is in the default branch (usually `main` or `master`)
