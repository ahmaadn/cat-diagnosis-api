from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from sqlalchemy.exc import SQLAlchemyError

from app.db.factories.base import AsyncFactory


class Seeder:
    def __init__(self):
        self.factories = []
        self.clear_factories = []
        self.results = {}
        self.console = Console()

    async def seed(self):
        """
        Run the seeding process for all factories.
        """
        self.console.print("[blue]Starting seeding process...[/]")

        for kwargs in self.factories:
            factory: AsyncFactory = kwargs.pop("factory")
            size = kwargs.pop("size")
            model_name = factory._meta.model.__name__  # noqa: SLF001

            self.console.print(
                f"[yellow]Seeding {size} records for {model_name}...[/]"
            )
            try:
                with self.progress_bar() as progress:
                    progress.add_task(
                        f"Creating {size} {model_name} records...", total=None
                    )
                    objects = await factory.create_batch(size, **kwargs)

                self.results[model_name] = objects
                self.console.print(
                    f"[green]Successfully seeded {size} records for {model_name}.[/]",  # noqa: E501
                    end="\n\n",
                )
            except Exception as e:
                self.console.print(
                    f"[red]Error seeding {factory.__name__}: {e!s}[/]"
                )
                raise

    async def clear_all(self):
        """
        Clear all data from all tables associated with the factories.
        """
        self.console.print("[blue]Clearing all data from the database...[/]")
        for factory in self.clear_factories:
            await self.clear(factory)

    async def clear(self, factory: AsyncFactory):
        model_name = factory._meta.model.__name__  # noqa: SLF001
        try:
            await factory.clear()
        except SQLAlchemyError as e:
            self.console.print(f"[red]Error clearing table '{model_name}': {e!s}[/]")

    @staticmethod
    def progress_bar():
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            expand=True,
            transient=True,
        )
