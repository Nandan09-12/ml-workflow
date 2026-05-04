# AWS Demo Files

This folder mixes two kinds of files:

- reusable helper files that are safe to commit
- private or machine-specific files that must stay local

## Safe To Commit

These files do not contain credentials and are intended to be shared in Git:

- `ec2-ssm-trust-policy.json`
- `ssm-up-params.json`
- `ssm-status-params.json`
- `ssm-debug-params.json`
- `ssm-ps-params.json`

## Keep Local Only

These files should not be committed:

- `*.pem`
- `demo-user-data.sh`
- `*.local.*`

Why:

- private keys and secret-filled bootstrap scripts should not go to GitHub
- local-only files may contain real environment values, instance details, or one-off deployment commands

## Pull Safety

Normal `git pull` does not delete untracked or ignored local files.

That means a local file like `aws/ml-workflow-demo-key.pem` or `aws/demo-user-data.sh` is usually still there after a pull.

The main ways local-only files can be lost are:

- you delete them manually
- you run cleanup commands such as `git clean -fd` or `git clean -fdx`
- you replace the whole repo folder
- a future tracked file is introduced at the exact same path and Git blocks checkout or merge until you move the local file out of the way

## Practical Recommendation

- keep private keys outside the repo when possible
- keep only sanitized helpers in Git
- if you create local variants, use names like `*.local.*` so they stay ignored
