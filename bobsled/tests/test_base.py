from ..base import Task


def test_task_entrypoint():
    assert Task("name", "image", entrypoint="one-word").entrypoint == ["one-word"]
    assert Task("name", "image", entrypoint="two words").entrypoint == ["two", "words"]
    assert Task("name", "image", entrypoint=["the", "right", "way"]).entrypoint == [
        "the",
        "right",
        "way",
    ]
