# Monitoring and Alerting Strategy

## Overview

This document describes the comprehensive monitoring and alerting strategy for the Brewery Data Pipeline. It covers operational metrics, data quality monitoring, alerting rules, and incident response procedures.

## 1. Monitoring Layers

### 1.1 Infrastructure Monitoring

**Metrics to Track:**
- CPU utilization (Target: <70% average)
- Memory usage (Target: <80% average)
- Disk I/O (Target: <500 IOPS)
- Network throughput
- Disk space (Alert: >80% used)

**Tools:**
- Docker: `docker stats`
- Prometheus + Grafana
- Cloud-native: CloudWatch (AWS), Cloud Monitoring (GCP), Azure Monitor

**Implementation:**
```python
# Add to Airflow metrics
from airflow.metrics.statsd_logger import SafeStatsdLogger

stats = SafeStatsdLogger()
stats.gauge('brewery_pipeline.cpu_percent', cpu_usage)
stats.gauge('brewery_pipeline.memory_mb', memory_mb)
```

### 1.2 Pipeline Monitoring

**Metrics to Track:**
| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Pipeline Duration | <10 min | >15 min |
| Task Success Rate | >99% | <95% |
| API Response Time | <5 sec | >30 sec |
| Records Processed | ~8000 | <6000 or >10000 |
| Data Freshness | <24 hrs | >36 hrs |

**Airflow Built-in Monitoring:**
```python
# In DAG definition:
default_args = {
    'sla': timedelta(minutes=15),  # Service Level Agreement
    'execution_timeout': timedelta(hours=1),
    'on_failure_callback': send_alert,
    'on_retry_callback': log_retry,
    'on_success_callback': update_metrics,
}

def send_alert(context):
    """Send alert on task failure."""
    task_instance = context['task_instance']
    dag_id = context['dag'].dag_id
    
    # Email (configured in airflow.cfg)
    # Automatically sent if email_on_failure=True
    # For custom notifications, add your integration here
```

### 1.3 Data Quality Monitoring

**Checks Implemented:**
1. **Record Count Validation**
   - Min threshold: 100 records
   - Variance check: Alert if >20% change from previous run

2. **Schema Validation**
   - Required columns present
   - Data types correct
   - No unexpected columns

3. **Data Completeness**
   - Critical fields non-null: >70%
   - Coordinates available: >50%
   - Complete addresses: >40%

4. **Data Integrity**
   - Duplicate IDs: <5%
   - Valid brewery types
   - Geographic data within bounds

5. **Freshness**
   - Bronze layer timestamp <1 hour old
   - Silver layer updated <2 hours after bronze
   - Gold layer updated <30 min after silver

**Extended Quality Module:**
```python
# src/common/data_quality_extended.py

def check_variance(current_count: int, previous_count: int, threshold: float = 0.2):
    """Check if record count variance exceeds threshold."""
    if previous_count == 0:
        return True
    
    variance = abs(current_count - previous_count) / previous_count
    if variance > threshold:
        logger.warning(
            f"Record count variance {variance:.2%} exceeds threshold {threshold:.2%}",
            extra={
                "current_count": current_count,
                "previous_count": previous_count,
                "variance": variance
            }
        )
        return False
    return True

def check_schema_drift(df: pd.DataFrame, expected_schema: dict):
    """Detect schema changes."""
    actual_cols = set(df.columns)
    expected_cols = set(expected_schema.keys())
    
    missing = expected_cols - actual_cols
    unexpected = actual_cols - expected_cols
    
    if missing or unexpected:
        logger.error(
            "Schema drift detected",
            extra={
                "missing_columns": list(missing),
                "unexpected_columns": list(unexpected)
            }
        )
        return False
    return True
```

## 2. Alerting Configuration

### 2.1 Alert Severity Levels

| Severity | Response Time | Notification Channels | Example |
|----------|--------------|----------------------|---------|
| CRITICAL | Immediate (15 min) | PagerDuty + Email | Pipeline failure, data corruption |
| HIGH | 1 hour | Email | Quality check failure, SLA breach |
| MEDIUM | 4 hours | Email | Performance degradation, warnings |
| LOW | 24 hours | Email digest | Informational, capacity planning |

### 2.2 Alert Rules

**Critical Alerts:**
```yaml
- name: pipeline_failure
  condition: any_task_failed
  severity: critical
  channels: [email, pagerduty]
  message: "Brewery pipeline failed at task {{ task_id }}"
  
- name: data_quality_critical
  condition: critical_quality_check_failed
  severity: critical
  channels: [email]
  message: "Critical data quality issue: {{ issue_description }}"
  
- name: no_data_extracted
  condition: records_extracted == 0
  severity: critical
  channels: [email, pagerduty]
  message: "API extraction returned zero records"
```

