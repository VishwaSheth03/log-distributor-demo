export interface Analyzer {
    id: string;
    effective_weight: number;
    healthy: boolean;
    admin_enabled: boolean;
    tx_packets: number;
}

export interface Emitter {
    emitter_id: string;
    buffer_size: number;
    rate_rps: number;
    paused: boolean;
}

export interface MetricsPayload {
    ts: number;
    queue_depth: number;
    analyzers: Analyzer[];
    emitters: Emitter[];
    packets_rx: number;
}

export interface LogEntry {
  packet: {
    packetId: string;
    emitter: string;
    messages: {
      ts: string;
      level: string;
      service: string;
      host: string;
      message: string;
    }[];
  };
  analyzer: string;
}