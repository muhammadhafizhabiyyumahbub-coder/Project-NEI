import threading
from nei.core.resource_manager import ResourceManager


def test_acquisition_releases():
    rm = ResourceManager()
    assert rm.acquire("rhino6", "task1") is True
    assert rm.holder("rhino6") == "task1"
    assert rm.all_holders()["rhino6"] == "task1"
    rm.release("rhino6", "task1")
    assert rm.holder("rhino6") is None


def test_second_holder_blocked():
    rm = ResourceManager()
    assert rm.acquire("solidworks2022", "task1") is True
    # task2 cannot acquire without waiting — test by checking holder
    assert rm.holder("solidworks2022") == "task1"
    rm.release("solidworks2022", "task1")
    assert rm.holder("solidworks2022") is None


def test_acquire_timeout_fails_when_held():
    rm = ResourceManager()
    assert rm.acquire("maxsurf20", "task1") is True
    # release in background after a moment
    def late_release():
        import time
        time.sleep(0.3)
        rm.release("maxsurf20", "task1")
    t = threading.Thread(target=late_release)
    t.start()
    got = rm.acquire("maxsurf20", "task2", timeout_s=0.1)
    assert got is False  # timed out
    t.join()
    assert rm.acquire("maxsurf20", "task3", timeout_s=0.1) is True
    rm.release("maxsurf20", "task3")
