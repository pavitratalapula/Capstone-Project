import json
import uuid
from decimal import Decimal

import pytest

import src.expense_tracker as expense_tracker
from src.expense_tracker import (
    ExpenseDataError,
    ExpenseStorageError,
    ExpenseTracker,
    load_expenses,
    main,
    save_expenses,
)


def test_add_persists_and_round_trips_insertion_order(tmp_path):
    path = tmp_path / "nested" / "expenses.json"
    tracker = ExpenseTracker(path)
    tracker.add_expense("  Coffee  ", Decimal("4.500000000000000001"))
    tracker.add_expense("Groceries", "45.00", " food ")

    reloaded = ExpenseTracker(path)
    expenses = reloaded.list_expenses()
    assert [(e.description, e.amount, e.category) for e in expenses] == [
        ("Coffee", Decimal("4.500000000000000001"), "Other"),
        ("Groceries", Decimal("45.00"), "Food"),
    ]
    assert all(uuid.UUID(expense.id) for expense in expenses)
    assert json.loads(path.read_text(encoding="utf-8"))[0]["id"] == expenses[0].id
    assert reloaded.total() == Decimal("49.500000000000000001")
    assert json.loads(path.read_text(encoding="utf-8"))[0]["amount"] == "4.500000000000000001"


def test_filtering_is_case_insensitive_and_empty_categories_total_zero(tmp_path):
    tracker = ExpenseTracker(tmp_path / "expenses.json")
    tracker.add_expense("Train", Decimal("12.50"), "Travel")
    tracker.add_expense("Lunch", Decimal("10"), "food")

    assert [e.description for e in tracker.list_expenses(" FOOD ")] == ["Lunch"]
    assert tracker.total("shopping") == Decimal("0")


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-1"), "nope", "NaN", "Infinity"])
def test_rejects_invalid_amounts(tmp_path, amount):
    with pytest.raises(ValueError):
        ExpenseTracker(tmp_path / "expenses.json").add_expense("Item", amount)


def test_rejects_float_amounts_explicitly(tmp_path):
    with pytest.raises(ValueError, match="floats are not supported"):
        ExpenseTracker(tmp_path / "expenses.json").add_expense("Item", 1.25)


def test_rejects_blank_descriptions_and_unknown_categories(tmp_path):
    tracker = ExpenseTracker(tmp_path / "expenses.json")
    with pytest.raises(ValueError, match="Description"):
        tracker.add_expense(" \n ", Decimal("1"))
    with pytest.raises(ValueError, match="Category"):
        tracker.add_expense("Item", Decimal("1"), "Entertainment")


def test_rejects_non_string_categories(tmp_path):
    tracker = ExpenseTracker(tmp_path / "expenses.json")
    with pytest.raises(ValueError, match="Category"):
        tracker.add_expense("Item", Decimal("1"), 123)
    with pytest.raises(ValueError, match="Category"):
        tracker.list_expenses(category=123)


def test_missing_file_is_empty(tmp_path):
    assert load_expenses(tmp_path / "missing.json") == []


def test_existing_empty_file_is_reported_as_malformed(tmp_path):
    path = tmp_path / "expenses.json"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ExpenseDataError, match="Malformed JSON"):
        load_expenses(path)


def test_load_wraps_non_missing_os_errors(tmp_path, monkeypatch):
    path = tmp_path / "expenses.json"

    def fail_open(*args, **kwargs):
        raise PermissionError("permission denied")

    monkeypatch.setattr(expense_tracker.Path, "open", fail_open)
    with pytest.raises(ExpenseStorageError, match="Could not read expense data"):
        load_expenses(path)


def test_load_wraps_invalid_utf8_with_path(tmp_path):
    path = tmp_path / "expenses.json"
    path.write_bytes(b"\xff")

    with pytest.raises(ExpenseDataError, match="Could not decode expense data") as exc_info:
        load_expenses(path)
    assert str(path) in str(exc_info.value)


def test_malformed_and_structurally_invalid_data_are_reported_without_replacement(tmp_path):
    path = tmp_path / "expenses.json"
    path.write_text("{not json", encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(ExpenseDataError, match="Malformed JSON"):
        load_expenses(path)
    assert path.read_bytes() == original

    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ExpenseDataError, match="root must be an array"):
        load_expenses(path)


