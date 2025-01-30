import logging

from source.celery.worker import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def celery_task():
    logger.info("celery")