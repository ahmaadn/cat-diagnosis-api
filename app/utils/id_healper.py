from dataclasses import dataclass
from typing import ClassVar, Generic, Sequence, Set, Tuple, TypeVar

ModelType = TypeVar("ModelType")


@dataclass
class IDConfig:
    """Configuration for ID generation and validation"""

    prefix: str
    length: int
    minimum_length_number: int
    example: str
    error_messages: ClassVar[dict[str, str]] = {
        "length": "ID harus memiliki panjang {length} karakter",
        "prefix": "ID harus dimulai dengan {prefix}",
        "numeric": "Bagian angka harus berisi digit",
        "duplicate": "ID {id} sudah digunakan",
        "invalid": "ID tidak valid. Contoh: {example}",
    }


class IDHelper(Generic[ModelType]):
    """Handles ID validation, generation, and error handling"""

    def __init__(self, config: IDConfig, field_id: str = "id"):
        self.config = config
        self.field_id = field_id

    def get_id(self, item: ModelType) -> str:
        return getattr(item, self.field_id)

    def validate_format(self, id_value: str):
        """
        Validates the format of an ID
        Returns: (is_valid, error_message)
        """
        if len(id_value) > self.config.length:
            return False, self.config.error_messages["length"].format(
                length=self.config.length
            )

        if id_value.startswith(self.config.prefix) is False:
            return False, self.config.error_messages["prefix"].format(
                prefix=self.config.prefix
            )

        numeric_part = id_value[len(self.config.prefix) :]
        if not numeric_part.isdigit():
            return False, self.config.error_messages["numeric"]

        # if len(numeric_part) != self.config.numeric_length:
        #     return False, self.config.error_messages["length"].format(
        #         length=self.config.length
        #     )

        return True, ""

    def create_id(self, existing_ids: Set[str], nums_ids: Set[int]) -> str:
        """
        Creates a new unique ID
        Args:
            existing_ids: Set of existing IDs to avoid duplicates
            nums_ids: Set of numeric parts of existing IDs
        Returns:
            str: A new unique ID
        """
        if not nums_ids:
            return f"{self.config.prefix}{'0' * (self.config.minimum_length_number - 1)}1"

        # Try to fill gaps first
        expected = set(range(1, max(nums_ids) + 1))
        missing_nums = sorted(expected - nums_ids)

        if missing_nums:
            for num in missing_nums:
                i = str(num)
                if len(i) < self.config.minimum_length_number:
                    i = i.zfill(self.config.minimum_length_number)
                new_id = f"{self.config.prefix}{i}"
                if new_id not in existing_ids:
                    return new_id

        # No gaps found, create new sequential ID
        next_num = max(nums_ids) + 1
        while True:
            i = str(next_num)
            if len(i) <= self.config.minimum_length_number:
                i = i.zfill(self.config.minimum_length_number)
            new_id = f"{self.config.prefix}{i}"
            if new_id not in existing_ids:
                return new_id
            next_num += 1

    def extract_numeric_ids(
        self, items: Sequence[ModelType]
    ) -> Tuple[Set[str], Set[int]]:
        """
        Extracts IDs and their numeric parts from a sequence of items
        Args:
            items: Sequence of items with ID attributes
        Returns:
            Tuple[Set[str], Set[int]]: (existing IDs, numeric parts of IDs)
        """
        existing_ids: Set[str] = {self.get_id(item) for item in items}
        nums_ids: Set[int] = {
            int(self.get_id(item)[len(self.config.prefix) :]) for item in items
        }
        return existing_ids, nums_ids