def test_save_is_deterministic_utf8(tmp_path):
    path = tmp_path / "expenses.json"
    tracker = ExpenseTracker(path)
    tracker.add_expense("Café", Decimal("2.10"))
    first = path.read_bytes()
    save_expenses(path, load_expenses(path))
    assert path.read_bytes() == first
    assert "Café" in path.read_text(encoding="utf-8")


def test_failed_replacement_preserves_existing_file(tmp_path, monkeypatch):
    path = tmp_path / "expenses.json"
    tracker = ExpenseTracker(path)
    tracker.add_expense("Original", Decimal("1"))
    original = path.read_bytes()

    def fail_replace(source, destination):
        raise OSError("replacement failed")

    monkeypatch.setattr(expense_tracker.os, "replace", fail_replace)
    with pytest.raises(expense_tracker.ExpenseStorageError, match="Could not save"):
        save_expenses(path, [expense_tracker.Expense("New", Decimal("2"))])
    assert path.read_bytes() == original


def test_failed_temporary_file_cleanup_is_reported(tmp_path, monkeypatch):
    path = tmp_path / "expenses.json"
    tracker = ExpenseTracker(path)
    tracker.add_expense("Original", Decimal("1"))
    original = path.read_bytes()

    def fail_replace(source, destination):
        raise OSError("replacement failed")

    original_unlink = expense_tracker.Path.unlink

    def fail_temporary_unlink(temporary_path, *args, **kwargs):
        if temporary_path.suffix == ".tmp":
            raise OSError("cleanup failed")
        original_unlink(temporary_path, *args, **kwargs)

    monkeypatch.setattr(expense_tracker.os, "replace", fail_replace)
    monkeypatch.setattr(expense_tracker.Path, "unlink", fail_temporary_unlink)
    with pytest.raises(ExpenseStorageError) as exc_info:
        save_expenses(path, [expense_tracker.Expense("New", Decimal("2"))])

    assert "replacement failed" in str(exc_info.value)
    assert "cleanup failed" in str(exc_info.value)
    assert path.read_bytes() == original


def test_cli_add_list_and_total_use_explicit_data_path(tmp_path, capsys):
    path = tmp_path / "expenses.json"
    assert main(["--data", str(path), "add", "Coffee", "4.50"]) == 0
    assert main(["--data", str(path), "list", "--category", "other"]) == 0
    assert main(["--data", str(path), "total"]) == 0
    assert "Coffee" in capsys.readouterr().out


def test_new_expense_ids_are_unique_and_persisted(tmp_path):
    path = tmp_path / "expenses.json"
    tracker = ExpenseTracker(path)
    first = tracker.add_expense("First", "1")
    second = tracker.add_expense("Second", "2")

    assert first.id != second.id
    assert [expense.id for expense in ExpenseTracker(path).list_expenses()] == [first.id, second.id]


def test_legacy_records_get_deterministic_ids_and_migrate_on_write(tmp_path):
    path = tmp_path / "expenses.json"
    path.write_text(
        json.dumps(
            [
                {"amount": "1.00", "category": "Food", "description": "Lunch"},
                {"amount": "1.00", "category": "Food", "description": "Lunch"},
            ]
        ),
        encoding="utf-8",
    )

    first_load = load_expenses(path)
    second_load = load_expenses(path)
    assert [expense.id for expense in first_load] == [expense.id for expense in second_load]
    assert first_load[0].id != first_load[1].id
    assert set(json.loads(path.read_text(encoding="utf-8"))[0]) == {"amount", "category", "description"}

    ExpenseTracker(path).add_expense("Snack", "2")
    migrated = json.loads(path.read_text(encoding="utf-8"))
    assert all(set(record) == {"id", "amount", "category", "description"} for record in migrated)
    assert [record["id"] for record in migrated[:2]] == [expense.id for expense in first_load]


