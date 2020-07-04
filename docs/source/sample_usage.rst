**************
Sample Usages
**************

Some samples for using ``evergreen.py``.

Diplaying all the failed tests from a given task
-------------------------------------------------

If you have an ID of a failed task, a common operation would be to
get a list of all the tests that failed. In this example, we will
print out that list.

.. code-block:: python

    from evergreen import EvergreenApi

    evg_api = EvergreenApi.get_api()
    task_id = "task_id_1"

    task = evg_api.task_by_id(task_id)
    for test in task.get_tests():
        if test.status != "pass":
            print(test.test_file)

