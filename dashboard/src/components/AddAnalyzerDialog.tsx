import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
} from "@mui/material";
import { useState } from "react";
import { addAnalyzer } from "../api";

export default function AddAnalyzerDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [id, setId] = useState("");
  const [url, setUrl] = useState("");
  const [weight, setWeight] = useState(0.5);

  const handleAdd = async () => {
    await addAnalyzer(id, url, weight).catch(console.error);
    onClose();
    // fields reset next open
    setId("");
    setUrl("");
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Add analyzer</DialogTitle>
      <DialogContent sx={{ pt: 2 }}>
        <TextField
          label="ID"
          value={id}
          onChange={(e) => setId(e.target.value)}
          fullWidth
          sx={{ mb: 2 }}
        />
        <TextField
          label="Ingest URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="http://analyzer3:9000/ingest"
          fullWidth
          sx={{ mb: 2 }}
        />
        <TextField
          label="Weight"
          type="number"
          value={weight}
          onChange={(e) => setWeight(parseFloat(e.target.value))}
          fullWidth
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleAdd} variant="contained" disabled={!id || !url}>
          Add
        </Button>
      </DialogActions>
    </Dialog>
  );
}
