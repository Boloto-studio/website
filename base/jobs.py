from django_apscheduler.models import DjangoJobExecution


def poll_youtube():
    print("Polling YouTube...")
    # TODO: Implement the actual YouTube polling logic here


def delete_old_job_executions(max_age=604_800):
    DjangoJobExecution.objects.delete_old_job_executions(max_age)
