export type AnalysisStatus = 'verified' | 'warning' | 'refused' | 'failed' | 'processing' | 'document_supported' | 'model_prediction';
export type ConfidenceLevel = 'high' | 'medium' | 'low';
export type FileType = 'csv' | 'xlsx' | 'pdf' | 'json';

export interface Dataset {
  id: string;
  name: string;
  type: FileType;
  rows: number;
  columns: number;
  size: string;
  updatedAt: string;
  status: 'ready' | 'processing' | 'error';
  missingValuesPct: number;
  duplicateRows: number;
  warningCount: number;
  columnNames: string[];
  sha256?: string;
  isDuplicate?: boolean;
  sampleRows?: Record<string, any>[];
  columnProfiles?: ColumnProfile[];
}

export interface ColumnProfile {
  name: string;
  inferredType: string;
  missingCount: number;
  missingPercentage: number;
  uniqueCount: number;
  sampleValues: (string | number)[];
}

export interface QualityWarning {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  type: string;
  message: string;
  affectedColumns?: string[];
}

export interface DataQualityReport {
  requiredColumnsPresent: boolean;
  numericFieldsValid: boolean;
  noRelevantMissingValues: boolean;
  duplicateRowsCount: number;
  duplicateRowsDetected: boolean;
  currencyMismatch: boolean;
  missingValuesMap: Record<string, number>;
  warnings: QualityWarning[];
  impactOnAnswer: string;
  impactLevel: 'low' | 'medium' | 'high';
}

export interface EvidenceItem {
  id: string;
  document: string;
  page?: number;
  section?: string;
  excerpt: string;
  relevance: number;
  fileType?: FileType;
  indexedChunks?: number;
}

export interface CalculationDetails {
  formula: string;
  inputs: Record<string, string | number>;
  steps: { label: string; expression: string; result: string }[];
  result: string | number;
  validations: {
    numericResultValidated: boolean;
    requiredFieldsPresent: boolean;
    calculationSuccessful: boolean;
  };
}

export interface CodeExecutionDetails {
  code: string;
  executionStatus: 'Successful' | 'Failed' | 'Timeout';
  executionTime: string;
  environment: string;
  outputType: string;
  reproducible: boolean;
  stdout?: string;
}

export interface TraceStep {
  timestamp: string;
  step: string;
  status: 'completed' | 'in_progress' | 'warning' | 'failed';
  details?: string;
}

export interface Verification {
  executionSuccessful: boolean;
  reproducible: boolean;
  requiredFieldsPresent: boolean;
  dataQualityPassed: boolean;
  sourceConflicts: boolean;
  confidenceReason: string[];
  vChecks?: Record<string, string>;
  reproducibilityDiff?: number;
  referenceMatch?: boolean;
}

export interface Analysis {
  id: string;
  question: string;
  datasetId: string;
  datasetName: string;
  status: AnalysisStatus;
  confidence: ConfidenceLevel;
  answer?: string;
  explanation?: string;
  date: string;
  timestamp: string;
  kpis?: { label: string; value: string }[];
  calculation?: CalculationDetails;
  codeDetails?: CodeExecutionDetails;
  evidence?: EvidenceItem[];
  dataQuality?: DataQualityReport;
  trace?: TraceStep[];
  verification?: Verification;
  ruleReasoning?: string[];
  analysisContract?: Record<string, any>;
  canonicalResult?: Record<string, any>;
  referenceResult?: Record<string, any>;
  proofTrace?: Record<string, any>;
  tableData?: Record<string, any>[];
  charts?: {
    type: 'monthly_growth' | 'regional_revenue' | 'product_profit' | 'bar_chart' | 'table';
    title: string;
    subtitle: string;
    data?: any[];
  };
  refusalDetails?: {
    reason: string;
    availableFields: string[];
    missingFields: string[];
    whyStopped: string;
  };
  conflictDetails?: {
    conflictType: string;
    sourceA: { name: string; val: string };
    sourceB: { name: string; val: string };
    explanation: string;
  };
}

export interface IndexedDocument {
  id: string;
  filename: string;
  fileType: FileType;
  pages: number;
  indexedChunks: number;
  status: 'Indexed' | 'Processing' | 'Failed';
  uploadedAt: string;
  sections: { title: string; page: number; snippet: string }[];
}
