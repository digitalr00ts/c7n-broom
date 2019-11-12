""" config pytest """
import c7n_broom


def pytest_report_header():
    """Additional report header"""
    return f"version: {c7n_broom.__version__}"
