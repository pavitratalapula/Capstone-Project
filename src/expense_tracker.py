from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass, field as dataclass_field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

SUPPORTED_CATEGORIES = ("Food", "Travel", "Shopping", "Bills", "Other")
DEFAULT_DATA_PATH = Path("data/expenses.json")
LEGACY_ID_NAMESPACE = uuid.UUID("8b1f9f6a-1e0a-4cb1-9cb3-7d5e5f4c4f4a")
UNSET = object()


class ExpenseDataError(ValueError):
    """Raised when the ledger contains malformed or invalid data."""


class ExpenseStorageError(OSError):
    """Raised when the ledger cannot be read or written."""


class ExpenseNotFoundError(ValueError):
    """Raised when an expense ID cannot be resolved."""


class ExpenseArgumentParser(argparse.ArgumentParser):
    """Argument parser with edit-command validation."""

    def parse_args(
        self, args: list[str] | None = None, namespace: argparse.Namespace | None = None
    ) -> argparse.Namespace:
        parsed = super().parse_args(args, namespace)
        if (
            parsed.command == "edit"
            and parsed.description is None
            and parsed.amount is None
            and parsed.category is None
        ):
            self.error("edit requires at least one of --description, --amount, or --category")
        return parsed


def normalize_category(category: str | None) -> str:
    if category is None:
        return "Other"
    if not isinstance(category, str):
        raise ValueError(f"Category must be one of: {', '.join(SUPPORTED_CATEGORIES)}.")
    value = category.strip()
    for supported in SUPPORTED_CATEGORIES:
        if value.casefold() == supported.casefold():
            return supported
    raise ValueError(f"Category must be one of: {', '.join(SUPPORTED_CATEGORIES)}.")


