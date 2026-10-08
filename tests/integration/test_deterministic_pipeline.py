import pytest
import pandas as pd
from io import StringIO
from backend.models.query import AnalysisRequest
from backend.models.analysis import AnalysisStatus
from backend.api.dependencies import get_orchestrator
from backend.services.storage import storage_service
from backend.ingestion.file_manager import FileManager
from backend.profiling.profiler import DataProfiler

@pytest.fixture(autouse=True)
def setup_test_datasets(tmp_path):
    orchestrator = get_orchestrator()

    # Create employee dataset
    emp_csv = """employee_id,department,salary,joining_date
E001,IT,60000,2023-01-01
E002,HR,45000,2022-04-01
E003,IT,75000,2021-06-01
E004,HR,50000,2024-02-01"""
    
    emp_path = tmp_path / "employee.csv"
    emp_path.write_text(emp_csv)

    df_emp, meta_emp = FileManager.ingest_dataset(emp_path, dataset_id="ds_test_employee")
    prof_emp = DataProfiler.profile("ds_test_employee", "employee.csv", df_emp)
    storage_service.save_dataset(meta_emp, emp_path, df_emp, prof_emp)

    # Create student dataset
    stu_csv = """student_id,branch,marks,attendance
S101,CS,85,92
S102,EC,78,88
S103,CS,95,96
S104,EC,82,85"""
    stu_path = tmp_path / "student.csv"
    stu_path.write_text(stu_csv)

    df_stu, meta_stu = FileManager.ingest_dataset(stu_path, dataset_id="ds_test_student")
    prof_stu = DataProfiler.profile("ds_test_student", "student.csv", df_stu)
    storage_service.save_dataset(meta_stu, stu_path, df_stu, prof_stu)

    return orchestrator

def test_average_salary_by_department():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="What is the average salary by department?",
        selected_datasets=["ds_test_employee"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    assert result.canonical_result is not None
    assert isinstance(result.canonical_result.result, list)
    
    # Check that HR = 47500 and IT = 67500
    res_map = {r["department"]: r["salary"] for r in result.canonical_result.result}
    assert res_map["HR"] == 47500.0
    assert res_map["IT"] == 67500.0

def test_average_salary():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="What is the average salary?",
        selected_datasets=["ds_test_employee"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    assert result.canonical_result is not None
    assert result.canonical_result.result == 57500.0

def test_how_many_employees():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="How many employees are there?",
        selected_datasets=["ds_test_employee"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    assert result.canonical_result.result == 4

def test_missing_column_refused():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="What is the average profit?",
        selected_datasets=["ds_test_employee"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.REFUSED
    assert "profit" in result.answer.lower() or result.refusal_reason is not None

def test_student_average_marks_by_branch():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="What is the average marks by branch?",
        selected_datasets=["ds_test_student"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    assert isinstance(result.canonical_result.result, list)
    res_map = {r["branch"]: r["marks"] for r in result.canonical_result.result}
    assert res_map["CS"] == 90.0
    assert res_map["EC"] == 80.0
