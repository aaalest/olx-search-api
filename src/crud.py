from sqlmodel import Session, select
from db.models import Offers


def upsert_offer(session: Session, offer: Offers) -> Offers:
    session.merge(offer)
    session.commit()
    return offer
