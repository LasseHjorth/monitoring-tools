import googleapiclient.discovery
import os
import datetime
import time
from google.cloud import monitoring_v3

sqladmin = googleapiclient.discovery.build('sqladmin', 'v1beta4')
monitoring = monitoring_v3.MetricServiceClient()
project = os.getenv("PROJECT_ID") or exit(1)


def get_sqlinstances(project,sqladmin):
    # Fetch all sqlinstances in the project
    # Might need something that can handle pagination.
    try:
        req = sqladmin.instances().list(project=project)
        resp = req.execute()
        return resp.get("items")
    except:
        return []
    
def get_latest_snapshot(sqladmin,instance):
    # Get the latest successful snapshot.
    req = sqladmin.backupRuns().list(project=instance['project'],instance=instance['name'])
    resp = req.execute()
    backups = resp.get("items")
    for backup in backups:
        if not "endTime" in backup: 
            pass              
        if backup["status"] != "SUCCESSFUL":
            pass

        if backup["status"] == "SUCCESSFUL":
            backup_time = datetime.datetime.fromisoformat(backup["startTime"])
            return int(datetime.datetime.timestamp(backup_time))
    return 0

def generate_metric_point(instance,metric_name,value):
    # Generate a single metric point to be sent to Google Cloud Monitoring
    time_series = monitoring_v3.types.TimeSeries()
    time_series.metric.type = 'custom.googleapis.com/' + metric_name
    time_series.resource.type = 'global'
    time_series.metric.labels["instance_name"] = instance['name']
    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)
    interval = monitoring_v3.TimeInterval(
        {"end_time": {"seconds": seconds, "nanos": nanos}}
    )
    point = monitoring_v3.Point({"interval": interval, "value": {"int64_value": value}})
    time_series.points.append(point)  
    return time_series

def write_metrics(project,monitoring,time_series):
    # Submit all the time_series(points) that has been generated.
    request = monitoring_v3.CreateTimeSeriesRequest(
        name=f"projects/{project}",
        time_series=time_series
    )
    monitoring.create_time_series(request=request)

# Get list of SQL instances.
sql_instances = get_sqlinstances(project,sqladmin)
# Init empty list of time_series.
time_series = []
for sql_instance in sql_instances:
    # Iterate the SQL Instances fetch latest backup and add metrics to time_series list.
    ts = get_latest_snapshot(sqladmin,sql_instance)
    metric_timestamp = generate_metric_point(sql_instance,"cloudsql_snapshot_timestamp",ts)
    time_series.append(metric_timestamp)
    metric_age = generate_metric_point(sql_instance,"cloudsql_snapshot_age",int(time.time()-ts))
    time_series.append(metric_age)

# Send the metric to Google Cloud Monitoring
write_metrics(project,monitoring,time_series)


