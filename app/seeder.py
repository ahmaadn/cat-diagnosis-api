# CARA MENJALANKAN, DARI ROOT DIREKTORI, JALANKAN DI TERMINAL:
# python3 -m app.seeder
# atau untuk membersihkan data terlebih dahulu:
# python3 -m app.seeder --clear_all=True

import csv
from pathlib import Path

import fire
from faker import Faker
from rich.console import Console
from rich.progress import track
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.base import async_session_maker
from app.db.models.gejala import Gejala
from app.db.models.kelompok import Kelompok
from app.db.models.kelompok_gejala import KelompokGejala
from app.db.models.pakar import Pakar
from app.db.models.penyakit import Penyakit
from app.db.models.rule import Rule
from app.db.models.rule_cf import RuleCf

# Inisialisasi console untuk output yang lebih baik
console = Console()
# Inisialisasi faker untuk data dummy regional Indonesia
fake = Faker("id_ID")

# Path ke direktori file CSV
CSV_DIR = Path(__file__).parent / "db/factories/file"


async def clear_database(session_maker: async_sessionmaker):
    """Menghapus semua data dari tabel dengan urutan yang benar."""
    console.print("\n[bold red]Menghapus data lama dari database...[/bold red]")
    tables_to_clear = [
        RuleCf,
        KelompokGejala,
        Rule,
        Gejala,
        Penyakit,
        Kelompok,
        Pakar,
    ]
    async with session_maker() as session:
        for table in track(
            tables_to_clear, description="[red]Menghapus tabel...[/red]"
        ):
            await session.execute(delete(table))
        await session.commit()
    console.print("[green]Database berhasil dibersihkan.[/green]")


