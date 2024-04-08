# Standard Library
import io
import os
from collections.abc import Callable, Iterable
from datetime import date, timedelta
from typing import TYPE_CHECKING

# Django
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.db.models import Case, F, IntegerField, Q, Sum, Value, When
from django.http import HttpResponse
from django.template import loader
from django.template.loader import get_template
from django.urls import reverse

# Third Party
from django_fsm import FSMField, Transition, transition
from django_fsm_log.models import StateLog
from djmoney.models.fields import MoneyField
from djmoney.models.managers import money_manager
from mjml import mjml2html
from model_utils.fields import MonitorField
from moneyed import Money
from xhtml2pdf import pisa
from xhtml2pdf.context import pisaContext

# Locals
from ..decorators import save_after

if TYPE_CHECKING:
    # Locals
    from . import Charge, Customer


class InvoiceManager(models.Manager["Invoice"]):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                subtotal=Sum(F("charges__line") * F("charges__quantity")),
                total=F("adjustment") + F("subtotal"),
                overdue=Q(state=Invoice.States.UNPAID.value, due__lt=date.today()),
            )
        )


class Invoice(models.Model):
    charges: models.QuerySet["Charge"]
    payments: models.QuerySet["Payment"]
    get_available_state_transitions: Callable[[], Iterable[Transition]]

    class States(models.TextChoices):
        DRAFT = "draft"
        UNPAID = "unpaid"
        PAID = "paid"
        VOID = "void"

    details = models.TextField(blank=True, default="")
    due = models.DateField(blank=True, null=True, default=None)
    adjustment = MoneyField(max_digits=14, default=0.0)

    customer_name = models.CharField(max_length=255, blank=True, default="")
    sent_to = models.CharField(max_length=255, blank=True, default="")
    invoice_address = models.TextField(default="", blank=True)

    state = FSMField(default=States.DRAFT.value, choices=States.choices, protected=True)  # type: ignore
    paid_on = MonitorField(monitor="state", when=[States.PAID.value], default=None, null=True)  # type: ignore
    sent_on = MonitorField(monitor="state", when=[States.UNPAID.value], default=None, null=True)  # type: ignore

    send_notes = models.TextField(blank=True, null=True, default="")  # noqa: DJ001

    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    _can_edit = False

    customer: models.ForeignKey["Customer|None"] = models.ForeignKey(
        "cerberus.Customer",
        on_delete=models.SET_NULL,
        null=True,
        related_name="invoices",
    )

    objects = money_manager(InvoiceManager())

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.can_edit:
            all_fields = {f.name for f in self._meta.concrete_fields if not f.primary_key}
            excluded = (
                "invoice",
                "details",
                "sent_to",
                "adjustment",
                "adjustment_currency",
                "customer_name",
                "due",
                "adjustment",
            )
            kwargs["update_fields"] = all_fields.difference(excluded)
        self._can_edit = False

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("invoice_detail", kwargs={"pk": self.pk})

    @classmethod
    def from_customer(cls, customer: "Customer"):
        invoice = cls(customer=customer, customer_name=customer.name, invoice_address=customer.invoice_address)
        invoice.save()
        return invoice

    def can_send(self) -> bool:
        return self.customer is not None and len(self.customer.issues) == 0

    def can_resend_email(self) -> bool:
        return self.can_send() and self.sent_to != ""

    @property
    def can_edit(self) -> bool:
        return self.state == self.States.DRAFT.value or self._can_edit

    @property
    def name(self) -> str:
        return f"INV-{self.pk:03}"

    @property
    def overdue(self) -> bool:
        return self.state == self.States.UNPAID.value and self.due is not None and self.due < date.today()

    @overdue.setter
    def overdue(self, value):
        pass

    @property
    def state_log(self):
        created = {
            "pk": 0,
            "timestamp": self.created,
            "source_state": None,
            "state": self.States.DRAFT,
            "transition": None,
            "description": "Created",
            "by": None,
        }
        created_log = StateLog(**created)

        return [created_log] + list(StateLog.objects.for_(self))  # type: ignore

    @save_after
    @transition(
        field=state,
        source=States.DRAFT.value,
        target=States.UNPAID.value,
        conditions=[can_send],
        custom={"icon": "icons/mail.svg", "url": "invoice_send"},
    )
    def send(self, to: str | None = None, send_email: bool = True, send_notes: str | None = None):
        if not self.customer:
            raise Exception("no customer set")
        self._can_edit = True
        self.customer_name = self.customer.name
        self.invoice_address = self.customer.invoice_address
        if self.due is None:
            self.due = date.today() + timedelta(weeks=1)

        self.send_notes = send_notes

        if send_email:
            self.sent_to = to or self.customer.invoice_email
            self.send_email([f"{self.customer.name} <{self.customer.invoice_email}>"])

    def resend_email(self):
        assert self.state == self.States.UNPAID.value, "Invoice must be unpaid to resend"
        assert self.sent_to, "No email address to send to"
        return self.send_email([self.sent_to])

    def send_email(self, to: list[str]):
        assert self.can_send(), "Unable to send email"

        html = loader.get_template("emails/invoice.mjml")
        txt = loader.get_template("emails/invoice.txt")

        context = {
            "invoice": self,
            "customer": self.customer,
            "send_notes": self.send_notes or "",
        }

        email = EmailMultiAlternatives(
            subject=f"Invoice {self.name} - Stretch there legs",
            body=txt.render(context),
            from_email="Stretch there legs - Accounts<admin@stretchtheirlegs.co.uk>",
            reply_to=["Stef <stef@stretchtheirlegs.co.uk>"],
            to=to,
        )

        dest = io.BytesIO()
        results = self.get_pdf(render_to=dest)
        if (err := getattr(results, "err", 0)) > 0:
            raise Exception(err)

        email.attach(f"{self.name}.pdf", dest.getvalue(), "application/pdf")
        email.attach_alternative(mjml2html(html.render(context)), "text/html")

        return email.send()

    @property
    def paid(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def unpaid(self):
        return (self.total or 0) - self.paid

    @save_after
    @transition(
        field=state,
        source=States.UNPAID.value,
        target=States.PAID.value,
        custom={"icon": "icons/pay.svg"},
    )
    def pay(self):
        for charge in self.charges.all():
            charge.pay()

        payment = Payment(invoice=self, amount=self.unpaid)
        payment.save()

    @save_after
    @transition(
        field=state,
        source=(States.DRAFT.value, States.UNPAID.value),  # type: ignore
        target=States.VOID.value,
        custom={"icon": "icons/invoice-void.svg"},
    )
    def void(self) -> None:
        pass

    def delete(self, force=False, *args, **kwargs) -> None:
        if self.state == self.States.DRAFT.value or force:
            super().delete(*args, **kwargs)
        else:
            self.void()

    @property
    def available_state_transitions(self) -> list[str]:
        return [i.name for i in self.get_available_state_transitions()]

    @property
    def issued(self):
        return self.sent_on or self.created

    def link_callback(self, uri, rel):
        """Convert HTML URIs to absolute system paths so xhtml2pdf can access
        those resources."""

        static_url = settings.STATIC_URL
        static_root = settings.STATIC_ROOT
        media_url = settings.MEDIA_URL
        media_root = settings.MEDIA_ROOT

        if result := finders.find(uri):
            if not isinstance(result, list | tuple):
                result = [result]
            result = [os.path.realpath(path) for path in result]
            path = result[0]
        elif uri.startswith(media_url):
            path = os.path.join(media_root, uri.replace(media_url, ""))
        elif uri.startswith(static_url):
            path = os.path.join(static_root, uri.replace(static_url, ""))
        else:
            return uri

        # make sure that file exists
        if not os.path.isfile(path):
            raise Exception(f"media URI must start with {static_url} or {media_url}")
        return path

    @property
    def subtotal(self) -> Money:
        return settings.DEFAULT_CURRENCY.zero + sum(c.amount for c in self.charges.all())

    @subtotal.setter
    def subtotal(self, value):
        pass

    @property
    def total(self) -> Money:
        return self.subtotal + self.adjustment

    @total.setter
    def total(self, _value):
        pass

    def get_pdf(self, render_to=None) -> pisaContext:
        template_path = "cerberus/invoice.html"
        context = {
            "invoice": self,
        }

        template = get_template(template_path)
        html = template.render(context)

        pdf = pisa.CreatePDF(html, dest=render_to, link_callback=self.link_callback)

        if not isinstance(pdf, pisaContext) or pdf.err > 0:
            raise Exception("Unable to create PDF")

        return pdf

    def get_pdf_response(self) -> HttpResponse:
        response = HttpResponse(
            content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{self.name}.pdf"'},
        )

        self.get_pdf(render_to=response)

        return response

    def add_open(self):
        o = InvoiceOpen(invoice=self)
        return o.save()

    @staticmethod
    def sort_state(queryset, dir):
        symbol = "-" if dir == "desc" else ""
        return queryset.annotate(
            state_order=Case(
                When(state=Invoice.States.DRAFT.value, then=Value(1)),
                When(state=Invoice.States.VOID.value, then=Value(2)),
                When(state=Invoice.States.PAID.value, then=Value(3)),
                When(state=Invoice.States.UNPAID.value, then=Value(4)),
                default=Value(5),
                output_field=IntegerField(),
            )
        ).order_by(f"{symbol}state_order", "due", "last_updated")


class InvoiceOpen(models.Model):
    opened = models.DateTimeField(auto_now_add=True, editable=False)
    invoice: models.ForeignKey["Invoice"] = models.ForeignKey(
        "cerberus.Invoice", on_delete=models.CASCADE, related_name="opens"
    )

    def __str__(self) -> str:
        return f"{self.invoice} opened at {self.opened}"


class Payment(models.Model):
    amount = MoneyField(max_digits=14, default=0.0)
    invoice: models.ForeignKey["Invoice|None"] = models.ForeignKey(
        "cerberus.Invoice",
        on_delete=models.PROTECT,
        null=True,
        related_name="payments",
        limit_choices_to={"state": Invoice.States.UNPAID.value},
    )

    customer: models.ForeignKey["Customer|None"] = models.ForeignKey(
        "cerberus.Customer",
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
    )

    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        constraints = [
            models.CheckConstraint(name="%(app_label)s_%(class)s_gte_0", check=models.Q(amount__gte=0)),
        ]

    def __str__(self) -> str:
        return f"{self.amount} for {self.invoice}"

    def save(self, *args, **kwargs) -> None:
        if self.customer is None and self.invoice and self.invoice.customer:
            self.customer = self.invoice.customer
        super().save(*args, **kwargs)
