export interface Analyzer {
    id: string;
    effective_weight: number;
    healthy: boolean;
    admin_enabled: boolean;
    tx_packets: number;
}

export interface MetricsPayload {
    ts: number;
    queue_depth: number;
    analyzers: Analyzer[];
    packets_rx: number;
}