# Functional labels — command interneuron ground truth

This file is the **independent** source of functional importance against which
graph-theoretic salience is triangulated. It is derived from
electrophysiology / laser-ablation literature and the Cook 2019 / WormAtlas
identity conventions — **never** from anything computed on the graph itself.
Keeping it separate is what makes the headline question non-circular.

> **Provenance rule (CLAUDE.md).** Neuron identities follow **Cook et al. 2019 /
> WormAtlas**, not older White-1986-derived edge lists. Cook 2019 corrected
> identity errors including the **PVCL/PVCR switch** and the **DVB/PVT
> crossing**. PVC is a command-interneuron *target*, so the label convention is
> load-bearing. If a downstream edge list uses White-1986 identities, relabel to
> Cook 2019 before analysis and record that step here.

## The command interneurons

The "command interneurons" are the interneuron classes whose activity drives
sustained forward and backward locomotion, established functionally by ablation
and optogenetics independently of connectivity. The canonical set:

| Class | Cells         | Primary role (functional literature)              | Notes on identity |
|-------|---------------|---------------------------------------------------|-------------------|
| AVA   | AVAL, AVAR    | Backward locomotion (drives A-type motor neurons) | Core command pair |
| AVB   | AVBL, AVBR    | Forward locomotion (drives B-type motor neurons)  | Core command pair |
| AVD   | AVDL, AVDR    | Backward locomotion; touch-response relay         | Core command pair |
| AVE   | AVEL, AVER    | Backward locomotion (anterior body)               | Core command pair |
| PVC   | PVCL, PVCR    | Forward locomotion; touch-response relay          | **PVCL/PVCR switched in White 1986; use Cook 2019 identities** |

These ten cells (five classes × L/R) are the **primary** ground-truth target
set used by `analysis/hub_recovery.py`.

### Optional extended set (sensitivity only, off by default)

Sometimes included in "command-like" locomotor interneurons; used only for a
robustness check, never as the headline set:

| Class | Cells       | Role                                    |
|-------|-------------|-----------------------------------------|
| PVP   | PVPL, PVPR  | Forward locomotion modulation           |
| AVG   | AVG         | Locomotion integration (weak evidence)  |

## Citations

- **Cook, S.J., Jarrell, T.A., Brittin, C.A., et al. (2019).** "Whole-animal
  connectomes of both *Caenorhabditis elegans* sexes." *Nature* 571, 63–71.
  — identity conventions, corrected PVCL/PVCR and DVB/PVT, connectivity source.
- **Chalfie, M., Sulston, J.E., White, J.G., et al. (1985).** "The neural
  circuit for touch sensitivity in *Caenorhabditis elegans*." *J. Neurosci.*
  5(4), 956–964. — AVA/AVB/AVD/AVE/PVC command role from ablation.
- **WormAtlas** (wormatlas.org) — neuron class descriptions and locomotor roles.
- **White, J.G., Southgate, E., Thomson, J.N., Brenner, S. (1986).** "The
  structure of the nervous system of *C. elegans*." *Phil. Trans. R. Soc. B*
  314, 1–340. — historical connectome; **identity errors corrected by Cook 2019**.

## Machine-readable source

The target set consumed by the analysis lives in
[`command_interneurons.csv`](command_interneurons.csv) next to this file. Edit
that CSV to change the ground-truth set; every code path reads from it so the
labels have exactly one source of truth. Each row records the label's citation.
