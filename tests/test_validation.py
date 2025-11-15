import pytest
from pydantic import ValidationError

from app.schemas import UpsellRequest


VALID_PAYLOAD = {
    "age": 30,
    "tenure_months": 12,
    "monthly_spend": 99.5,
    "num_support_tickets": 1,
}


def test_valid_payload():
    data = UpsellRequest(**VALID_PAYLOAD)
    assert data.age == 30


def test_missing_field():
    incomplete = VALID_PAYLOAD.copy()
    incomplete.pop("monthly_spend")
    with pytest.raises(ValidationError):
        UpsellRequest(**incomplete)


def test_extra_field():
    extra = VALID_PAYLOAD | {"foo": "bar"}
    with pytest.raises(ValidationError):
        UpsellRequest(**extra)


def test_wrong_type():
    wrong = VALID_PAYLOAD | {"age": "thirty"}
    with pytest.raises(ValidationError):
        UpsellRequest(**wrong)


def test_out_of_range_values():
    invalid = VALID_PAYLOAD | {"monthly_spend": -10}
    with pytest.raises(ValidationError):
        UpsellRequest(**invalid)
