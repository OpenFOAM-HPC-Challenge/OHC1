# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: py3.12
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Prolog

# %%
import pandas as pd
import seaborn as sb
import os
import OHCParser as op
import datetime
import traceback
from scipy.optimize import curve_fit
from matplotlib.ticker import FormatStrFormatter
import matplotlib
import numpy as np
import pathlib
import matplotlib.pyplot as plt

pd.options.mode.chained_assignment = None  # default='warn' - supress SettingWithCopyWarning

# %% [markdown]
# ## Auxiliary methods

# %%
# Secondary x-axis for cells per core
def addSecondaryAxisCellsPerCore(ax, cellsNumber, labelFontSize = 7):
    ticksCellsPerCoreInT = [round(cellsNumber/n/1000, 1) for n in ax.get_xticks()]
    tickLabelsStr = [f'{val:.0f}' if val%1 < 1e-1 else f'{val:.1f}' \
            for val in ticksCellsPerCoreInT]
    ax2 = ax.twiny()


    ax2.set_xscale("log")
    ax2.set_xticks(ax.get_xticks())
    ax2.set_xticklabels(tickLabelsStr, fontsize=labelFontSize)
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xlabel("Number of Cells per Core in thousands")
    ax2.tick_params(axis='x', which='both', labelrotation=90)

    formatter = matplotlib.ticker.LogFormatter(labelOnlyBase=False, minor_thresholds=(3, 1))
    ax2.xaxis.set_minor_formatter(formatter)
    ticksCellsPerCoreInT = [round(cellsNumber/n/1000, 1) for n in ax.get_xticks(minor=True)]
    tickLabelsStr = [f'{val:.0f}' if val%1 < 1e-1 else f'{val:.1f}' \
             for val in ticksCellsPerCoreInT]
    ax2.set_xticks(ax.get_xticks(minor=True), minor=True)
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticklabels(tickLabelsStr, minor=True, fontsize=labelFontSize)
    return ax2



# %% [markdown]
# ## Read Data

# %%
# general data
size_coarse=65e6
size_medium=110e6
size_fine=236e6

dfs = op.read_submissions()
dfs = op.derive_metrics(dfs)

# provide filtered data
df_hardware = dfs[dfs["Track"] == "Hardware Track"]
df_hardware = df_hardware.sort_values("CPU Family")
df_software = dfs[dfs["Track"] == "Software Track"]
df_hw_coarse = df_hardware[df_hardware["Mesh"]=="coarse"]
df_hw_medium = df_hardware[df_hardware["Mesh"]=="medium"]
df_hw_fine = df_hardware[df_hardware["Mesh"]=="fine"]

fig_folder = "figures_hwtrack"
doSaveFig = False



# %%
# Serialize forces we try to read in all even if most of them fail
_,_,fs = next(os.walk("submissions"))

df_forces = pd.DataFrame()
for fn in fs:
    if not fn.endswith("xlsm"):
        continue
    try:
        df_meta = pd.read_excel("submissions/" + fn, sheet_name="META Data")
        df_forces_submission = pd.read_excel("submissions/" + fn, sheet_name="Aero Forces")
        dft = op.serialize_forces(df_forces_submission, df_meta, fn)
    except Exception as e:
        print(f"failed force serialization {fn}")
        print(traceback.format_exc())
    df_forces = pd.concat([df_forces, dft])

# Clean up the forces dataframe by dropping rows with NaN values
df_forces = df_forces.dropna()

# %% [markdown]
# # Analysis
# ## Data validation

# %%
df_forces

# Focus on one submission for the example plot
df = df_forces[df_forces["Filename"] == "05_Huawei_OHC1_DrivAer_Result_Software_Selective_Coarse.xlsm"]

# Set the starting iteration for sampling according to the meanCalc result
samplingStartIter = 1265

# Calculate running mean, standard deviation, and standard error for Cd, Cl, and Cs
df["CdExpandingMean0"] = df["Cd"].expanding().mean()
df["CdExpandingMean"] = df["Cd"][samplingStartIter:].expanding().mean()
df["CdExpandingStd"] = df["Cd"].expanding().std()
df["CdExpandingSem"] = df["Cd"][samplingStartIter:].expanding().sem()
df["ClExpandingMean"] = df["Cl"][samplingStartIter:].expanding().mean()
df["ClExpandingStd"] = df["Cl"].expanding().std()
df["ClExpandingSem"] = df["Cl"][samplingStartIter:].expanding().sem()
df["CsExpandingMean"] = df["Cs"][samplingStartIter:].expanding().mean()
df["CsExpandingStd"] = df["Cs"].expanding().std()
df["CsExpandingSem"] = df["Cs"][samplingStartIter:].expanding().sem()

