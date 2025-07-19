import React, { useState, useEffect } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
  Slider,
  Switch,
} from "@mui/material";
import { setEmitterRate, pauseEmitter, resumeEmitter } from "../api";
import { type Emitter } from "../types";

/* one row with optimistic‑UI */
function EmitterRow({ e }: { e: Emitter }) {
  const [localRate, setLocalRate] = useState(e.rate_rps);
  const [localPaused, setLocalPaused] = useState(e.paused);

  useEffect(() => {
    setLocalRate(e.rate_rps);
    setLocalPaused(e.paused);
  }, [e]);

  const commitRate = (
    _evt: Event | React.SyntheticEvent,
    value: number | number[]
  ) => {
    setEmitterRate(e.emitter_id, value as number).catch(console.error);
  };

  const togglePause = () => {
    const next = !localPaused;
    setLocalPaused(next);
    next ? pauseEmitter(e.emitter_id) : resumeEmitter(e.emitter_id);
  };

  return (
    <TableRow key={e.emitter_id}>
      <TableCell>{e.emitter_id}</TableCell>
      <TableCell width={160}>
        <Slider
          value={localRate}
          onChange={(_, v) => setLocalRate(v as number)}
          onChangeCommitted={commitRate}
          step={0.5}
          min={0}
          max={10}
          valueLabelDisplay="auto"
          size="small"
        />
      </TableCell>
      <TableCell>
        <Switch checked={localPaused} onChange={togglePause} size="small" />
      </TableCell>
      <TableCell>{e.buffer_size ?? "—"}</TableCell>
    </TableRow>
  );
}

/* entire table */
export default function EmitterTable({ list }: { list: Emitter[] }) {
  return (
    <>
      <Typography variant="h6" sx={{ mt: 3 }}>
        Emitters
      </Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>ID</TableCell>
            <TableCell>Rate (rps)</TableCell>
            <TableCell>Paused</TableCell>
            <TableCell>Buffer</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {list.map((em) => (
            <EmitterRow key={em.emitter_id} e={em} />
          ))}
        </TableBody>
      </Table>
    </>
  );
}