def read_csv(file_path: Path) -> list[dict]:
    """Membaca file CSV dan mengembalikannya sebagai list of dictionaries."""
    with open(file_path, mode="r", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


async def seed_data(session_maker: async_sessionmaker):
    """Fungsi utama untuk mengisi database dari file CSV dan factory."""
    async with session_maker() as session:
        # 1. Seed Kelompok (Data statis diperbarui sesuai gambar)
        console.print("\n[bold cyan]1. Seeding Tabel Kelompok...[/bold cyan]")
        kelompok_data = [
            {
                "id": 1,
                "nama": "Gejala Umum",
                "deskripsi": "Gejala yang bersifat umum dan bisa ditemukan pada berbagai jenis penyakit.",
            },
            {
                "id": 2,
                "nama": "Gejala Saraf & Kepala",
                "deskripsi": "Gejala yang berkaitan dengan otak, sistem saraf, dan area kepala.",
            },
            {
                "id": 3,
                "nama": "Gejala Pernapasan & THT",
                "deskripsi": "Gejala yang berkaitan dengan sistem pernapasan dari hidung hingga paru-paru.",
            },
            {
                "id": 4,
                "nama": "Gejala Pencernaan",
                "deskripsi": "Gejala yang berhubungan dengan lambung, usus, dan sistem pencernaan lainnya.",
            },
            {
                "id": 5,
                "nama": "Gejala Otot, Tulang, & Sendi",
                "deskripsi": "Gejala yang dirasakan pada sistem gerak tubuh.",
            },
            {
                "id": 6,
                "nama": "Gejala Kulit & Rambut",
                "deskripsi": "Gejala yang tampak pada permukaan tubuh.",
            },
            {
                "id": 7,
                "nama": "Gejala Mata",
                "deskripsi": "Gejala yang spesifik pada indra penglihatan.",
            },
            {
                "id": 8,
                "nama": "Gejala Ginjal & Saluran Kemih",
                "deskripsi": "Gejala yang berhubungan dengan produksi dan pengeluaran urin.",
            },
            {
                "id": 9,
                "nama": "Gejala Psikologis & Perilaku",
                "deskripsi": "Gejala yang berkaitan dengan suasana hati dan kondisi mental.",
            },
        ]
        session.add_all([Kelompok(**data) for data in kelompok_data])
        await session.commit()
        console.print(
            f"[green]  -> {len(kelompok_data)} record Kelompok berhasil dibuat.[/green]"
        )

        # 2. Seed Pakar
        console.print("\n[bold cyan]2. Seeding Tabel Pakar...[/bold cyan]")
        pakar_list = read_csv(CSV_DIR / "daftar pakar.csv")
        session.add_all(
            [
                Pakar(id=p["id_pakar"].strip(), nama=p["nama_pakar"].strip())
                for p in pakar_list
            ]
        )
        await session.commit()
        console.print(
            f"[green]  -> {len(pakar_list)} record Pakar berhasil dibuat.[/green]"
        )

        # 3. Seed Penyakit (Hybrid: CSV + Faker untuk atribut yang kosong)
        console.print("\n[bold cyan]3. Seeding Tabel Penyakit...[/bold cyan]")
        penyakit_list_csv = read_csv(CSV_DIR / "daftar penyakit.csv")
        penyakit_to_add = [
            Penyakit(
                id=p["kode_penyakit"],
                nama=p["nama_penyakit"],
                deskripsi=fake.paragraph(nb_sentences=5),
                solusi=fake.paragraph(nb_sentences=4),
                pencegahan=fake.paragraph(nb_sentences=4),
                image_url=fake.image_url(),
            )
            for p in penyakit_list_csv
        ]
        session.add_all(penyakit_to_add)
        await session.commit()
        console.print(
            f"[green]  -> {len(penyakit_to_add)} record Penyakit berhasil dibuat.[/green]"
        )

        # Baca file gejala.csv yang lengkap
        gejala_list_csv = read_csv(CSV_DIR / "daftar gejala.csv")

        # 4. Seed Gejala (Menggunakan data lengkap dari CSV)
        console.print("\n[bold cyan]4. Seeding Tabel Gejala...[/bold cyan]")
        gejala_to_add = [
            Gejala(
                id=g["kode_gejala"],
                nama=g["nama_gejala"],
                deskripsi=g["deskripsi"],
                pertanyaan=f"Apakah kucing Anda menunjukkan gejala: {g['nama_gejala']}?",
                image_url=fake.image_url(),  # image_url tetap menggunakan faker
            )
            for g in gejala_list_csv
        ]
        session.add_all(gejala_to_add)
        await session.commit()
        console.print(
            f"[green]  -> {len(gejala_to_add)} record Gejala berhasil dibuat.[/green]"
        )

        # 5. Seed Relasi KelompokGejala (Langsung dari CSV)
        console.print(
            "\n[bold cyan]5. Seeding Relasi Kelompok-Gejala...[/bold cyan]"
        )
        kg_relations = []
        for g in gejala_list_csv:
            gejala_id = g["kode_gejala"]
            # Memisahkan ID kelompok jika ada lebih dari satu (dipisah ';')
            kelompok_ids_str = g.get("id_kelompok", "")
            if kelompok_ids_str:
                kelompok_ids = [
                    int(kid.strip())
                    for kid in kelompok_ids_str.split(";")
                    if kid.strip()
                ]
                for kelompok_id in kelompok_ids:
                    kg_relations.append(
                        KelompokGejala(id_gejala=gejala_id, id_kelompok=kelompok_id)
                    )

        session.add_all(kg_relations)
        await session.commit()
        console.print(
            f"[green]  -> {len(kg_relations)} relasi Kelompok-Gejala berhasil dibuat.[/green]"
        )

        # 6. Seed Rule
        console.print("\n[bold cyan]6. Seeding Tabel Rule...[/bold cyan]")
        rule_list = read_csv(CSV_DIR / "daftar rule.csv")
        session.add_all(
            [
                Rule(
                    id=r["id_rule"],
                    id_penyakit=r["kode_penyakit"],
                    id_gejala=r["kode_gejala_terkait"],
                )
                for r in rule_list
            ]
        )
        await session.commit()
        console.print(
            f"[green]  -> {len(rule_list)} record Rule berhasil dibuat.[/green]"
        )

        # 7. Seed RuleCf
        console.print("\n[bold cyan]7. Seeding Tabel Rule CF...[/bold cyan]")
        cf_list = read_csv(CSV_DIR / "daftar cf.csv")
        session.add_all(
            [
                RuleCf(
                    id_rule=cf["id_rule"],
                    id_pakar=cf["id_pakar"],
                    nilai=float(cf["nilai_cf"]),
                )
                for cf in cf_list
            ]
        )
        await session.commit()
        console.print(
            f"[green]  -> {len(cf_list)} record Rule CF berhasil dibuat.[/green]"
        )


async def main(clear_all: bool = False):
    """
    Fungsi utama untuk menjalankan proses seeding.

    Args:
        clear_all (bool): Jika True, hapus semua data sebelum seeding.
    """
    if clear_all:
        await clear_database(async_session_maker)

    await seed_data(async_session_maker)
    console.print("\n[bold green]Proses seeding selesai dengan sukses![/bold green]")


if __name__ == "__main__":
    fire.Fire(main)
