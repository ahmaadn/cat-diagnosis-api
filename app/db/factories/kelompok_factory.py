import factory
import faker

from app.db.factories.base import AsyncFactory
from app.db.models.kelompok import Kelompok

fake = faker.Faker()


class KelompokFactory(AsyncFactory):
    class Meta:
        model = Kelompok

    nama = factory.LazyFunction(lambda: fake.unique.company())
    deskripsi = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
