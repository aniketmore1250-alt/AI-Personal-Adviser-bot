from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlparse


class ValidationError(ValueError):
    pass


def parse_money(value, *, allow_zero=False):
    try:
        amount = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        raise ValidationError("Enter a valid amount.")
    if amount < 0 or (amount == 0 and not allow_zero):
        raise ValidationError("Amount must be greater than zero.")
    if amount.quantize(Decimal("0.01")) != amount:
        raise ValidationError("Use no more than two decimal places.")
    return amount.quantize(Decimal("0.01"))


def parse_date(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValidationError("Choose a valid date.")


def parse_month(value):
    try:
        parsed = datetime.strptime(str(value), "%Y-%m")
        return parsed.strftime("%Y-%m")
    except (TypeError, ValueError):
        raise ValidationError("Choose a valid month.")


def current_month():
    return date.today().strftime("%Y-%m")


def clean_text(value, fallback=""):
    return " ".join(str(value or fallback).strip().split())


def safe_next_url(target):
    if not target:
        return None
    host_url = urlparse(urljoin("http://localhost", target))
    if host_url.netloc and host_url.netloc != "localhost":
        return None
    return host_url.path or "/"
