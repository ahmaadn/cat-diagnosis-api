# HOW TO RUN, IN ROOT FOLDER RUN TERMINAL
# python3 -m app.seeder
# or
# py -m app.seeder


from app.db.factories.kelompok_factory import KelompokFactory
from app.db.seed import Seeder


async def main(
    clear_all: bool = False,
    kelompok_count: int = 10,
):
    """
    Main function to handle seeding logic.

    Args:
        clear_all (bool): Whether to clear all data before seeding.
        user_count (int): Number of users to seed.
        admin_count (int): Number of admin users to seed.
        recipe_count (int): Number of recipes to seed.
    """
    seeder = Seeder()

    # Update factory sizes based on arguments
    seeder.factories = [
        {"factory": KelompokFactory, "size": kelompok_count},
    ]

    # Factory for clear
    seeder.clear_factories = [
        KelompokFactory,  # relasion first
        # include user and admin
    ]

    if clear_all:
        await seeder.clear_all()

    await seeder.seed()


if __name__ == "__main__":
    import fire

    fire.Fire(main)
