from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.base import JobLookupError
from datetime import datetime, timedelta, timezone
import logging

# Loglar uchun sozlama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_notification(user_id, event_name, context):
    """Foydalanuvchiga eslatma yuborish."""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📅 Eslatma: {event_name} tadbiri 5 daqiqadan so'ng boshlanadi!"
        )
        logger.info(f"✅ Xabar yuborildi: {user_id} - {event_name}")
    except Exception as e:
        logger.error(f"❌ Xato xabar yuborishda: {e}")

class Scheduler:
    def __init__(self):
        """Rejalashtiruvchi (scheduler) ishga tushiriladi."""
        self.scheduler = AsyncIOScheduler(jobstores={'default': MemoryJobStore()})
        self.scheduler.start()  # Schedulerni boshlash
        logger.info("✅ Scheduler ishga tushirildi")

    def schedule_event(self, user_id, event_name, event_time, context, reminder_time):
        """Tadbirni rejalashtirish."""
        job_id = f"{user_id}_{event_name}_{event_time}"
        # Eslatma vaqtini hisoblash va UTC bilan ishlash
        notify_time = event_time - timedelta(minutes=reminder_time)
        if notify_time > datetime.now(timezone.utc):
            self.scheduler.add_job(
                send_notification,
                trigger='date',
                run_date=notify_time,
                args=[user_id, event_name, context],
                id=job_id,
                replace_existing=True
            )
            logger.info(f"✅ Tadbir rejalashtirildi: {job_id} - {notify_time}")
        else:
            logger.warning(f"❌ O'tmish vaqti uchun tadbir rejalashtirilmaydi: {notify_time}")

    def remove_event(self, job_id):
        """Tadbirni rejalashtirishdan olib tashlash."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"✅ Tadbir olib tashlandi: {job_id}")
        except JobLookupError:
            logger.error(f"❌ Tadbir topilmadi: {job_id}")

    def shutdown(self):
        """Schedulerni to'xtatish."""
        self.scheduler.shutdown()
        logger.info("✅ Scheduler to'xtatildi")