fig, ax = plt.subplots(2, 3, figsize=(15, 7))
ax[0,0].plot(df["Iteration"], df["Cd"], label="Instantaneous")
ax[0,0].set_ylabel("Cd")
ax[0,0].plot(df["Iteration"], df["CdExpandingMean"], label="Running Mean")
ax[0,1].plot(df["Iteration"], df["Cl"], label="Instantaneous")
ax[0,1].set_ylabel("Cl")
ax[0,1].plot(df["Iteration"], df["ClExpandingMean"], label="Running Mean")
ax[0,2].plot(df["Iteration"], df["Cs"], label="Instantaneous")
ax[0,2].set_ylabel("Cs")
ax[0,2].plot(df["Iteration"], df["CsExpandingMean"], label="Running Mean")
ax[1,0].plot(df["Iteration"], 2*df["CdExpandingSem"], label="Running Std Error")
ax[1,1].plot(df["Iteration"], 2*df["ClExpandingSem"], label="Running Std Error")
ax[1,2].plot(df["Iteration"], 2*df["CsExpandingSem"], label="Running Std Error")

# Add reference lines for the mean values of Cd, Cl, and Cs
references = [0.262, 0.0787, 0.0116]
for i, a in enumerate(ax[0,:]):
    a.xaxis.set_ticklabels([])
    a.set_xticks(np.arange(0, 4001, 1000))
    a.set_xlim(0, 4000)
    # a.set_xticks([])
    a.plot(df["Iteration"], np.array([references[i]]*len(df)), label="Reference (" + str(references[i]) + ")")
    a.legend()

# Add reference lines for the threshold of 2*sem
threshold = 0.0015
coeffs = ["Cd", "Cl", "Cs"]
for i, a in enumerate(ax[1,:]):
    a.set_xlabel("Iteration")
    a.set_xticks(np.arange(0, 4001, 1000))
    a.set_ylabel(r"$2\sigma(\mu)$ for " + coeffs[i])
    a.plot(df["Iteration"], np.array([threshold]*len(df)), label="Threshold (" + str(threshold) + ")")
    a.set_xlim(0, 4000)
    a.legend()

figFontSize = 12
for a in ax.flat:
    for item in ([a.title, a.xaxis.label, a.yaxis.label] +
             a.get_xticklabels() + a.get_yticklabels() + a.legend().texts):
        item.set_fontsize(figFontSize)

fig.tight_layout()
op.save_fig(fig, fig_folder, "meancalc_validation_example_remake", True, fig_dpi=200)

# %% [markdown]
# ## Hardware track
# ### Strong scaling

# %%
# Use only CPUs with more than one entry per CPU Generation and Mesh combination, to ensure that the lowess fit is meaningful
df = df_hardware
df = df[df.groupby(["CPU Generation", "Mesh"])["CPU Generation"].transform(len) > 2]

# Sort the DataFrame by CPU Generation and Mesh to ensure the correct order in the plots
CPUGen_sorting_order = [
    'Rome (2nd-gen)','Milan (3rd-gen)','Genoa (4th-gen)','Turin (5th-gen)',
    'ARMv8.2','ARMv9','Skylake (1st-gen)','Broadwell','Cascade Lake (2nd-gen)',
    'Sapphire Rapids (4th-gen)','Emerald Rapids (5th-gen)',
    'i9']
df["CPUGenIndex"] = df["CPU Generation"].apply(lambda gen: CPUGen_sorting_order.index(gen))
df["MeshIndex"] = df["Mesh"].apply(lambda mesh: ["coarse","medium","fine"].index(mesh))
df = df.sort_values(["MeshIndex", "CPUGenIndex"])

ax = sb.lmplot(
    df,
    x="Number of CPU Cores",
    y="Time-To-Solution [h]",
    hue="CPU Generation",
    ci=None,
    col="CPU Family",
    row="Mesh",
    lowess=True,
    )

