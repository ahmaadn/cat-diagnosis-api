from enum import StrEnum, auto


class ErrorCode(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values) -> str:
        return name.upper()

    # APP ERROR
    APP_ERROR = auto()
    INTERNAL_SERVER_ERROR = auto()
    INTEGRITY_ERROR = auto()

    # BASE
    NOT_FOUND = auto()
    DUPLICATE_ID = auto()
    DUPLICATE_NAMA = auto()
    NOT_VALID_ID = auto()

    # PAKAR
    PAKAR_NOT_FOUND = auto()
    ID_PAKAR_DUPLICATE = auto()
    NAMA_PAKAR_DUPLICATE = auto()
    NOT_VALID_ID_PAKAR = auto()

    # PENYAKIT
    PENYAKIT_NOT_FOUND = auto()
    ID_PENYAKIT_DUPLICATE = auto()
    NAMA_PENYAKIT_DUPLICATE = auto()
    NOT_VALID_ID_PENYAKIT = auto()

    # GEJALA
    GEJALA_NOT_FOUND = auto()
    ID_GEJALA_DUPLICATE = auto()
    NAMA_GEJALA_DUPLICATE = auto()
    NOT_VALID_ID_GEJALA = auto()

    # KELOMPOK
    KELOMPOK_NOT_FOUND = auto()
    ID_KELOMPOK_DUPLICATE = auto()
    NAMA_KELOMPOK_DUPLICATE = auto()
    NOT_VALID_ID_KELOMPOK = auto()