**High Alerts:**
```yaml
- name: sla_breach
  condition: task_duration > sla_threshold
  severity: high
  channels: [email]
  message: "SLA breached: {{ task_id }} took {{ duration }} (SLA: {{ sla }})"
  
- name: record_count_variance
  condition: abs(current - previous) / previous > 0.2
  severity: high
  channels: [email]
  message: "Record count variance: {{ variance }}% (current: {{ current }}, previous: {{ previous }})"
```

**Medium Alerts:**
```yaml
- name: quality_warning
  condition: quality_check_status == "WARNING"
  severity: medium
  channels: [email]
  message: "Quality check warning: {{ warning_message }}"
  
- name: slow_task
  condition: task_duration > 2 * avg_duration
  severity: medium
  channels: [email]
  message: "Task {{ task_id }} slower than usual: {{ duration }} vs avg {{ avg }}"
```

### 2.3 Alert Implementations

**Email Alerting (Built-in Airflow):**
```python
# Configure in airflow.cfg:
[email]
email_backend = airflow.utils.email.send_email_smtp

[smtp]
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = your-email@gmail.com
smtp_password = your-app-password
smtp_port = 587
smtp_mail_from = airflow@brewery-pipeline.com
```

**PagerDuty Integration:**
```python
from pdpyras import EventsAPISession

class PagerDutyAlerter:
    def __init__(self, integration_key: str):
        self.session = EventsAPISession(integration_key)
    
    def trigger_incident(self, title: str, details: dict):
        """Trigger PagerDuty incident."""
        self.session.trigger(
            summary=title,
            source='brewery_pipeline',
            severity='critical',
            custom_details=details
        )
```

## 3. Monitoring Dashboards

### 3.1 Airflow Dashboard (Built-in)

**Views to Monitor:**
- DAG Run Duration (time-series chart)
- Task Success/Failure Rates (pie chart)
- Task Duration by Task ID (bar chart)
- Recent Failures (table)

### 3.2 Grafana Dashboard (Recommended)

**Panels:**

1. **Pipeline Health Panel**
   - Success rate (last 30 runs)
   - Average duration trend
   - Task-by-task status

2. **Data Metrics Panel**
   - Records processed per run
   - Data quality score (0-100)
   - Layer-wise data size

3. **Infrastructure Panel**
   - CPU/Memory usage
   - Disk I/O
   - Network traffic

4. **Quality Metrics Panel**
   - Completeness score
   - Duplicate percentage
   - Schema validation status

**Grafana Dashboard JSON:**
```json
{
  "dashboard": {
    "title": "Brewery Pipeline Monitoring",
    "panels": [
      {
        "title": "Pipeline Success Rate",
        "targets": [{
          "expr": "rate(airflow_dag_run_success_total[1h])"
        }],
        "type": "graph"
      },
      {
        "title": "Records Processed",
        "targets": [{
          "expr": "brewery_pipeline_records_total"
        }],
        "type": "stat"
      }
    ]
  }
}
```

### 3.3 Custom Quality Dashboard

```python
# Generate HTML dashboard from quality results

def generate_quality_dashboard(quality_results: dict) -> str:
    """Generate HTML quality dashboard."""
    
    html = f"""
    <html>
    <head><title>Data Quality Dashboard</title></head>
    <body>
        <h1>Data Quality Report</h1>
        <h2>Status: {quality_results['status']}</h2>
        
        <table border="1">
            <tr><th>Check</th><th>Status</th><th>Value</th><th>Threshold</th></tr>
            {"".join([
                f"<tr><td>{c['check']}</td><td>{'✅' if c['passed'] else '❌'}</td>"
                f"<td>{c['value']}</td><td>{c.get('threshold', 'N/A')}</td></tr>"
                for c in quality_results['checks']
            ])}
        </table>
        
        <h3>Summary</h3>
        <p>Total Checks: {quality_results['total_checks']}</p>
        <p>Passed: {quality_results['passed_checks']}</p>
        <p>Failed: {quality_results['total_checks'] - quality_results['passed_checks']}</p>
    </body>
    </html>
    """
    
    return html
```

## 4. Incident Response

### 4.1 Response Procedures

**Critical Pipeline Failure:**
1. **Alert received** → Auto-page on-call engineer
2. **Initial triage** (5 min):
   - Check Airflow UI for failed task
   - Review task logs
   - Identify error type
