import axios from "axios";

/* ----- emitter controls via distributor proxy ----- */
export async function setEmitterRate(id: string, rps: number) {
  await axios.post(`/emitter/${id}/rate`, { rps });
}

export async function pauseEmitter(id: string) {
  await axios.post(`/emitter/${id}/pause`);
}

export async function resumeEmitter(id: string) {
  await axios.post(`/emitter/${id}/resume`);
}

/* ----- analyzer controls ----- */
export async function enableAnalyzer(id: string) {
  await axios.post(`/analyzer/${id}/enable`);
}

export async function disableAnalyzer(id: string) {
  await axios.post(`/analyzer/${id}/disable`);
}
