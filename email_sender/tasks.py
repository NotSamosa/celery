import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail, send_mass_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject, message, recipient_list, html_message=None):
    """
    Celery task to send a single or multi-recipient email asynchronously with retries and logging.
    """
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]

    logger.info(
        f"[Task {self.request.id}] Attempting to send email to {recipient_list} with subject '{subject}'"
    )

    # Validate email addresses
    valid_recipients = []
    for email in recipient_list:
        try:
            validate_email(email)
            valid_recipients.append(email)
        except ValidationError:
            logger.warning(f"[Task {self.request.id}] Invalid email address skipped: {email}")

    if not valid_recipients:
        error_msg = "No valid recipients found in recipient_list."
        logger.error(f"[Task {self.request.id}] {error_msg}")
        return {
            "status": "failed",
            "error": error_msg,
            "task_id": self.request.id,
        }

    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=valid_recipients,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"[Task {self.request.id}] Successfully sent email to {valid_recipients}. Count: {sent_count}"
        )
        return {
            "status": "success",
            "recipients": valid_recipients,
            "subject": subject,
            "sent_count": sent_count,
            "task_id": self.request.id,
        }

    except Exception as exc:
        retry_count = self.request.retries
        logger.error(
            f"[Task {self.request.id}] Error sending email to {valid_recipients}: {str(exc)}. "
            f"Retry {retry_count}/{self.max_retries}"
        )
        try:
            # Exponential backoff: 60s, 120s, 240s
            countdown = 60 * (2 ** retry_count)
            raise self.retry(exc=exc, countdown=countdown)
        except self.MaxRetriesExceededError:
            logger.critical(
                f"[Task {self.request.id}] Max retries exceeded when sending email to {valid_recipients}."
            )
            return {
                "status": "failed",
                "error": str(exc),
                "task_id": self.request.id,
                "retries": retry_count,
            }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_bulk_email_task(self, subject, message, recipient_list):
    """
    Celery task to send bulk emails efficiently.
    """
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]

    logger.info(
        f"[Task {self.request.id}] Sending bulk emails to {len(recipient_list)} recipients..."
    )

    from_email = settings.DEFAULT_FROM_EMAIL
    messages = [
        (subject, message, from_email, [email])
        for email in recipient_list
    ]

    try:
        sent_count = send_mass_mail(tuple(messages), fail_silently=False)
        logger.info(f"[Task {self.request.id}] Sent {sent_count} bulk emails successfully.")
        return {
            "status": "success",
            "total_recipients": len(recipient_list),
            "sent_count": sent_count,
            "task_id": self.request.id,
        }
    except Exception as exc:
        logger.error(f"[Task {self.request.id}] Failed sending bulk emails: {str(exc)}")
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "error": str(exc),
                "task_id": self.request.id,
            }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email_task(self, user_email, username):
    """
    Celery task to send a formatted welcome onboarding email to a newly registered user.
    """
    subject = f"Welcome to our platform, {username}!"
    message = (
        f"Hi {username},\n\n"
        "Thank you for joining us! Your account has been registered successfully.\n\n"
        "Best regards,\nThe Team"
    )
    html_message = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
          <h2 style="color: #2b6cb0;">Welcome to our platform, {username}! 👋</h2>
          <p>Thank you for signing up. Your account has been created and is ready to use.</p>
          <div style="background-color: #f7fafc; padding: 15px; border-radius: 6px; margin: 20px 0;">
            <strong>Username:</strong> {username}<br>
            <strong>Registered Email:</strong> {user_email}
          </div>
          <p>If you have any questions, feel free to reply to this email.</p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
          <p style="font-size: 12px; color: #718096;">This is an automated background email sent via Celery & Redis.</p>
        </div>
      </body>
    </html>
    """
    return send_email_task.apply_async(
        args=[subject, message, [user_email]],
        kwargs={"html_message": html_message},
    ).id


@shared_task(bind=True)
def send_scheduled_report_task(self, recipient_email=None):
    """
    Periodic task to compile and send a task execution summary report.
    """
    from django_celery_results.models import TaskResult
    from django.utils import timezone

    if not recipient_email:
        recipient_email = settings.DEFAULT_FROM_EMAIL

    total_tasks = TaskResult.objects.count()
    success_tasks = TaskResult.objects.filter(status="SUCCESS").count()
    failed_tasks = TaskResult.objects.filter(status="FAILURE").count()
    now_local = timezone.localtime(timezone.now())

    subject = f"Periodic System Report - {now_local.strftime('%Y-%m-%d %H:%M %Z')}"
    message = (
        f"Celery Execution Summary Report\n"
        f"Generated at: {now_local.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n"
        f"Total Recorded Tasks: {total_tasks}\n"
        f"Successful Tasks: {success_tasks}\n"
        f"Failed Tasks: {failed_tasks}\n"
    )

    logger.info(f"[Periodic Report] Sending report to {recipient_email}...")
    return send_email_task.apply(
        args=[subject, message, [recipient_email]]
    ).get()


