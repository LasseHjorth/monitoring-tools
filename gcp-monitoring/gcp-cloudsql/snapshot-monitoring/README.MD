# Send timestamp + age of snapshots to Google Cloud Monitoring.

Creates two metrics:
* cloudsql_snapshot_timestamp - unixtimestamp value of the starttime of the snapshot (intended to be used with promql and time() function).

* cloudsql_snapshot_age - Age in seconds of the latest snapshot. (Can be used directly for monitoring)

Will send metrics on each run - suggested run rate is every 15-60 minutes.

Needs pipenv (or the packages listed in Pipfile to be available)

Example run:
```
PROJECT_ID="my-project-name" python __main__.py
```