def parse_decimal(value: Decimal | str | int | float) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("Amount must be a valid number.")
    if isinstance(value, float):
        raise ValueError("Amount must be provided as Decimal, string, or integer; floats are not supported.")
    try:
        amount = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Amount must be a valid number.") from exc
    if not amount.is_finite():
        raise ValueError("Amount must be finite.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return amount


def validate_description(description: str) -> str:
    if not isinstance(description, str):
        raise ValueError("Description must be a string.")
    description = description.strip()
    if not description:
        raise ValueError("Description must not be empty.")
    return description


@dataclass(frozen=True)
class Expense:
    description: str
    amount: Decimal
    category: str = "Other"
    id: str = dataclass_field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        object.__setattr__(self, "description", validate_description(self.description))
        object.__setattr__(self, "amount", parse_decimal(self.amount))
        object.__setattr__(self, "category", normalize_category(self.category))
        try:
            parsed_id = uuid.UUID(self.id)
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError("Expense ID must be a valid UUID.") from exc
        if str(parsed_id) != self.id:
            raise ValueError("Expense ID must use canonical UUID format.")


def _expense_from_record(record: Any, index: int) -> Expense:
    if not isinstance(record, dict):
        raise ExpenseDataError(f"Invalid expense at index {index}: expected an object.")
    legacy_fields = {"amount", "category", "description"}
    current_fields = {"id", "amount", "category", "description"}
    if set(record) not in (legacy_fields, current_fields):
        raise ExpenseDataError(
            f"Invalid expense at index {index}: expected exactly id, amount, category, and description."
        )
    if not isinstance(record["amount"], str):
        raise ExpenseDataError(f"Invalid expense at index {index}: amount must be a string.")
    if not isinstance(record["category"], str) or not isinstance(record["description"], str):
        raise ExpenseDataError(f"Invalid expense at index {index}: category and description must be strings.")
    try:
        expense = Expense(record["description"], Decimal(record["amount"]), record["category"])
        if set(record) == current_fields:
            if not isinstance(record["id"], str):
                raise ExpenseDataError(f"Invalid expense at index {index}: id must be a string.")
            return Expense(expense.description, expense.amount, expense.category, record["id"])
        legacy_name = f"{index}:{expense.amount}|{expense.category}|{expense.description}"
        legacy_id = str(uuid.uuid5(LEGACY_ID_NAMESPACE, legacy_name))
        return Expense(expense.description, expense.amount, expense.category, legacy_id)
    except (ValueError, InvalidOperation) as exc:
        raise ExpenseDataError(f"Invalid expense at index {index}: {exc}") from exc


def load_expenses(path: str | Path = DEFAULT_DATA_PATH) -> list[Expense]:
    data_path = Path(path)
    try:
        with data_path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return []
    except UnicodeDecodeError as exc:
        raise ExpenseDataError(f"Could not decode expense data {data_path} as UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ExpenseDataError(f"Malformed JSON in {data_path}: {exc.msg}.") from exc
    except OSError as exc:
        raise ExpenseStorageError(f"Could not read expense data {data_path}: {exc}") from exc
    if not isinstance(data, list):
        raise ExpenseDataError(f"Invalid expense data in {data_path}: the root must be an array.")
    expenses = [_expense_from_record(record, index) for index, record in enumerate(data)]
    ids = [expense.id for expense in expenses]
    if len(ids) != len(set(ids)):
        raise ExpenseDataError("Expense IDs must be unique.")
    return expenses


def save_expenses(path: str | Path, expenses: Iterable[Expense]) -> None:
    data_path = Path(path)
    temporary_path: Path | None = None
    try:
        data_path.parent.mkdir(parents=True, exist_ok=True)
        records = [
            {
                "id": expense.id,
                "amount": str(expense.amount),
                "category": expense.category,
                "description": expense.description,
            }
            for expense in expenses
        ]
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{data_path.name}.", suffix=".tmp", dir=data_path.parent
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(records, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, data_path)
        temporary_path = None
    except (OSError, TypeError, ValueError) as exc:
        raise ExpenseStorageError(f"Could not save expense data {data_path}: {exc}") from exc
    finally:
        if temporary_path is not None:
            active_error = sys.exc_info()[1]
            try:
                temporary_path.unlink()
            except OSError as cleanup_error:
                message = (
                    f"Could not remove temporary expense data "
                    f"{temporary_path}: {cleanup_error}"
                )
                if active_error is not None:
                    message = f"{active_error}; additionally, {message}"
                    raise ExpenseStorageError(message) from active_error
                raise ExpenseStorageError(message) from cleanup_error


class ExpenseTracker:
    def __init__(self, data_path: str | Path = DEFAULT_DATA_PATH) -> None:
        self.data_path = Path(data_path)

    def add_expense(
        self, description: str, amount: Decimal | str | int | float, category: str = "Other"
    ) -> Expense:
        expense = Expense(description, parse_decimal(amount), normalize_category(category))
        expenses = load_expenses(self.data_path)
        expenses.append(expense)
        save_expenses(self.data_path, expenses)
        return expense

    def edit_expense(
        self,
        expense_id: str,
        *,
        description: str | object = UNSET,
        amount: Decimal | str | int | float | object = UNSET,
        category: str | object = UNSET,
    ) -> Expense:
        if description is UNSET and amount is UNSET and category is UNSET:
            raise ValueError("At least one field must be supplied for editing.")
        try:
            parsed_id = uuid.UUID(expense_id)
        except (ValueError, AttributeError, TypeError) as exc:
            raise ExpenseNotFoundError(f"Expense ID not found: {expense_id}") from exc
        if str(parsed_id) != expense_id:
            raise ExpenseNotFoundError(f"Expense ID not found: {expense_id}")

        expenses = load_expenses(self.data_path)
        for index, existing in enumerate(expenses):
            if existing.id == expense_id:
                updated = Expense(
                    existing.description if description is UNSET else description,
                    existing.amount if amount is UNSET else amount,
                    existing.category if category is UNSET else category,
                    existing.id,
                )
                expenses[index] = updated
                save_expenses(self.data_path, expenses)
                return updated
        raise ExpenseNotFoundError(f"Expense ID not found: {expense_id}")

    def list_expenses(self, category: str | None = None) -> list[Expense]:
        expenses = load_expenses(self.data_path)
        if category is None:
            return expenses
        normalized = normalize_category(category)
        return [expense for expense in expenses if expense.category == normalized]

    def total(self, category: str | None = None) -> Decimal:
        return sum((expense.amount for expense in self.list_expenses(category)), Decimal("0"))


def parse_amount(value: str) -> Decimal:
    try:
        return parse_decimal(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = ExpenseArgumentParser(description="Track expenses and filter them by category.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="Expense JSON path.")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="Add an expense.")
    add.add_argument("description")
    add.add_argument("amount", type=parse_amount)
    add.add_argument("--category", default="Other")

    listing = commands.add_parser("list", help="List expenses.")
    listing.add_argument("--category")
    total = commands.add_parser("total", help="Print the expense total.")
    total.add_argument("--category")
    edit = commands.add_parser("edit", help="Edit an expense.")
    edit.add_argument("id")
    edit.add_argument("--description")
    edit.add_argument("--amount", type=parse_amount)
    edit.add_argument("--category")
    return parser


def _format_expense(expense: Expense) -> str:
    return f"{expense.id}: {expense.description} - {expense.amount} ({expense.category})"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        tracker = ExpenseTracker(args.data)
        if args.command == "add":
            expense = tracker.add_expense(args.description, args.amount, args.category)
            print(f"Added: {_format_expense(expense)}")
        elif args.command == "list":
            for expense in tracker.list_expenses(args.category):
                print(_format_expense(expense))
            print(f"Total: {tracker.total(args.category)}")
        elif args.command == "total":
            print(tracker.total(args.category))
        else:
            expense = tracker.edit_expense(
                args.id,
                description=args.description if args.description is not None else UNSET,
                amount=args.amount if args.amount is not None else UNSET,
                category=args.category if args.category is not None else UNSET,
            )
            print(f"Updated: {_format_expense(expense)}")
    except (ValueError, ExpenseStorageError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
