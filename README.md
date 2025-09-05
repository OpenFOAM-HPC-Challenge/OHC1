# 1st OpenFOAM HPC Challenge (OHC-1)
This repository contains the data, scripts and notebooks that were used to analyze the results of the 1st OpenFOAM HPC Challenge (OHC-1), held July 1-2, 2025 in Vienna as part of the 20th OpenFOAM Workshop.

## OHC-1 Overview
The challenge was aimed at evaluating the efficiency, scalability, and performance of OpenFOAM on various hardware platforms, with and without software enhancements, using a standardized industrial test case (DrivAer). The challenge included two tracks:
  - **Hardware Track:** Participants simulated the case using standard (unmodified) OpenFOAM v2412, on any supported hardware.
  - **Software Track:** Participants could use custom solvers and code optimizations, provided the mesh and physical modeling correspond to the original setup.

A detailed description of the challenge is provided in the [introductory presentation](Introduction.pdf).

## DrivAer Case
The challenge focused on simulation of external flow over a static version of the DrivAer automotive model. The model consists of a full car geometry, with closed coolings and a complex underbody, without considering wheel rotation. A detailed description of the test case may be found in the repository[^DrivAerCase] of the HPC Technical Committee.

## Data Analysis
Submissions were originally given in the form of Excel files. These files were parsed with [python utilities](OHCParser.py), and the results were visualized in a set of Jupyter notebooks.
Several metrics of interest (time-to-solution, energy-to-solution, FVOPS, etc) were analyzed. See the HPC TC repository[^HPCTC] for a detailed description of the metrics.

## Repository Structure

- [Introduction.pdf](Introduction.pdf): Full challenge description, rules, metrics, and data submission guidelines.
- [HW-track Summary.pdf](<HW-track Summary.pdf>): Summary of hardware track analysis (presentation)
- [SW-track Summary.pdf](<SW-track Summary.pdf>): Summary of software track analysis (presentation)
- [Overview.ipynb](Overview.ipynb): Jupyter notebook producing submission statistics
- [HWTrack.ipynb](HWTrack.ipynb): Jupyter notebook used to analyse hardware track submissions
- [SWTrack.ipynb](SWTrack.ipynb): Jupyter notebook used to analyse software track submissions
- [IO.ipynb](IO.ipynb): Jupyter notebook used to analyse submissions of I/O optimizations
- [Interactive.ipynb](Interactive.ipynb): Jupyter notebook providing an interactive plot for custom data analysis, [click for demonstration](https://colab.research.google.com/drive/1adJGbMC4VwWhiD31JNCRvXBWWno_dYxF?usp=sharing)
- [OHCParser.py](OHCParser.py): Data parsing and metric calculation utilities
- [data.json](data.json): JSON file produced from the raw xls submissions (used to accelerated data loading in the Interactive.ipynb notebook)
- [submissions](submissions): Raw submissions (excel sheets, logs, input files, etc)
- [presentations](presentations): Participant presentations

## Getting Started

- If this is your first encounter with OHC, please start by reading [Introduction.pdf](Introduction.pdf), to get familiar with the challenge aims and scope.

- If you're interested in the main conclusions and analysis presented in the workshop, please see [HW-track Summary.pdf](<HW-track Summary.pdf>) and [SW-track Summary.pdf](<SW-track Summary.pdf>), for the hardware and software tracks, respectively.

- If you would like to dive deeper into the data analysis that was done as part of the workshop, please see the individual Jupyter notebooks in the main folder (best viewed from within VS code). The notebooks are known to work with python 3.12.

- Finally, if you wish to conduct custom analysis of the data, it is recommended to use [Interactive.ipynb](Interactive.ipynb) (best viewed from within VS code).

## License
### Source Code
The source code of the parser and the Jupyter notebooks is licensed under the MIT license.

### Submissions Data
All submissions data (folder "submissions") is licensed under CC BY 4.0. To view a copy of this license, visit https://creativecommons.org/licenses/by/4.0/. For citation, we suggest to provide a link to this repository.

### Presentations
The presentations (folder "presentations") are not covered by any specific license. For further guidance, please reach out to the respective author.

## Questions/Comments

If you have any questions regarding the data, or comments that may help us better prepare for the next occasion of OHC, please feel free to post an issue or contact us at hpc-tc-group@googlegroups.com.


[^DrivAerCase]: https://develop.openfoam.com/committees/hpc/-/tree/develop/incompressible/simpleFoam/occDrivAerStaticMesh
[^HPCTC]: https://develop.openfoam.com/committees/hpc#key-performance-indicators