def test_edit_legacy_expense_by_migrated_id_preserves_all_records(tmp_path):
    path = tmp_path / "expenses.json"
    path.write_text(
        json.dumps(
            [
                {"amount": "1.00", "category": "Food", "description": "Lunch"},
                {"amount": "2.00", "category": "Travel", "description": "Train"},
            ]
        ),
        encoding="utf-8",
    )

    legacy_expenses = load_expenses(path)
    edited = ExpenseTracker(path).edit_expense(legacy_expenses[0].id, description="Dinner")

    assert edited.id == legacy_expenses[0].id
    migrated = json.loads(path.read_text(encoding="utf-8"))
    assert len(migrated) == 2
    assert migrated[0]["id"] == legacy_expenses[0].id
    assert migrated[0]["description"] == "Dinner"
    assert migrated[1]["description"] == "Train"


def test_edit_expense_supports_partial_and_multiple_field_updates(tmp_path):
    path = tmp_path / "expenses.json"
    tracker = ExpenseTracker(path)
    first = tracker.add_expense("Lunch", "10", "Food")
    tracker.add_expense("Train", "5", "Shopping")

    edited = tracker.edit_expense(first.id, description="Dinner")
    assert edited.id == first.id
    assert edited.description == "Dinner"
    assert edited.amount == Decimal("10")
    assert edited.category == "Food"
    assert [expense.id for expense in tracker.list_expenses()] == [first.id, tracker.list_expenses()[1].id]

    edited = tracker.edit_expense(first.id, amount="12.50", category=" travel ")
    assert (edited.amount, edited.category) == (Decimal("12.50"), "Travel")
    reloaded = ExpenseTracker(path)
    assert reloaded.total() == Decimal("17.50")
    assert reloaded.total("TRAVEL") == Decimal("12.50")


@pytest.mark.parametrize(
    "edit_kwargs",
    [
        {},
        {"description": " "},
        {"amount": "0"},
        {"amount": 1.25},
        {"category": "Leisure"},
    ],
)
def test_edit_rejects_invalid_input_without_changing_file(tmp_path, edit_kwargs):
    path = tmp_path / "expenses.json"
    tracker = ExpenseTracker(path)
    expense = tracker.add_expense("Original", "10", "Food")
    original = path.read_bytes()

    with pytest.raises(ValueError):
        tracker.edit_expense(expense.id, **edit_kwargs)
    assert path.read_bytes() == original


def test_edit_rejects_unknown_malformed_and_duplicate_ids(tmp_path):
    path = tmp_path / "expenses.json"
    tracker = ExpenseTracker(path)
    expense = tracker.add_expense("Original", "10")

    with pytest.raises(expense_tracker.ExpenseNotFoundError):
        tracker.edit_expense("not-a-uuid", description="Changed")
    with pytest.raises(expense_tracker.ExpenseNotFoundError):
        tracker.edit_expense(str(uuid.uuid4()), description="Changed")

    duplicate = {
        "id": expense.id,
        "amount": "2",
        "category": "Food",
        "description": "Duplicate",
    }
    path.write_text(json.dumps([json.loads(path.read_text())[0], duplicate]), encoding="utf-8")
    with pytest.raises(ExpenseDataError, match="unique"):
        load_expenses(path)


def test_edit_raises_not_found_when_ledger_is_absent(tmp_path):
    path = tmp_path / "missing.json"
    tracker = ExpenseTracker(path)
    with pytest.raises(expense_tracker.ExpenseNotFoundError, match="Expense ID not found"):
        tracker.edit_expense(str(uuid.uuid4()), description="Changed")
    assert not path.exists()


