import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.booking import Booking, BookingStatus, BookingTableSlot
from tasks.celery_app import celery_app
from tasks.email_sender import send_email

from core.db import session_maker

logger = logging.getLogger(__name__)

REMINDER_TIMEDELTA = timedelta(hours=1)  # за сколько времени до бронирования отправлять напоминание


def schedule_booking_reminder(booking: Booking) -> None:
    """Планирует отправку напоминания пользователю о предстоящем бронировании."""
    if booking.status != BookingStatus.ACTIVE:
        return

    if not booking.tables_slots:
        return

    first_slot = min(
        booking.tables_slots,
        key=lambda ts: ts.slot.start_time,
    )

    booking_start = datetime.combine(
        booking.booking_date,
        first_slot.slot.start_time,
        tzinfo=timezone.utc,
    )

    eta = booking_start - REMINDER_TIMEDELTA

    if eta <= datetime.now(timezone.utc):
        return

    send_booking_reminder.apply_async(
        args=[booking.id],
        eta=eta,
        task_id=f'booking-reminder-{booking.id}',
    )
    logger.info(
        'Запланировано напоминание: booking_id=%d, eta=%s',
        booking.id,
        eta.isoformat(),
    )


@celery_app.task
def send_booking_reminder(booking_id: int) -> None:
    """Отправляет напоминание пользователю о предстоящем бронировании."""
    asyncio.run(_send_booking_reminder(booking_id))


async def _send_booking_reminder(booking_id: int) -> None:
    """Отправляет напоминание пользователю о предстоящем бронировании."""
    async with session_maker() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                selectinload(Booking.tables_slots).selectinload(
                    BookingTableSlot.slot,
                ),
                selectinload(Booking.user),
            ),
        )

        booking = result.scalar_one_or_none()

        if booking is None:
            return

        if booking.status not in (
            BookingStatus.BOOKING,
            BookingStatus.ACTIVE,
        ):
            return

        if not booking.tables_slots:
            return

        first_slot = min(
            booking.tables_slots,
            key=lambda ts: ts.slot.start_time,
        )

        subject = 'Напоминание о бронировании'
        body = (
            f'Напоминаем о вашем бронировании.\n\n'
            f'Номер бронирования: {booking.id}\n'
            f'Дата: {booking.booking_date}\n'
            f'Время: {first_slot.slot.start_time}'
        )

        send_email(
            booking.user.email,
            subject,
            body,
        )
        logger.info(
            'Отправлено напоминание: booking_id=%d, user_id=%d',
            booking.id,
            booking.user_id,
        )


@celery_app.task
def notify_admin(booking_id: int, user_id: int, action: str) -> None:
    """Уведомляет администратора о создании или изменении бронирования."""
    logger.info(
        'Уведомление админа: booking_id=%d, user_id=%d, action=%s',
        booking_id,
        user_id,
        action,
    )
