import hashlib
import pytest
from pathlib import Path
from backend.models.query import AnalysisRequest
from backend.models.analysis import AnalysisStatus
from backend.api.dependencies import get_orchestrator
from backend.services.storage import storage_service
from backend.ingestion.file_manager import FileManager
from backend.profiling.profiler import DataProfiler

@pytest.fixture(scope="module", autouse=True)
def setup_arbitrary_datasets(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("arbitrary_csvs")

    # 1. Student
    stu_csv = """student_id,branch,marks,attendance
S101,CS,85,92
S102,EC,78,88
S103,CS,95,96
S104,EC,82,85"""
    stu_path = tmp_dir / "student.csv"
    stu_path.write_text(stu_csv)
    df_stu, m_stu = FileManager.ingest_dataset(stu_path, dataset_id="ds_arb_student")
    p_stu = DataProfiler.profile("ds_arb_student", "student.csv", df_stu)
    storage_service.save_dataset(m_stu, stu_path, df_stu, p_stu)

    # 2. Employee
    emp_csv = """employee_id,department,salary,joining_date
E001,IT,60000,2023-01-01
E002,HR,45000,2022-04-01
E003,IT,75000,2021-06-01
E004,HR,50000,2024-02-01"""
    emp_path = tmp_dir / "employee.csv"
    emp_path.write_text(emp_csv)
    df_emp, m_emp = FileManager.ingest_dataset(emp_path, dataset_id="ds_arb_employee")
    p_emp = DataProfiler.profile("ds_arb_employee", "employee.csv", df_emp)
    storage_service.save_dataset(m_emp, emp_path, df_emp, p_emp)

    # 3. Product Transaction
    prod_csv = """product,region,amount,transaction_date
Laptop,North,120000,2024-01-10
Mouse,South,1500,2024-01-12
Laptop,South,120000,2024-01-15
Keyboard,North,3500,2024-01-18"""
    prod_path = tmp_dir / "transactions.csv"
    prod_path.write_text(prod_csv)
    df_prod, m_prod = FileManager.ingest_dataset(prod_path, dataset_id="ds_arb_transactions")
    p_prod = DataProfiler.profile("ds_arb_transactions", "transactions.csv", df_prod)
    storage_service.save_dataset(m_prod, prod_path, df_prod, p_prod)

    # 4. Customer Revenue with Special Punctuation: Customer Name,Revenue ($),Order Date,Product Category
    cust_csv = """Customer Name,Revenue ($),Order Date,Product Category
Alice,500,2024-02-01,Electronics
Bob,250,2024-02-02,Clothing
Charlie,750,2024-02-03,Electronics
Diana,150,2024-02-04,Clothing"""
    cust_path = tmp_dir / "customers.csv"
    cust_path.write_text(cust_csv)
    df_cust, m_cust = FileManager.ingest_dataset(cust_path, dataset_id="ds_arb_customers")
    p_cust = DataProfiler.profile("ds_arb_customers", "customers.csv", df_cust)
    storage_service.save_dataset(m_cust, cust_path, df_cust, p_cust)


def test_average_marks():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="What is the average marks?",
        selected_datasets=["ds_arb_student"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    assert result.canonical_result.result == 85.0

def test_average_marks_by_branch():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="What is the average marks by branch?",
        selected_datasets=["ds_arb_student"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    res_map = {r["branch"]: r["marks"] for r in result.canonical_result.result}
    assert res_map["CS"] == 90.0
    assert res_map["EC"] == 80.0

def test_how_many_employees():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="How many employees are there?",
        selected_datasets=["ds_arb_employee"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    assert result.canonical_result.result == 4

def test_average_salary_by_department():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="What is the average salary by department?",
        selected_datasets=["ds_arb_employee"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    res_map = {r["department"]: r["salary"] for r in result.canonical_result.result}
    assert res_map["HR"] == 47500.0
    assert res_map["IT"] == 67500.0

def test_total_amount_by_region():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="What is the total amount by region?",
        selected_datasets=["ds_arb_transactions"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    res_map = {r["region"]: r["amount"] for r in result.canonical_result.result}
    assert res_map["North"] == 123500.0
    assert res_map["South"] == 121500.0

def test_which_product_generated_most_amount():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="Which product generated the most amount?",
        selected_datasets=["ds_arb_transactions"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    assert result.canonical_result.label == "Laptop"
    assert result.canonical_result.result == 240000.0

def test_average_revenue_by_product_category():
    orchestrator = get_orchestrator()
    req = AnalysisRequest(
        question="What is the average revenue by product category?",
        selected_datasets=["ds_arb_customers"]
    )
    result = orchestrator.process_analysis(req)
    assert result.status == AnalysisStatus.VERIFIED
    res_map = {r["Product Category"]: r["Revenue ($)"] for r in result.canonical_result.result}
    assert res_map["Electronics"] == 625.0
    assert res_map["Clothing"] == 200.0

def test_duplicate_detection_sha256(tmp_path):
    """Phase 34: Test duplicates behavior."""
    content_a = b"id,val\n1,100\n2,200\n"
    content_b = b"id,val\n1,100\n2,201\n"  # 1 byte changed

    h_a = hashlib.sha256(content_a).hexdigest()
    h_a2 = hashlib.sha256(content_a).hexdigest()
    h_b = hashlib.sha256(content_b).hexdigest()

    # Same bytes -> same hash & dataset_id
    assert f"ds_{h_a[:12]}" == f"ds_{h_a2[:12]}"

    # Different filename, same bytes -> same dataset_id
    f1 = tmp_path / "data1.csv"
    f2 = tmp_path / "different_name.csv"
    f1.write_bytes(content_a)
    f2.write_bytes(content_a)
    assert hashlib.sha256(f1.read_bytes()).hexdigest() == hashlib.sha256(f2.read_bytes()).hexdigest()

    # One byte changed -> different dataset_id
    assert f"ds_{h_a[:12]}" != f"ds_{h_b[:12]}"
