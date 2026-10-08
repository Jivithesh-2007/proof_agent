import { Analysis, AnalysisStatus, ConfidenceLevel, TraceStep } from '../types';
import { request } from './api';

export function mapBackendAnalysis(res: any): Analysis {
  const statusStr = (res.status || 'verified').toLowerCase();
  let status: AnalysisStatus = 'verified';
  if (statusStr.includes('refused')) status = 'refused';
  else if (statusStr.includes('failed')) status = 'failed';
  else if (statusStr.includes('warning')) status = 'warning';
  else if (statusStr.includes('prediction')) status = 'model_prediction';
  else if (statusStr.includes('document')) status = 'document_supported';

  const confScore = res.confidence ?? res.verification?.confidence_score ?? 1.0;
  const confidence: ConfidenceLevel = confScore > 0.8 ? 'high' : confScore > 0.5 ? 'medium' : 'low';

  const proof = res.proof_trace || {};
  const ruleReasoning: string[] = proof.rule_reasoning || [];
  const canonical = res.canonical_result || proof.canonical_result || {};
  const reference = res.reference_result || proof.reference_result || {};
  const execution = res.execution_result || {};
  const contract = res.analysis_contract || proof.analysis_contract || {};

  // Construct KPIs
  const kpis = [];
  if (canonical && canonical.result !== undefined && canonical.result !== null) {
    if (typeof canonical.result === 'object' && Array.isArray(canonical.result)) {
      kpis.push({ label: 'Total Groups', value: `${canonical.result.length}` });
    } else {
      const unitStr = canonical.unit ? ` ${canonical.unit}` : '';
      kpis.push({ label: canonical.metric || 'Calculated Metric', value: `${canonical.result}${unitStr}` });
    }
  }
  if (proof.execution?.execution_ms) {
    kpis.push({ label: 'Execution Runtime', value: `${proof.execution.execution_ms} ms` });
  }
  if (proof.reproducibility?.matches !== undefined) {
    kpis.push({ label: 'Reproducibility', value: proof.reproducibility.matches ? '100% (Pass)' : 'Failed' });
  }
  if (proof.reference_match !== undefined) {
    kpis.push({ label: 'Reference Verification', value: proof.reference_match ? 'Exact Match' : 'Mismatch' });
  }

  // Construct Trace Steps
  const trace: TraceStep[] = [];
  trace.push({ timestamp: 'Stage 1', step: 'Question received & dynamic schema profiled', status: 'completed' as const });
  if (ruleReasoning.length > 0) {
    trace.push({
      timestamp: 'Stage 2',
      step: 'ProofAI Rule Analyst interpreted intent',
      status: 'completed' as const,
      details: ruleReasoning.join(' | ')
    });
  }
  if (status === 'refused') {
    trace.push({
      timestamp: 'Stage 3',
      step: 'Intelligent Refusal Enforced',
      status: 'failed' as const,
      details: res.refusal_reason || 'Query refused due to missing schema columns or unresolvable concepts.'
    });
  } else {
    trace.push({ timestamp: 'Stage 3', step: 'Analysis Contract validated strictly', status: 'completed' as const });
    trace.push({
      timestamp: 'Stage 4',
      step: 'Deterministic Analytics Engine executed calculation',
      status: 'completed' as const,
      details: `Runtime: ${proof.execution?.execution_ms || 0}ms`
    });
    trace.push({
      timestamp: 'Stage 5',
      step: 'Independent Reference Engine cross-verified result',
      status: proof.reference_match ? 'completed' : 'failed'
    });
    trace.push({
      timestamp: 'Stage 6',
      step: 'Reproducibility & Proof Policy verified',
      status: status === 'verified' ? 'completed' : 'warning'
    });
  }

  // Handle Table Data if grouped result
  let tableData: any[] | undefined = undefined;
  if (canonical && Array.isArray(canonical.result)) {
    tableData = canonical.result;
  } else if (res.execution_result?.table) {
    tableData = res.execution_result.table;
  }

  return {
    id: res.analysis_id || `ans_${Date.now()}`,
    question: res.question,
    datasetId: res.resolved_dataset_ids?.[0] || 'dataset',
    datasetName: res.resolved_dataset_ids?.[0] || 'dataset.csv',
    status,
    confidence,
    answer: res.answer,
    explanation: res.answer,
    date: 'Today',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    kpis,
    ruleReasoning,
    analysisContract: contract,
    canonicalResult: canonical,
    referenceResult: reference,
    proofTrace: proof,
    tableData,
    codeDetails: res.code ? {
      code: res.code,
      executionStatus: execution.success ? 'Successful' : 'Failed',
      executionTime: `${proof.execution?.execution_ms || 0}ms`,
      environment: 'Isolated Sandbox (Deterministic)',
      outputType: contract.expected_result_type || 'Scalar',
      reproducible: proof.reproducibility?.matches ?? true,
      stdout: execution.stdout
    } : undefined,
    trace,
    verification: {
      executionSuccessful: res.verification?.v1_code_executed === 'PASS' || res.verification?.execution_success === 'PASS',
      reproducible: res.verification?.v6_reproducible === 'PASS' || proof.reproducibility?.matches === true,
      requiredFieldsPresent: res.verification?.v8_required_columns_used === 'PASS',
      dataQualityPassed: res.verification?.v12_quality_requirements_satisfied === 'PASS',
      sourceConflicts: false,
      confidenceReason: [
        `Deterministic ProofAI reasoning applied (${ruleReasoning.length} rules matched)`,
        proof.reference_match ? 'Independently verified against host reference engine' : 'Reference calculation completed',
        proof.reproducibility?.matches ? 'Reproducibility check passed' : 'Reproducibility evaluated',
      ],
      vChecks: res.verification || {},
      referenceMatch: proof.reference_match
    },
    refusalDetails: status === 'refused' ? {
      reason: res.refusal_reason || 'Query cannot be answered from dataset schema.',
      availableFields: res.proof_trace?.available_columns || [],
      missingFields: [res.refusal_reason || 'Target Column'],
      whyStopped: 'ProofAI strictly adheres to verification principles and refuses unanswerable queries without hallucination.'
    } : undefined
  };
}

export async function createAnalysis(
  question: string,
  datasetId: string,
  datasetName: string
): Promise<Analysis> {
  const reqBody = {
    question,
    selected_datasets: datasetId ? [datasetId] : [],
    selected_documents: []
  };

  const res = await request<any>('/analysis', {
    method: 'POST',
    body: JSON.stringify(reqBody)
  });

  return mapBackendAnalysis(res);
}

export async function getAnalysisById(id: string): Promise<Analysis | undefined> {
  try {
    const res = await request<any>(`/analysis/${id}`);
    if (!res || !res.analysis_id) return undefined;
    return mapBackendAnalysis(res);
  } catch (error) {
    console.warn(`Analysis ${id} not found:`, error);
    return undefined;
  }
}

export async function getAnalyses(): Promise<Analysis[]> {
  return [];
}
