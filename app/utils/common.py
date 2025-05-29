from enum import StrEnum, auto


class ErrorCode(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values) -> str:
        return name.upper()

    APP_ERROR = auto()
    PAKAR_NOT_FOUND = auto()

    DUPLICATE_ID = auto()
    DUPLICATE_NAMA = auto()
    NOT_VALID_ID = auto()

    DUPLICATE_ID_PENYAKIT = auto()
    DUPLICATE_NAMA_PENYAKIT = auto()
    NOT_VALID_ID_PENYAKIT = auto()

    DUPLICATE_ID_GEJALA = auto()
    DUPLICATE_NAMA_GEJALA = auto()

    BULK_PENYAKIT_ERROR = auto()
    INTEGRITY_ERROR = auto()
