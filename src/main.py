from dataclasses import dataclass
from pathlib import Path
import csv
import argparse


VALID_CLASSES = {"жёсткое", "твёрдое", "мягкое"}


@dataclass
class Task:
    name: str
    hardness: str
    C: float
    D: float
    T: float


def load_tasks(path: Path) -> list[Task]:
    """Загружает задачи из CSV-файла."""
    tasks = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required_columns = {"name", "hardness", "C", "D", "T"}
        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError(
                "В CSV должны быть столбцы: name, hardness, C, D, T"
            )

        for row_number, row in enumerate(reader, start=2):
            hardness = row["hardness"].strip().lower()
            if hardness not in VALID_CLASSES:
                raise ValueError(
                    f"Строка {row_number}: неизвестный класс {hardness!r}. "
                    f"Допустимые значения: {', '.join(sorted(VALID_CLASSES))}"
                )
            try:
                C, D, T = float(row["C"]), float(row["D"]), float(row["T"])
            except (TypeError, ValueError):
                raise ValueError(
                    f"Строка {row_number}: C, D и T должны быть числами"
                )
            if C <= 0 or D <= 0 or T <= 0:
                raise ValueError(
                    f"Строка {row_number}: C, D и T должны быть больше нуля"
                )
            if not row["name"].strip():
                raise ValueError(f"Строка {row_number}: имя задачи не задано")
            tasks.append(Task(row["name"].strip(), hardness, C, D, T))

    if not tasks:
        raise ValueError("Файл не содержит задач")
    return tasks


def slack(task: Task) -> float:
    """Запас времени: L = D - C."""
    return task.D - task.C


def is_feasible(task: Task) -> bool:
    """Проверяет индивидуальное условие C <= D."""
    return slack(task) >= 0


def deadline_type(task: Task) -> str:
    """Определяет тип дедлайна по соотношению D и T."""
    if task.D == task.T:
        return "неявный (D = T)"
    if task.D < task.T:
        return "ограниченный (D < T)"
    return "произвольный (D > T)"


def classify_system(tasks: list[Task]) -> str:
    """По заданию: система жёсткого ВР, если есть жёсткая задача."""
    if any(task.hardness == "жёсткое" for task in tasks):
        return "жёсткого реального времени"
    return "мягкого реального времени"


def critical_task(tasks: list[Task]) -> Task | None:
    """Возвращает жёсткую задачу с минимальным запасом."""
    hard_tasks = [task for task in tasks if task.hardness == "жёсткое"]
    return min(hard_tasks, key=slack) if hard_tasks else None


def required_reaction_time(tasks: list[Task]) -> float:
    """
    В рамках этой работы требуемое время реакции принимается равным
    минимальному относительному дедлайну выбранного набора задач:
    жёстких, если они есть, иначе всех задач.
    """
    hard_tasks = [task for task in tasks if task.hardness == "жёсткое"]
    selected_tasks = hard_tasks if hard_tasks else tasks
    return min(task.D for task in selected_tasks)


def utilization(tasks: list[Task]) -> float:
    """Коэффициент загрузки: U = сумма(C_i / T_i)."""
    return sum(task.C / task.T for task in tasks)


def classify_architecture(n_cpu: int, has_network: bool) -> str:
    """Классифицирует архитектуру по числу процессоров и наличию сети."""
    if n_cpu < 1:
        raise ValueError("Число процессоров должно быть не меньше 1")
    if has_network:
        return "распределённая"
    if n_cpu > 1:
        return "многопроцессорная"
    return "однопроцессорная"


def format_ms(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def print_report(tasks: list[Task], n_cpu: int, has_network: bool) -> None:
    system_class = classify_system(tasks)
    critical = critical_task(tasks)
    reaction = required_reaction_time(tasks)
    U = utilization(tasks)
    architecture = classify_architecture(n_cpu, has_network)
    all_individually_feasible = all(is_feasible(task) for task in tasks)

    headers = [
        "Задача", "Класс", "C, мс", "D, мс", "T, мс",
        "L, мс", "Выполнимо", "Тип дедлайна"
    ]
    rows = []
    for task in tasks:
        rows.append([
            task.name, task.hardness, format_ms(task.C), format_ms(task.D),
            format_ms(task.T), format_ms(slack(task)),
            "да" if is_feasible(task) else "нет", deadline_type(task)
        ])

    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
    line = "-+-".join("-" * width for width in widths)
    print(line)
    print(" | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print(line)
    for row in rows:
        print(" | ".join(row[i].ljust(widths[i]) for i in range(len(headers))))
    print(line)

    print("\nИТОГОВОЕ ЗАКЛЮЧЕНИЕ")
    print(f"Класс системы: {system_class}.")
    if critical:
        print(
            f"Критическая задача: «{critical.name}», "
            f"запас L = {format_ms(slack(critical))} мс."
        )
    else:
        print("Критическая задача среди жёстких отсутствует: жёстких задач нет.")
    print(f"Требуемое время реакции R_треб = {format_ms(reaction)} мс.")
    print(f"Коэффициент загрузки U = {format_ms(U)}.")
    print(f"Необходимое условие U <= 1: {'выполняется' if U <= 1 else 'не выполняется'}.")
    print(f"Архитектура: {architecture} (процессоров: {n_cpu}, сеть: {'есть' if has_network else 'нет'}).")
    print(
        "Индивидуальные дедлайны: "
        + ("выполнимы по проверке C <= D." if all_individually_feasible
           else "не все выполнимы по проверке C <= D.")
    )
    if U <= 1 and all_individually_feasible:
        print(
            "Предварительный вывод: проверенные индивидуальные ограничения "
            "и необходимое условие загрузки соблюдаются. Это само по себе "
            "не является полным доказательством планируемости системы."
        )
    else:
        print(
            "Вывод: выявлено нарушение хотя бы одного проверяемого условия; "
            "требуется пересмотреть параметры задач или архитектуру."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Классификация системы реального времени и расчёт характеристик задач"
    )
    parser.add_argument(
        "--data", type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "tasks.csv",
        help="Путь к CSV-файлу с задачами"
    )
    parser.add_argument("--cpu", type=int, default=1, help="Количество процессоров")
    parser.add_argument(
        "--network", choices=("yes", "no"), default="no",
        help="Есть ли сеть: yes или no"
    )
    args = parser.parse_args()

    try:
        tasks = load_tasks(args.data)
        print_report(tasks, args.cpu, args.network == "yes")
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
