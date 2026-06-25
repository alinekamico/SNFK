import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import settings

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def iniciar_scheduler(db_session_factory):
    from app.services.coleta_service import executar_coleta_todas_empresas

    scheduler.add_job(
        func=lambda: executar_coleta_todas_empresas(db_session_factory),
        trigger=IntervalTrigger(minutes=settings.COLLECTION_INTERVAL_MINUTES),
        id="coleta_fiscal",
        name="Coleta periódica de documentos fiscais",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler iniciado — coleta a cada {settings.COLLECTION_INTERVAL_MINUTES} minutos")


def parar_scheduler():
    if scheduler.running:
        scheduler.shutdown()
