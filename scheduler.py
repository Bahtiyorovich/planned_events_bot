from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.base import JobLookupError
from datetime import datetime, timedelta
import pytz


async def send_notification(user_id, event_name, context):
    """Foydalanuvchiga eslatma yuborish."""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📅 Eslatma: {event_name} tadbiri 5 daqiqadan so'ng boshlanadi!"
        )
    except Exception as e:
        print(f"Xato: {e}")


class Scheduler:
    def __init__(self):
        """Rejalashtiruvchi (scheduler) ishga tushiriladi."""
        # AsyncIOScheduler ni ishlatish
        self.scheduler = AsyncIOScheduler(jobstores={'default': MemoryJobStore()})
        self.scheduler.start()  # Schedulerni boshlash

    def schedule_event(self, user_id, event_name, event_time, context):
        """Tadbirni rejalashtirish."""
        job_id = f"{user_id}_{event_name}_{event_time}"
        # Eslatmani 5 daqiqa oldin yuborish uchun vaqtni hisoblash
        notify_time = event_time - timedelta(minutes=5)
        if notify_time > datetime.now():
            self.scheduler.add_job(
                send_notification,
                trigger='date',
                run_date=notify_time,
                args=[user_id, event_name, context],
                id=job_id,
                replace_existing=True
            )

    def remove_event(self, job_id):
        """Tadbirni rejalashtirishdan olib tashlash."""
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            print(f"Xato: {job_id} topilmadi.")

    def shutdown(self):
        """Schedulerni to'xtatish."""
        self.scheduler.shutdown()