# Adjust axes, labels, and legend
figFontSize = 16
for a in ax.axes.flat:
    print(a.get_title())
    a.set_xscale("log", base=2)
    a.set_yscale("log", base=2)
    a.xaxis.set_major_formatter(FormatStrFormatter('%.5g'))
    a.yaxis.set_major_formatter(FormatStrFormatter('%.2g'))
    title = a.get_title()
    if "coarse" in title:
        size = size_coarse
    elif "medium" in title:
        size = size_medium
    elif "fine" in title:
        size = size_fine
    else:
        raise ValueError(f"Unexpected title: {title}")
    ax2 = addSecondaryAxisCellsPerCore(a, size, labelFontSize=14)
    fig = a.get_figure()
    for item in ([a.title, a.xaxis.label, a.yaxis.label, ax2.xaxis.label] +
             a.get_xticklabels() + a.get_yticklabels() + ax._legend.texts):
        item.set_fontsize(figFontSize)

ax.tight_layout()
sb.move_legend(ax, "lower right", bbox_to_anchor=(0.70, 1.01), borderaxespad=0,
               frameon=True, ncol=3, fontsize=figFontSize, title_fontsize=figFontSize)
op.save_fig(fig, fig_folder, "strong_scaling_facetgrid", doSaveFig)

# %% [markdown]
# ### Parallel efficiency

# %%
# Use only CPUs with more than one entry per CPU Generation, to ensure that the lowess fit is meaningful
df = df_hardware
df = df.reset_index(drop=True)
df = df[df["Number of Nodes"] > 1]
df = df[df.groupby("CPU Generation")["CPU Generation"].transform(len) > 2]

# Calculate Total Core Time and find the minimum Total Core Time for each Mesh and CPU Family combination
df["Total Core Time [h]"] = df["Time-To-Solution [h]"] * df["Number of CPU Cores"]
for mesh in ["coarse", "medium", "fine"]:
    for cpuFamily in df["CPU Family"].unique():
        maxT_val = df["Total Core Time [h]"].where((df["Mesh"] == mesh) & (df["CPU Family"] == cpuFamily)).min()
        maxT_id = df["Total Core Time [h]"].where((df["Mesh"] == mesh) & (df["CPU Family"] == cpuFamily)).idxmin()
        print(f"Mesh: {mesh}, CPU Family: {cpuFamily}, min Total Core Time: {maxT_val} s, index: {maxT_id}, achieved by CPU Generation: {df.loc[maxT_id, 'CPU Generation']} with {df.loc[maxT_id, 'Number of CPU Cores']} cores")
        df.loc[(df["Mesh"] == mesh) & (df["CPU Family"] == cpuFamily), "maxT"] = maxT_val

# Calculate Parallel Efficiency
df["Parallel Efficiency"] = df["maxT"] / df["Time-To-Solution [h]"] / df["Number of CPU Cores"]

# Sort the DataFrame by CPU Generation and Mesh to ensure the correct order in the plots
CPUGen_sorting_order = [
    'Rome (2nd-gen)','Milan (3rd-gen)','Genoa (4th-gen)','Turin (5th-gen)',
    'ARMv8.2','ARMv9','Skylake (1st-gen)','Broadwell','Cascade Lake (2nd-gen)',
    'Sapphire Rapids (4th-gen)','Emerald Rapids (5th-gen)',
    'i9']
df["CPUGenIndex"] = df["CPU Generation"].apply(lambda gen: CPUGen_sorting_order.index(gen))
df["MeshIndex"] = df["Mesh"].apply(lambda mesh: ["coarse","medium","fine"].index(mesh))
df = df[df["Mesh"] != "medium"]
df = df.sort_values(["MeshIndex", "CPUGenIndex"])

ax = sb.lmplot(
    df,
    x="Number of CPU Cores",
    y="Parallel Efficiency",
    hue="CPU Generation",
    ci=None,
    col="CPU Family",
    row="Mesh",
    lowess=True,
    )

