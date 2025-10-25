def test_smoke_imports():
    import merlin
    from merlin.utils import get_logger, load_config

    assert hasattr(merlin, "VERSION")
    assert callable(get_logger)
    assert callable(load_config)


