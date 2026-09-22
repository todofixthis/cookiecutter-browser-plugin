from datetime import UTC, datetime
from json import dump, load


def main() -> None:
    context_filename = "cookiecutter.json"

    with open(context_filename, "r") as f_in:
        context_data: dict[str, str] = load(f_in)

    context_data.update(
        {
            "this_year": str(datetime.now(tz=UTC).date().year),
        }
    )

    with open(context_filename, "w") as f_out:
        dump(context_data, f_out, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
