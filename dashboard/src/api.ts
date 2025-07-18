import axios from "axios";

const BASE = "";

export async function setEmitterRate(id: string, rps: number) {
    await axios.post(`${BASE}/${id}/rate`, {rps});
}

export async function pauseEmitter(id: string) {
    await axios.post(`${BASE}/${id}/pause`);
}

export async function resumeEmitter(id: string) {
    await axios.post(`${BASE}/${id}/resume`);
}

export async function enableAnalyzer(id: string) {
    await axios.post(`${BASE}/analyzer/${id}/enable`);
}

export async function disableAnalyzer(id: string) {
    await axios.post(`${BASE}/analyzer/${id}/disable`);
}