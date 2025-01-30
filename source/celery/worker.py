from celery import Celery
from celery.signals import setup_logging as celery_setup_logging
from source.config import Config
from source.log import setup_logging

celery_app = Celery(
    main="celery-worker",
    broker=Config.REDIS_DSN,
    backend=Config.POSTGRESQL_DSN,
    task_track_started=True,
    include=["source.celery.entropy_tasks"],
)


@celery_setup_logging.connect()
def setup_celery_logger(**_):
    setup_logging(log_filename="celery.log")