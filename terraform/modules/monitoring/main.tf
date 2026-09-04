resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_sns_topic_subscription" "email_backup" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "pragashk14m@gmail.com"
}


# --- Alarm 1: Errors (ALB 5xx) ---
resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Triggers when the ALB sees more than 5 backend errors in a minute"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

# --- Alarm 2: Latency (ALB response time) ---
resource "aws_cloudwatch_metric_alarm" "alb_latency" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 2
  alarm_description   = "Triggers when average response time exceeds 2 seconds"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

# --- Alarm 3: Saturation (ASG CPU) ---
resource "aws_cloudwatch_metric_alarm" "asg_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-asg-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Triggers when average CPU across the ASG exceeds 80%"
  treat_missing_data  = "notBreaching"

  dimensions = {
    AutoScalingGroupName = var.asg_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "Pam-Kitchen-Dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 2
        properties = {
          markdown = "# 🍽️ PAM KITCHEN — Observability Dashboard\n**Domain:** pam-kitchen.online | **ASG:** ${var.asg_name} | **Region:** eu-west-3"
        }
      },
      {
        type   = "text"
        x      = 0
        y      = 2
        width  = 24
        height = 1
        properties = {
          markdown   = "## Golden Signals — Traffic & Errors"
          background = "transparent"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 3
        width  = 12
        height = 6
        properties = {
          title  = "Traffic — Request Count"
          region = "eu-west-3"
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", period = 60, color = "#1f77b4" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 3
        width  = 12
        height = 6
        properties = {
          title  = "Errors — 5XX Count"
          region = "eu-west-3"
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", period = 60, color = "#d62728" }]
          ]
        }
      },
      {
        type   = "text"
        x      = 0
        y      = 9
        width  = 24
        height = 1
        properties = {
          markdown   = "## Golden Signals — Latency & Saturation"
          background = "transparent"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 10
        width  = 8
        height = 6
        properties = {
          title  = "Latency — Target Response Time"
          region = "eu-west-3"
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix, { stat = "Average", period = 60, color = "#1f77b4" }],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix, { stat = "p95", period = 60, color = "#2ca02c" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 10
        width  = 8
        height = 6
        properties = {
          title  = "Saturation — ASG CPU Utilization"
          region = "eu-west-3"
          metrics = [
            ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", var.asg_name, { stat = "Average", period = 60, color = "#2ca02c" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 10
        width  = 8
        height = 6
        properties = {
          title  = "RDS CPU Utilization"
          region = "eu-west-3"
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.db_instance_id, { stat = "Average", period = 60, color = "#2ca02c" }]
          ]
        }
      },
      {
        type   = "alarm"
        x      = 0
        y      = 16
        width  = 24
        height = 4
        properties = {
          title = "Alarm Status"
          alarms = [
            aws_cloudwatch_metric_alarm.alb_5xx.arn,
            aws_cloudwatch_metric_alarm.alb_latency.arn,
            aws_cloudwatch_metric_alarm.asg_cpu.arn
          ]
        }
      },
      {
        type   = "text"
        x      = 0
        y      = 20
        width  = 24
        height = 1
        properties = {
          markdown   = "## Business Signals"
          background = "transparent"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 21
        width  = 12
        height = 6
        properties = {
          title  = "Orders Placed"
          region = "eu-west-3"
          metrics = [
            ["PamKitchen/Sales", "OrdersPlaced", { stat = "Sum", period = 300, color = "#2ca02c" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 21
        width  = 12
        height = 6
        properties = {
          title  = "Revenue (EUR)"
          region = "eu-west-3"
          metrics = [
            ["PamKitchen/Sales", "RevenueEUR", { stat = "Sum", period = 300, color = "#1f77b4" }]
          ]
        }
      },
      {
        type   = "text"
        x      = 0
        y      = 27
        width  = 24
        height = 2
        properties = {
          markdown = "---\n**Questions or issues?** Contact Pragash Kumaravel (Cloud/DevOps Engineer) at pragash_m@hotmail.co.uk | See `RUNBOOK.md` in the project repository for troubleshooting steps."
        }
      }
    ]
  })
}