3. **Mitigation** (15 min):
   - API failure → Check API status, retry
   - Transform failure → Check data format, rollback if needed
   - Resource issue → Scale up resources
4. **Resolution** (30 min):
   - Fix root cause
   - Re-run failed task
   - Verify success
5. **Postmortem** (24 hrs):
   - Document incident
   - Identify prevention measures
   - Update runbooks

**Quality Check Failure:**
1. **Review quality report**
2. **Check if data anomaly or code issue**
3. **If data anomaly:**
   - Investigate source (API change?)
   - Adjust quality thresholds if needed
   - Document finding
4. **If code issue:**
   - Fix transformation logic
   - Add test case
   - Re-run pipeline

### 4.2 Runbook

**Common Issues & Solutions:**

| Issue | Symptoms | Solution |
|-------|----------|----------|
| API Rate Limiting | 429 status, slow extraction | Increase retry delay, reduce concurrency |
| Out of Memory | OOM error in Silver layer | Increase memory, process in batches |
| Disk Full | Write errors | Clean old data, increase disk size |
| Schema Drift | Silver transformation fails | Update schema, add migration |
| Duplicate Data | Quality check fails | Fix deduplication logic, clean Bronze |

## 5. Performance Monitoring

### 5.1 Key Metrics

```python
# Track in each layer:

def track_performance(func):
    """Decorator to track function performance."""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        logger.info(
            f"{func.__name__} completed",
            extra={
                "duration_seconds": duration,
                "function": func.__name__
            }
        )
        
        # Send to monitoring
        stats.timing(f'brewery_pipeline.{func.__name__}.duration', duration)
        
        return result
    
    return wrapper
```

### 5.2 Optimization Triggers

**When to Optimize:**
- Task duration increases >50% over 7-day average
- Memory usage consistently >80%
- API calls fail >5% of the time
- Data processing time exceeds SLA

**Optimization Strategies:**
- Parallel processing (Airflow task groups)
- Incremental data loading
- Partition pruning
- Data compression
- Caching frequently accessed data

## 6. Cost Monitoring

### 6.1 Resource Costs

**Track:**
- Compute costs (per DAG run)
- Storage costs (by layer)
- Network egress costs
- API call costs (if applicable)

**Optimization:**
- Compress old data
- Archive Bronze layer after N days
- Use spot instances for non-critical tasks
- Optimize Parquet compression

### 6.2 Cost Alerts

```python
# Alert if daily cost exceeds budget
daily_budget = 10.00  # USD
if actual_cost > daily_budget:
    send_alert(f"Cost alert: ${actual_cost:.2f} exceeds budget ${daily_budget:.2f}")
```

## 7. Audit Logging

### 7.1 What to Log

**Execution Logs:**
- Pipeline start/end times
- Records processed per layer
- Quality check results
- Errors and warnings

**Data Lineage:**
- Source file → Bronze → Silver → Gold
- Transformation applied
- Quality checks passed/failed

**Access Logs:**
- Who triggered manual runs
- Configuration changes
- Data access patterns

### 7.2 Log Retention

| Log Type | Retention | Storage |
|----------|-----------|---------|
| Execution logs | 90 days | Airflow logs |
| Quality reports | 1 year | S3/GCS/Azure Blob |
| Audit logs | 7 years | Compliance storage |
| Debug logs | 30 days | Local/ELK stack |

## 8. Continuous Improvement

### 8.1 Monthly Review

- Analyze failure patterns
- Review SLA compliance
- Optimize slow tasks
- Update quality thresholds
- Review alert effectiveness

### 8.2 Metrics to Track

```python
monthly_metrics = {
    "availability": "99.5%",
    "avg_duration": "6.5 minutes",
    "cost_per_run": "$0.15",
    "quality_score": "98/100",
    "incidents": 2,
    "mttr": "25 minutes"  # Mean Time To Resolution
}
```

---

## Implementation Checklist

- [ ] Set up Airflow alerting callbacks
- [ ] Set up email SMTP
- [ ] Create Grafana dashboard
- [ ] Implement extended quality checks
- [ ] Document runbooks
- [ ] Test alert channels
- [ ] Train team on incident response
- [ ] Schedule monthly reviews
- [ ] Set up cost tracking

## References

- [Airflow Monitoring](https://airflow.apache.org/docs/apache-airflow/stable/logging-monitoring/index.html)
- [Data Quality Patterns](https://www.datakitchen.io/data-quality-patterns)
- [SRE Best Practices](https://sre.google/workbook/alerting-on-slos/)
