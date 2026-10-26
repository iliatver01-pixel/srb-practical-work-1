import unittest

from src.main import (
    Task,
    slack,
    is_feasible,
    deadline_type,
    classify_system,
    critical_task,
    required_reaction_time,
    utilization,
    classify_architecture,
)


class TaskCalculationTests(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            Task("Аварийный останов", "жёсткое", 1, 5, 5),
            Task("Опрос датчиков", "жёсткое", 2, 20, 20),
            Task("Воздействие на привод", "жёсткое", 2, 10, 10),
            Task("Обновление индикации", "мягкое", 8, 100, 100),
            Task("Журналирование", "мягкое", 40, 500, 500),
        ]

    def test_slack(self):
        self.assertEqual(slack(self.tasks[0]), 4)

    def test_individual_feasibility(self):
        self.assertTrue(is_feasible(self.tasks[0]))
        impossible = Task("Тест", "жёсткое", 8, 5, 10)
        self.assertFalse(is_feasible(impossible))

    def test_deadline_type(self):
        self.assertEqual(
            deadline_type(self.tasks[0]),
            "неявный (D = T)",
        )

    def test_system_classification(self):
        self.assertEqual(
            classify_system(self.tasks),
            "жёсткого реального времени",
        )

    def test_critical_task(self):
        self.assertEqual(
            critical_task(self.tasks).name,
            "Аварийный останов",
        )

    def test_required_reaction_time(self):
        self.assertEqual(required_reaction_time(self.tasks), 5)

    def test_utilization(self):
        self.assertAlmostEqual(utilization(self.tasks), 0.66)

    def test_architecture(self):
        self.assertEqual(
            classify_architecture(1, False),
            "однопроцессорная",
        )
        self.assertEqual(
            classify_architecture(4, False),
            "многопроцессорная",
        )
        self.assertEqual(
            classify_architecture(1, True),
            "распределённая",
        )


if __name__ == "__main__":
    unittest.main()