# Adjust axes, labels, and legend
figFontSize = 16
print(ax.axes.flat)
for a in ax.axes.flat:
    print(a.get_title())
    a.set_xscale("log", base=2)
    a.xaxis.set_major_formatter(FormatStrFormatter('%.5g'))
    a.yaxis.set_major_formatter(FormatStrFormatter('%.2g'))
    title = a.get_title()
    if "coarse" in title:
        size = size_coarse
    elif "medium" in title:
        size = size_medium
    elif "fine" in title:
        size = size_fine
    else:
        raise ValueError(f"Unexpected title: {title}")
    ax2 = addSecondaryAxisCellsPerCore(a, size, labelFontSize=14)
    fig = a.get_figure()
    for item in ([a.title, a.xaxis.label, a.yaxis.label, ax2.xaxis.label] +
             a.get_xticklabels() + a.get_yticklabels() + ax._legend.texts):
        item.set_fontsize(figFontSize)

ax.tight_layout()
sb.move_legend(ax, "lower right", bbox_to_anchor=(0.70, 1.01), borderaxespad=0,
               frameon=True, ncol=3, fontsize=figFontSize, title_fontsize=figFontSize)
op.save_fig(fig, fig_folder, "efficiency_cores_facetGrid_mesh_CPUFamily", doSaveFig, fig_dpi=200)

# %% [markdown]
# ### High Bandwidth Memory and Last-Level Cache effect
# #### Single node

# %%
df = df_hardware
df = df[df["Number of Nodes"] == 1]

# Harmonize the Last-Level Cache information, to be able to use it as a hue in the plots
df["Last-Level Cache"] = df["Last-Level Cache"].str.replace(" MB", "MB")
df["Last-Level Cache"] = df["Last-Level Cache"].str.replace("MB", " MB")

# Extract the numeric value of the Last-Level Cache in MB for sorting and plotting
df["Last-Level Cache in MB"] = df["Last-Level Cache"].str.extract(r'(\d+[.\d]*)')
df["Last-Level Cache in MB"] = pd.to_numeric(df["Last-Level Cache in MB"], errors='coerce')
df.sort_values("Last-Level Cache in MB", inplace=True)

g = sb.FacetGrid(
    df,
    col="Mesh",
    hue="Last-Level Cache",
    aspect=0.75,
    sharey=True,
    subplot_kws={"yscale":"log", "xscale":"log"},
    col_order=["coarse","medium","fine"],
    legend_out=True
)

g.map_dataframe(sb.scatterplot, y="Time-To-Solution [h]", x="Energy-To-Solution [kWh]")
g.add_legend()
for ax in g.axes.flat:
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.4g'))
    ax.set_yscale("log", base=2)
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.4g'))

fig = ax.get_figure()
op.save_fig(fig, fig_folder, "TTS_ETS_facetGrid-singleNode-Last-Level Cache", doSaveFig)

# %% [markdown]
# #### Multi-node
#

# %%
df = df_hardware

# Restrict to the runs with more than one node
df = df[df["Number of Nodes"] > 1]

# Harmonize the Last-Level Cache information, to be able to use it as a hue in the plots
df["Last-Level Cache"] = df["Last-Level Cache"].str.replace(" MB", "MB")
df["Last-Level Cache"] = df["Last-Level Cache"].str.replace("MB", " MB")

# Extract the numeric value of the Last-Level Cache in MB for sorting and plotting
df["Last-Level Cache in MB"] = df["Last-Level Cache"].str.extract(r'(\d+[.\d]*)')
df["Last-Level Cache in MB"] = pd.to_numeric(df["Last-Level Cache in MB"], errors='coerce')

# Choose specific Last-Level Cache values to focus on in the plot
df = df[(df["Last-Level Cache in MB"] == 384)
        | (df["Last-Level Cache in MB"] == 256)
        | (df["Last-Level Cache in MB"] == 105)
        | (df["Last-Level Cache"] == "on-package memory")
    ]

df.sort_values("Last-Level Cache in MB", inplace=True)
g = sb.FacetGrid(
    df,
    col="Mesh",
    hue="Last-Level Cache",
    aspect=0.75,
    sharey=True,
    subplot_kws={"yscale":"log", "xscale":"log"},
    col_order=["coarse","medium","fine"],
    legend_out=True
)

g.map_dataframe(sb.scatterplot, y="Energy-To-Solution [kWh]", x="Number of Nodes")
g.add_legend()
for ax in g.axes.flat:
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.5g'))
    ax.set_yscale("log", base=2)
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.4g'))

fig = ax.get_figure()
op.save_fig(fig, fig_folder, "ETS_nodes_facetGrid_mesh_LLC", doSaveFig)
