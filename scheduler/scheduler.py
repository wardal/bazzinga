import logging
from dataclasses import dataclass
from datetime import date, datetime

from dateutil.relativedelta import *
from dateutil.rrule import *
from django.utils.timezone import make_aware, make_naive

from .models import CustomerBaz, BazSendOut, Target

logger = logging.getLogger(__name__)


class Scheduler:
    TARGETS_PER_DAY_SECONDS = 480
    TARGETS_PER_DAY_HOURS = 11

    def run(self):
        for event in (
            CustomerBaz.objects.select_related("customer")
            .prefetch_related("customer__targets")
            .filter(finished=False)
        ):
            customer = event.customer
            baz = event.baz

            bazes_already_sent = BazSendOut.objects.filter(
                baz=baz, customer=customer, success=True
            ).only("datetime", "target_id")
            first_sent_baz = bazes_already_sent.first()
            first_sent_baz_datetime = (
                datetime.now()
                if not first_sent_baz
                else make_naive(first_sent_baz.datetime)
            )

            current_interval = self.get_current_interval(first_sent_baz_datetime)
            intervals_in_work = customer.interval - current_interval
            logger.warning(f"Current interval: {current_interval}")
            logger.warning(f"Intervals in work: {intervals_in_work}")

            targets_already_sent = bazes_already_sent.values_list(
                "target_id", flat=True
            )
            targets_to_send = (
                Target.objects.filter(customer=customer)
                .exclude(id__in=targets_already_sent)
                .order_by("id")
            )

            days_todo = self._get_intervals_working_days(
                first_sent_baz_datetime, customer.interval
            )
            targets_per_day = targets_to_send.count() // days_todo
            logger.warning(
                f"Still have {days_todo} days in campaign, bazes per day: {targets_per_day}"
            )

            targets_for_today = (
                targets_to_send.count() if days_todo == 1 else targets_per_day
            )
            baz_periods = iter(self.count_baz_periods(targets_for_today))
            logger.warning(f"Going to send {targets_for_today} emails today.")

            emails = [
                self._make_email(target, baz, next(baz_periods))
                for target in targets_to_send[:targets_for_today]
            ]
            self.mock_send_emails(emails, customer, baz, current_interval)

    @staticmethod
    def get_current_interval(first_time):
        return relativedelta(date.today(), datetime.date(first_time)).weeks + 1

    def count_baz_periods(self, targets_per_day):
        periods_rules = {
            "freq": 5,  # MINUTES
            "count": targets_per_day,
            "byhour": range(8, 18),
            "dtstart": date.today(),
            "until": date.today() + relativedelta(days=1),
        }

        if targets_per_day > self.TARGETS_PER_DAY_SECONDS:
            periods_rules.update({"freq": 6, "interval": 10})
        if targets_per_day < self.TARGETS_PER_DAY_HOURS:
            periods_rules.update({"freq": 4})

        return rrule(**periods_rules)

    def _get_intervals_working_days(self, first_time, intervals):
        return len(
            set(
                rrule(
                    DAILY,
                    count=31,
                    byweekday=(MO, TU, WE, TH, FR),
                    dtstart=date.today(),
                    until=self._get_intervals_last_day(first_time, intervals),
                )
            )
        )

    @staticmethod
    def _get_intervals_last_day(first_run: date, intervals: int):
        return first_run + relativedelta(weeks=intervals)

    @staticmethod
    def mock_send_emails(emails, customer, baz, interval):
        emails_list = []
        for email in emails:
            emails_list.append(
                BazSendOut(
                    target=email.target,
                    customer=customer,
                    baz=baz,
                    datetime=email.time,
                    interval=interval,
                    success=True,
                )
            )
            logger.warning(
                f"Prepare to send Email to:{email.target.email} time: {email.time} with content: {email.content}"
            )
        BazSendOut.objects.bulk_create(emails_list)

    @staticmethod
    def _make_email(target, baz, time):
        return Email(baz.content, target, make_aware(time))


@dataclass
class Email:
    content: str
    target: Target
    time: datetime