def test_edit_raises_not_found_when_ledger_is_empty_and_file_is_untouched(tmp_path):
    path = tmp_path / "expenses.json"
    path.write_text("[]", encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(expense_tracker.ExpenseNotFoundError, match="Expense ID not found"):
        ExpenseTracker(path).edit_expense(str(uuid.uuid4()), description="Changed")
    assert path.read_bytes() == original


def test_edit_raises_data_error_when_ledger_is_malformed_and_file_is_untouched(tmp_path):
    path = tmp_path / "expenses.json"
    path.write_text("{broken", encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(ExpenseDataError, match="Malformed JSON"):
        ExpenseTracker(path).edit_expense(str(uuid.uuid4()), description="Changed")
    assert path.read_bytes() == original


def test_failed_edit_replacement_preserves_existing_file(tmp_path, monkeypatch):
    path = tmp_path / "expenses.json"
    tracker = ExpenseTracker(path)
    expense = tracker.add_expense("Original", "1")
    original = path.read_bytes()

    def fail_replace(source, destination):
        raise OSError("replacement failed")

    monkeypatch.setattr(expense_tracker.os, "replace", fail_replace)
    with pytest.raises(ExpenseStorageError):
        tracker.edit_expense(expense.id, description="Changed")
    assert path.read_bytes() == original


def test_cli_edit_and_list_include_ids(tmp_path, capsys):
    path = tmp_path / "expenses.json"
    assert main(["--data", str(path), "add", "Coffee", "4.50"]) == 0
    added_output = capsys.readouterr().out
    expense_id = added_output.removeprefix("Added: ").split(":", 1)[0]
    assert uuid.UUID(expense_id)

    assert main(["--data", str(path), "edit", expense_id, "--description", "Latte"]) == 0
    assert "Updated:" in capsys.readouterr().out
    assert main(["--data", str(path), "list"]) == 0
    listed = capsys.readouterr().out
    assert expense_id in listed
    assert "Latte" in listed


def test_cli_edit_requires_at_least_one_option(tmp_path):
    path = tmp_path / "expenses.json"

    with pytest.raises(SystemExit):
        main(["--data", str(path), "edit", str(uuid.uuid4())])


def test_cli_edit_unknown_id_returns_nonzero_and_stderr(tmp_path, capsys):
    path = tmp_path / "expenses.json"
    assert main(["--data", str(path), "add", "Coffee", "4.50"]) == 0
    capsys.readouterr()
    assert main(["--data", str(path), "edit", str(uuid.uuid4()), "--description", "Changed"]) == 1
    assert "Expense ID not found" in capsys.readouterr().err


@pytest.mark.parametrize(
    "extra_argv, expected_err_fragment",
    [
        (["--description", " "], "Description"),
        (["--category", "Leisure"], "Category"),
    ],
)
def test_cli_edit_invalid_field_returns_nonzero_and_stderr(tmp_path, capsys, extra_argv, expected_err_fragment):
    path = tmp_path / "expenses.json"
    assert main(["--data", str(path), "add", "Coffee", "4.50"]) == 0
    added_out = capsys.readouterr().out
    expense_id = added_out.removeprefix("Added: ").split(":", 1)[0]
    assert main(["--data", str(path), "edit", expense_id] + extra_argv) == 1
    assert expected_err_fragment in capsys.readouterr().err


@pytest.mark.parametrize(
    "payload",
    [
        [{"id": str(uuid.uuid4()), "amount": "1", "category": "Food"}],
        [{"id": str(uuid.uuid4()), "amount": 1, "category": "Food", "description": "Item"}],
        [{"id": str(uuid.uuid4()), "amount": "1", "category": "Food", "description": "Item", "extra": True}],
        [{}],
    ],
)
def test_repository_rejects_invalid_record_shapes(tmp_path, payload):
    path = tmp_path / "expenses.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ExpenseDataError):
        load_expenses(path)


def test_cli_reports_malformed_json_without_replacing_file(tmp_path, capsys):
    path = tmp_path / "expenses.json"
    path.write_text("{broken", encoding="utf-8")
    original = path.read_bytes()

    assert main(["--data", str(path), "total"]) == 1
    captured = capsys.readouterr()
    assert "Malformed JSON" in captured.err
    assert str(path) in captured.err
    assert path.read_bytes() == original


def test_cli_missing_storage_is_a_successful_empty_ledger(tmp_path, capsys):
    path = tmp_path / "not-created-yet" / "expenses.json"

    assert main(["--data", str(path), "list"]) == 0
    assert capsys.readouterr().out == "Total: 0\n"
    assert not path.exists()


def test_cli_rejects_unknown_category_without_creating_storage(tmp_path, capsys):
    path = tmp_path / "expenses.json"

    assert main(["--data", str(path), "add", "Coffee", "4.50", "--category", "Leisure"]) == 1
    captured = capsys.readouterr()
    assert "Category" in captured.err
    assert not path.exists()
