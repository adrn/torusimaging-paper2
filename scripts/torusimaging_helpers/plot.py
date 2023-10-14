import astropy.units as u
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


def plot_bdata(bdata):
    fig, axes = plt.subplots(
        1, 3, figsize=(15, 5), constrained_layout=True, sharex=True, sharey=True
    )
    cs = axes[0].pcolormesh(
        bdata["vel"].to_value(u.km / u.s),
        bdata["pos"].to_value(u.kpc),
        bdata["counts"],
        norm=mpl.colors.LogNorm(),
        cmap="Greys",
    )
    fig.colorbar(cs, ax=axes[0])

    cs = axes[1].pcolormesh(
        bdata["vel"].to_value(u.km / u.s), bdata["pos"].to_value(u.kpc), bdata["label"]
    )
    fig.colorbar(cs, ax=axes[1])

    cs = axes[2].pcolormesh(
        bdata["vel"].to_value(u.km / u.s),
        bdata["pos"].to_value(u.kpc),
        bdata["label_err"],
        norm=mpl.colors.LogNorm(),
        cmap="Blues",
    )
    fig.colorbar(cs, ax=axes[2])

    axes[0].set_title("Log counts")
    axes[1].set_title("Mean label")
    axes[2].set_title("Label error")

    for ax in axes:
        ax.set_xlabel("$v_z$ [km/s]")
    axes[0].set_ylabel("$z$ [kpc]")

    return fig, axes


def plot_spline_functions(model, params):
    r_e_grid = np.linspace(0, model._label_knots.max(), 128)
    e_vals = model._get_es(r_e_grid, params["e_params"])

    fig, axes = plt.subplots(1, 2, figsize=(10, 5), layout="constrained")

    ax = axes[0]
    sum_ = None
    for m, vals in e_vals.items():
        (l,) = ax.plot(r_e_grid, vals, marker="", label=f"$e_{m}$")  # noqa
        ax.scatter(
            model._e_knots[m],
            model.e_funcs[m](model._e_knots[m], params["e_params"][m]["vals"]),
            color=l.get_color(),
        )

        if sum_ is None:
            sum_ = vals
        else:
            sum_ += vals

    ax.plot(r_e_grid, sum_, ls="--", marker="")
    ax.set_title("$e_m$ functions")
    ax.legend(loc="upper left", fontsize=10)
    ax.set_xlabel("$r_e$")

    ax = axes[1]
    l_vals = model.label_func(r_e_grid, **params["label_params"])
    (l,) = ax.plot(r_e_grid, l_vals, marker="")  # noqa

    l_vals = model.label_func(model._label_knots, **params["label_params"])
    ax.scatter(model._label_knots, l_vals, color=l.get_color())
    ax.set_xlabel("$r$")
    ax.set_title("Label function")

    return fig, axes


def plot_data_model_residual(
    model, bdata, params, zlim, vzlim=None, aspect=True, residual_lim=0.05
):
    title_fontsize = 20
    title_pad = 10

    cb_labelsize = 16
    mgfe_cbar_xlim = (0, 0.15)
    mgfe_cbar_vlim = (-0.05, 0.18)

    tmp_aaf = model.compute_action_angle(
        np.atleast_1d(zlim) * 0.75, [0.0] * u.km / u.s, params
    )
    Omega = tmp_aaf["Omega"][0]
    if vzlim is None:
        vzlim = zlim * Omega
    vzlim = vzlim.to_value(u.km / u.s, u.dimensionless_angles())

    fig, axes = plt.subplots(
        1, 3, figsize=(16, 5.1), sharex=True, sharey=True, layout="constrained"
    )

    cs = axes[0].pcolormesh(
        bdata["vel"].to_value(u.km / u.s),
        bdata["pos"].to_value(u.kpc),
        bdata["label"],
        cmap="magma",
        rasterized=True,
        vmin=mgfe_cbar_vlim[0],
        vmax=mgfe_cbar_vlim[1],
    )
    cb = fig.colorbar(cs, ax=axes[0:2])
    cb.set_label("mean [Mg/Fe]", fontsize=cb_labelsize)
    cb.ax.set_ylim(mgfe_cbar_xlim)
    cb.ax.set_yticks(np.arange(mgfe_cbar_xlim[0], mgfe_cbar_xlim[1] + 1e-3, 0.05))
    cb.ax.yaxis.set_tick_params(labelsize=14)

    model_mgfe = np.array(model._get_label(bdata["pos"], bdata["vel"], params))
    cs = axes[1].pcolormesh(
        bdata["vel"].to_value(u.km / u.s),
        bdata["pos"].to_value(u.kpc),
        model_mgfe,
        cmap="magma",
        rasterized=True,
        vmin=mgfe_cbar_vlim[0],
        vmax=mgfe_cbar_vlim[1],
    )

    cs = axes[2].pcolormesh(
        bdata["vel"].to_value(u.km / u.s),
        bdata["pos"].to_value(u.kpc),
        bdata["label"] - model_mgfe,
        cmap="RdBu_r",
        vmin=-residual_lim,
        vmax=residual_lim,
        rasterized=True,
    )
    cb = fig.colorbar(cs, ax=axes[2])  # , orientation="horizontal")
    cb.set_label("data $-$ model", fontsize=cb_labelsize)
    cb.ax.yaxis.set_tick_params(labelsize=14)

    # Titles
    axes[0].set_title("Simulated Data", fontsize=title_fontsize, pad=title_pad)
    axes[1].set_title("Optimized OTI Model", fontsize=title_fontsize, pad=title_pad)
    axes[2].set_title("Residuals", fontsize=title_fontsize, pad=title_pad)
    fig.suptitle("Demonstration with Simulated Data: Harmonic Oscillator", fontsize=24)

    # Labels
    axes[0].set_ylabel(f"$z$ [{u.kpc:latex_inline}]")
    for ax in axes:
        ax.set_xlabel(f"$v_z$ [{u.km/u.s:latex_inline}]")

    # Ticks
    axes[0].set_xticks(np.arange(-300, 300 + 1, 100))
    axes[0].set_xticks(np.arange(-300, 300 + 1, 50), minor=True)
    axes[1].set_yticks(np.arange(-3, 3 + 1e-3, 1))
    axes[1].set_yticks(np.arange(-3, 3 + 1e-3, 0.5), minor=True)

    for ax in axes:
        if aspect:
            # ax.set_aspect(2 * np.pi / Omega.value)
            ax.set_aspect(1 / Omega.value)
        ax.set_xlim(-vzlim, vzlim)
        ax.set_ylim(-zlim.to_value(u.kpc), zlim.to_value(u.kpc))

    return fig, axes