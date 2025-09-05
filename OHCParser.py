"""
The MIT License (MIT)

Copyright (c) 2025 Mark Wasserman, Huawei
Copyright (c) 2025 Gregor Olenik, TUM
Copyright (c) 2025 Sergey Lesnik, Wikki GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the “Software”), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


# helper functions
import re
import warnings
import pandas as pd
from functools import partial
import os
import datetime
import traceback
import pathlib
import matplotlib.pyplot as plt

def get_cpu_model(fn, s):
    """ given the processor string this functions returns common model names"""
    ls = s.lower()
    generation = "Unknown"

    if "intel" in ls or "xeon" in ls:
        family = "Intel"
        if "core" in ls and "i9-14900" in ls:
            model = "Core"
            submodel = "i9-14900ks"
            generation = "i9"
        elif "xeon" in ls:
            model = "Xeon"
            match = re.search(r'(?<!\d)\d{4}(?!\d)', ls)
            if not match:
                match = re.search(r'(?<!\d)\d[a-z]\d{2}(?!\d)', ls)
                if not match:
                    submodel = "Other"
                    print(f"{fn}: Unknown CPU submodel: {ls}")
                    return family,model,submodel,generation

            submodel = match.group()
            if submodel[1] == "1":
                generation = "Skylake (1st-gen)"
            elif submodel[1] == "2":
                generation = "Cascade Lake (2nd-gen)"
            elif submodel[1] == "3":
                generation = "Ice Lake (3rd-gen)"
            elif submodel[1] == "4":
                generation = "Sapphire Rapids (4th-gen)"
            elif submodel[1] == "5":
                generation = "Emerald Rapids (5th-gen)"
            elif submodel[0] == "2" and submodel[1] == "6":
                generation = "Broadwell"
            else:
                generation = "Unknown"
            return family,model,submodel,generation
        else:
            print(f"{fn}: Unknown CPU model {ls}")


        return family,model,submodel,generation

    if "amd" in ls or "epyc" in ls:
        family = "AMD"
        if "instinct" in ls:
            model = "Instinct"
            submodel = "MI300A"
        elif "epyc" in ls:
            model = "EPYC"
            match = re.search(r'(?<!\d)\d{4}(?!\d)', ls)
            if not match:
                match = re.search(r'(?<!\d)\d[a-z]\d{2}(?!\d)', ls)
                if not match:
                    submodel = "Other"
                    print(f"{fn}: Unknown CPU submodel: {ls}")
                    return family,model,submodel,generation

            submodel = match.group()
            if submodel[-1] == "5":
                generation = "Turin (5th-gen)"
            elif submodel[-1] == "4":
                generation = "Genoa (4th-gen)"
            elif submodel[-1] == "3":
                generation = "Milan (3rd-gen)"
            elif submodel[-1] == "2":
                generation = "Rome (2nd-gen)"
            elif submodel[-1] == "1":
                generation = "Naples (1st-gen)"
            else:
                generation = "Unknown"
            return family,model,submodel,generation
        else:
            print(f"{fn}: Unknown CPU model {ls}")

        return family,model,submodel,generation

    if "arm" in ls or "lx2" in ls or "fujitsu" in ls:
        family = "ARM"
        if "lx2" in ls:
            model = "LX2"
            submodel = "High-Performance"
            generation = "ARMv9"
        elif "a64fx" in ls:
            model = "Fujitsu"
            submodel = "A64FX"
            generation = "ARMv8.2"
        elif "grace" in ls:
            model = "Neoverse"
            submodel = "v2"
            generation = "ARMv9"
        else:
            model = "Other"
            submodel = "Other"
            print(f"{fn}: Unknown CPU model {ls}")

        return family,model,submodel,generation

    print(f"{fn}: Unknown CPU {ls}")
    return "Unknown","Unknown","Unknown","Unknown"

def get_gpu_model(fn, s):
    ls = s.lower()
    if ls in ["n/a", "/"]:
        return "N/A"
    if "nvidia a100" in ls:
        return "NVIDIA A100-64"
    if "a100-40" in ls:
        return "NVIDIA A100-40"
    if "mi100" in ls:
        return "AMD MI100"
    return "N/A"

def get_software_track_type(fn):
    """ tries to deduce the type of submission based on the file name"""
    if "Selective" in fn :
        return "Selective"
    if "MxP" in fn:
        return "MixedPrecission"
    if "Decomposer" in fn:
        return "Decomposer"
    if "coherent" in fn:
        return "CoherentIO"
    if "HKN_M." in fn or "HKN_S." in fn or "_CPU." in fn :
        return "Multilevel"
    if "A100_" in fn :
        return "LinearSolverOffload"
    if "ENGYS" in fn or "Cineca" in fn:
        return "FullGPUPort"
    return "Other"


# some affiliations are too long or need to be ammended
affil_map = {
 'Federal Waterways Engineering and Research Institute Germany (BAW)': 'BAW',
 'Technical University of Munich': "KIT/TUM",
}

def get_cells(s):
    """ given the mesh name this functions returns the cell numbers"""
    ls = s.lower()
    if ls == "coarse":
        return 65e6
    if ls == "medium":
        return 110e6
    if ls == "fine":
        return 236e6
    return 0

def take_till(df_in, col, end):
    """ takes all values until the example value end is reached """
    vs = df_in.loc[col].dropna().values[1:]
    out = []
    for v in vs:
        if v==end:
            return out
        out.append(v)

def find_row(df_in, name):
    """ this functions searches for the row that contains the string name """
    # row names are stored in the column with name Unnamed: 1
    col_1 = df_in["Unnamed: 1"]
    vals = list(col_1.values)
    # print(vals)
    col =  -1 if name not in vals else vals.index(name)
    if col > 0:
        return col
    # if we havend found the row yet we try to match the row name a bit fuzzy, the reason is that in same cases people edited the rowname by modifying the physical units
    for i,val in enumerate(vals):
        if name[0:12] in str(val):
            return i
    # if we reached this the row couldn't be found
    warnings.warn(f"could not find column {name}")
    return -1

def get_meta(df_in, field):
    """ given a field name this finds the corresponding value in column 3"""
    i = find_row(df_in, field)
    return df_in.loc[i].values[3]

def get_sim(df_in, field, terminator=None, num_vals = -1, has_separator=True, default=None):
    """ given a field name this function extracts the corresponding values till a final separator is found

    The function either searches till a terminator is found or takes the values[1:num_vals+1]
    """
    i = find_row(df_in, field)
    # early return if field not found
    if i < 0:
        warnings.warn(f"field {field} not found")
        return []
    if terminator:
        return take_till(df_in, i, terminator)
    if num_vals >= 0:
        values = df_in.loc[i].dropna().values
        # check if we have sufficient non nan values
        # if not we just return an empty list and deal
        # with it later
        # in the values list there are at least two values we dont
        # want to parse 1. the name and the default value
        offs = 2 if has_separator else 1

        if num_vals + offs <= len(values):
            # for v in values:
            #     print(f"type {type(v)}")
            ret = values[1:num_vals+1]

            return ret
        else:
            ret = []
            if not default is None :
                ret = [default for _ in range(num_vals)]
            return ret

# def get_timeseries()

def to_float(fn, what, s):
    try:
        return float(s)
    except:
        print(f"{fn}: failed to convert {s} {what} to float")
        return 1e-16

def to_tdp(fn, what, s):
    try:
        return float(s)
    except:
        print(f"{fn}: failed to convert {s} {what} to tdp")
        ss = str(s)
        ss=ss.replace("-", "0")
        ss=ss.replace("W", "")
        return to_float(fn, what, ss)

def read_row_col(df_in, row, col, filename):
    return df_in.loc[row].values[col]


def to_kwh(s):
    return s if s < 1000 else s/3.6e6

def serialize_forces(df_in, df_meta, filename):
    cid = filename.split("_")[0]
    track = get_meta(df_meta, "Submission relates to:")
    affil = get_meta(df_meta, "Affiliation:")
    iteration = df_in["Unnamed: 9"].dropna().values[2:]
    num_entries = len(iteration)
    wct = df_in["Unnamed: 10"].dropna().values[1:num_entries+1]
    cd = df_in["Unnamed: 11"].dropna().values[1:num_entries+1]
    cl = df_in["Unnamed: 12"].dropna().values[1:num_entries+1]
    cs = df_in["Unnamed: 13"].dropna().values[1:num_entries+1]
    iteration = list(map(partial(to_float, filename, "Iteration"), iteration))
    cd = list(map(partial(to_float, filename, "Cd"), cd))
    cs = list(map(partial(to_float, filename, "Cs"), cs))
    cl = list(map(partial(to_float, filename, "Cl"), cl))

    affil = affil_map[affil] if affil in affil_map.keys() else affil
    affils = [affil]*num_entries
    cid = [cid]*num_entries
    track = [track]*num_entries
    fn = [filename] * num_entries
    if num_entries < 500:
        return pd.DataFrame()

    cd_mean =   [read_row_col(df_in, 29, 3, filename)] * num_entries
    cs_mean =   [read_row_col(df_in, 29, 4, filename)] * num_entries
    cl_mean =   [read_row_col(df_in, 29, 5, filename)] * num_entries
    cd_error =  [read_row_col(df_in, 30, 3, filename)] * num_entries
    cs_error =  [read_row_col(df_in, 30, 4, filename)] * num_entries
    cl_error =  [read_row_col(df_in, 30, 5, filename)] * num_entries
    two_sigma_cd=  [read_row_col(df_in, 31, 3, filename)] * num_entries
    two_sigma_cs=  [read_row_col(df_in, 31, 4, filename)] * num_entries
    std_dev_cl= [read_row_col(df_in, 31, 5, filename)] * num_entries
    std_dev_cd= [read_row_col(df_in, 31, 3, filename)] * num_entries
    std_dev_cs= [read_row_col(df_in, 31, 4, filename)] * num_entries
    std_dev_cl= [read_row_col(df_in, 31, 5, filename)] * num_entries

    data_dict = {
            "Contributor Affiliation": affils,
            "Filename": fn,
            "Contributor ID": cid,
            "Track": track,
            "Run Wall-Clock Time [s]": wct,
            "Iteration": iteration,
            "Cd": cd,
            "Cl": cl,
            "Cs": cs,
            "cd_mean"   :    cd_mean   ,
            "cs_mean"   :    cs_mean   ,
            "cl_mean"   :    cl_mean   ,
            "cd_error"  :    cd_error  ,
            "cs_error"  :    cs_error  ,
            "cl_error"  :    cl_error  ,
            "2sigma_cd" :    two_sigma_cd,
            "2sigma_cs" :    two_sigma_cs,
            "std_dev_cl":    std_dev_cl,
            "std_dev_cd":    std_dev_cd,
            "std_dev_cs":    std_dev_cs,
            "std_dev_cl":    std_dev_cl,
            }
    try:
        df_out = pd.DataFrame.from_dict(data=data_dict)
        return df_out
    except Exception as e:
        print(f"{filename} cannot generate dataframe for forces: {e}")

def serialize(df_in, df_meta, filename):
    """ reads in raw dataframes and extracts the relevant data
    """
    # filenames are prefixed with contributor ids
    cid = filename.split("_")[0]
    # get the meta data
    # values are in column 3
    affil = get_meta(df_meta, "Affiliation:")
    mesh = get_meta(df_meta, "Selected Mesh")
    track = get_meta(df_meta, "Submission relates to:")
    flavour = get_meta(df_meta, "Flavor")

    # from now on the number of average time step  entries serves as a single source of truth
    # every submitted data set should at least t wall clock times
    ts = get_sim(df_in, "Wall-clock time per timestep/iteration [s]:", 24)
    ts = list(map(float, ts))
    num_entries = len(ts)

    wct = get_sim(df_in, "Wall-clock time to completion excl. pre-processing [s]:", 3600)
    is_partial = 0
    if len(wct) != len(ts):
        print(f"{filename}: number of timestep != number of wall clock time, assuming partial run")
        is_partial = 1
        if len(wct):
            print(f"{filename}: trying to fill wct, this makes only sense if N/A cases are contiguously to the right at the moment")
            for _ in range(len(ts)-len(wct)):
                wct.append(0)

    wct_pre = get_sim(df_in, "Time for pre-processing [s]:", num_vals=num_entries, default="N/A")
    nodes = get_sim(df_in, "# of nodes used:", num_vals=num_entries)
    cores = get_sim(df_in, "# of CPU cores used:", num_vals=num_entries)
    cpu = get_sim(df_in, "Hardware Spec (CPU):", num_vals=num_entries)
    cpu_model = list(map(partial(get_cpu_model, filename), cpu))
    gpu = get_sim(df_in, "Hardware Spec (GPU):", num_vals=num_entries, default="N/A")
    gpu_number = get_sim(df_in, "# of GPUs used:", num_vals=num_entries, default=0)
    gpu_model = list(map(partial(get_gpu_model, filename), gpu))
    software_type = [get_software_track_type(filename)] * num_entries

    fn = [filename] * num_entries
    flavour = [flavour] * num_entries
    is_partial = [is_partial] * num_entries
    track = [track] * num_entries
    cid = [cid] * num_entries
    affil = affil_map[affil] if affil in affil_map.keys() else affil
    affils = [affil]*num_entries
    meshs = [mesh.lower()]*num_entries
    cells = list(map(get_cells,meshs))
    tdp = get_sim(df_in, "TDP of system (CPU+Accelerator) [W]:", num_vals=num_entries, default=0.0)

    energy = get_sim(df_in, "Total energy to completion [kW*h or J]:", num_vals=num_entries, has_separator=False)
    decomp = get_sim(df_in, "Decomposition Method Method:", num_vals=num_entries, default="N/A")

    llc = get_sim(df_in, "Last-level Cache (Last-Level Cache):", num_vals=num_entries, default="N/A")
    interconnect = get_sim(df_in, "Network Interconnect Interconnect:", num_vals=num_entries, default="N/A")
    renum = get_sim(df_in, "Renumbering Method Method:", num_vals=num_entries, default="N/A")
    storage_fs = get_sim(df_in, "Storage File-system:", num_vals=num_entries, default="N/A")


    # NOTE this doesnt do anything at the moment, since
    if not ts:
        print(f"{filename}: No timesteps found, using wall clock time")
        ts = [wct[i]/4000 for i in range(len(wct))]

    reported_energy = 1
    if len(energy) == 0:
        print(f"{filename}: No energy data found")
        # energy = [tdp[i]/1000*nodes[i]*wct[i]/3600 for i in range(num_entries)]
        energy = [1e-32 for _ in range(num_entries)]
        reported_energy = 0

    # NOTE some files contain non convertible energy values
    energy = list(map(partial(to_float, filename, "energy"), energy))
    # NOTE some energies are in J so values above 1000 are considered to be in J
    energy = list(map(to_kwh, energy))
    reported_energy = [reported_energy]*num_entries
    tdp = list(map(partial(to_tdp, filename, "tdp"), tdp))

    if (num_entries == 0):
        print(f"{filename}: failed to process")

    data_dict = {
        "Contributor Affiliation": affils,
        "File Name": fn,
        "Run Wall-Clock Time [s]": wct,
        "Pre-Processing Wall-Clock Time [s]": wct_pre,
        "Storage File-System": storage_fs,
        "Number of CPU Cores": cores,
        "Number of GPU Devices": gpu_number,
        "Number of Nodes": nodes,
        "CPU Family": [t[0] for t in cpu_model],
        "CPU Model": [t[1] for t in cpu_model],
        "CPU Submodel": [t[2] for t in cpu_model],
        "CPU Generation": [t[3] for t in cpu_model],
        "GPU Model": gpu_model,
        "Mesh": meshs,
        "System TDP [W]": tdp,
        "Number of Cells": cells,
        "Time per Iteration [s]": ts,
        "Track": track,
        "OpenFOAM Flavor": flavour,
        "Run Consumed Energy [kWh]": energy,
        "Decomposition Method": decomp,
        "Last-Level Cache": llc,
        "Network Interconnect": interconnect,
        "Renumbering Method": renum,
        "Contributor ID": cid,
        "Is Partial": is_partial,
        "Is Energy Reported": reported_energy,
        "Software Optimization Category": software_type
    }

    try:
        df_out = pd.DataFrame.from_dict(data=data_dict)
        return  df_out
    except Exception as e:
        print(f"{filename} cannot generate dataframe: {e}")
        print(
            "Contributor Affiliation", len(affils),
            "File Name", len(fn),
            "Run Wall-Clock Time [s]", len(wct),
            "Pre-Processing Wall-Clock Time [s]", len(wct_pre),
            "Storage File-System", len(storage_fs),
            "Number of CPU Cores", len(cores),
            "Number of GPU Devices", len(gpu_number),
            "Number of Nodes", len(nodes),
            "CPU Family", len([t[0] for t in cpu_model]),
            "CPU Model", len([t[1] for t in cpu_model]),
            "CPU Submodel", len([t[2] for t in cpu_model]),
            "CPU Generation", len([t[3] for t in cpu_model]),
            "GPU Model", len(gpu_model),
            "Mesh", len(meshs),
        # "System TDP [W]": tdp,
        # "Number of Cells": cells,
        # "Time per Iteration [s]": ts,
        # "Track": track,
        # "OpenFOAM Flavor": flavour,
        # "Run Consumed Energy [kWh]": energy,
        # "Decomposition Method": decomp,
        # "Last-Level Cache": llc,
        # "Network Interconnect": interconnect,
        # "Renumbering Method": renum,
        # "Contributor ID": cid,
        # "Is Partial": is_partial,
        # "Is Energy Reported": reported_energy,
        # "Software Optimization Category": software_type
        )

def read_submissions(folder_name="submissions"):
    print("last time the data was updated",datetime.datetime.now(), " by ", os.getlogin() )
    _,_,fs = next(os.walk(folder_name))
    dfs = pd.DataFrame()

    for fn in fs:
        if not fn.endswith("xlsm"):
            continue
        try:
            df_meta = pd.read_excel(os.path.join(folder_name, fn), sheet_name="META Data")
            df_sim = pd.read_excel(os.path.join(folder_name, fn), sheet_name="Simulations")
            dft = serialize(df_sim, df_meta, fn)
        except Exception as e:
            print(f"failed serialization of {fn} with {e}")
            print(traceback.format_exc())
        dfs = pd.concat([dfs,dft])

    return dfs

def derive_metrics(df):
    df["Total Core Time [s]"] = df["Run Wall-Clock Time [s]"] * df["Number of CPU Cores"]
    df["Total Node Time [s]"] = df["Run Wall-Clock Time [s]"] * df["Number of Nodes"]
    #energy per iteration = tdp * dt [Ws]
    df["Energy per Iteration [J]"] = df["System TDP [W]"] * df["Time per Iteration [s]"]
    df["Energy per Iteration [kJ]"] = df["Energy per Iteration [J]"] / 1000

    # Total energy is based on the TDP since not all submissions provided (reliable) measurements
    df["Energy-To-Solution [kWh]"] = df["Energy per Iteration [J]"] * 4/3600

    # Total WCT is based on the WCT/iteration since there were partial runs
    df["Time-To-Solution [h]"] = df["Time per Iteration [s]"] * 4000/3600
    df["Core-Time-To-Solution [h]"] = df["Time-To-Solution [h]"] * df["Number of CPU Cores"]
    df["Node-Time-To-Solution [h]"] = df["Time-To-Solution [h]"] * df["Number of Nodes"]

    # FVOPS (Finite VOlume Operations Per Second) definition available in
    # " Galeazzo, F.C.C., Weiß, R.G., Lesnik, S., Rusche, H., Ruopp, A., 2024.
    #   Understanding superlinear speedup in current HPC architectures. IOP Conf.
    #   Ser.: Mater. Sci. Eng. 1312, 012009.
    #   https://doi.org/10.1088/1757-899X/1312/1/012009 "
    df["FVOPS"] = df["Number of Cells"] / df["Time per Iteration [s]"]
    df = df.astype({"Run Consumed Energy [kWh]": "float", "Number of CPU Cores": "int" })
    df["FVOPS per Energy"] = df["FVOPS"]/df["Energy per Iteration [J]"]
    df["FVOPS per Energy per Iteration"] = df["FVOPS"]/df["Energy per Iteration [J]"]
    df["FVOPS per Node"] = df["FVOPS"]/df["Number of Nodes"]

    return df

def save_fig(fig, fig_folder, name, do_save_fig=True, fig_dpi=600):
    if not do_save_fig:
        return

    pathlib.Path(fig_folder).mkdir(parents=True, exist_ok=True)
    fig_name = os.path.join(fig_folder, name+".png")
    print(f"saving figure to {fig_name}")
    fig.savefig(fig_name, dpi=fig_dpi, bbox_inches='tight')