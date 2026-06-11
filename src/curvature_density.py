"""S1 module: per-vertex principal curvatures + QEM importance -> density map.

Input: a coarse face mesh (OBJ/PLY/STL). Output: per-vertex density in [0, 1]
that should be high on nose/lips/ears/eye rims and low on cheeks/forehead,
plus a vertex-colored PLY and orthographic PNG views for visual verification.

Usage:
    python curvature_density.py <mesh_file> [--out-dir ../output]
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.sparse as sp
import trimesh


def vertex_rings(mesh, n_rings=2):
    """List of neighbor index arrays (n-ring, excluding the vertex itself)."""
    n = len(mesh.vertices)
    e = mesh.edges_unique
    A = sp.csr_matrix(
        (np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])),
        shape=(n, n),
    )
    reach = A.copy()
    acc = A.copy()
    for _ in range(n_rings - 1):
        reach = reach @ A
        acc = acc + reach
    acc = acc.tolil()
    acc.setdiag(0)
    acc = acc.tocsr()
    return [acc.indices[acc.indptr[i]:acc.indptr[i + 1]] for i in range(n)]


def principal_curvatures(mesh, n_rings=2):
    """Per-vertex (k1, k2) by quadric fit in the tangent frame.

    Fits z = d*u + e*v + 1/2*(a*u^2 + 2*b*u*v + c*v^2) over the n-ring
    neighborhood, then takes eigenvalues of the Weingarten map I^-1 * II.
    """
    V = mesh.vertices.view(np.ndarray)
    N = mesh.vertex_normals
    rings = vertex_rings(mesh, n_rings)

    k1 = np.zeros(len(V))
    k2 = np.zeros(len(V))
    for i in range(len(V)):
        nb = rings[i]
        if len(nb) < 5:  # underdetermined fit (boundary/degenerate vertex)
            continue
        n = N[i]
        if not np.all(np.isfinite(n)):  # degenerate vertex -> garbage normal
            continue
        # tangent basis
        t = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        e1 = np.cross(n, t)
        e1_norm = np.linalg.norm(e1)
        if e1_norm < 1e-12:  # zero normal -> no tangent frame
            continue
        e1 /= e1_norm
        e2 = np.cross(n, e1)
        d = V[nb] - V[i]
        u, v, w = d @ e1, d @ e2, d @ n
        M = np.column_stack([u, v, 0.5 * u * u, u * v, 0.5 * v * v])
        try:
            du, dv, a, b, c = np.linalg.lstsq(M, w, rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        # first/second fundamental forms of the fitted graph at the origin
        E, F, G = 1 + du * du, du * dv, 1 + dv * dv
        scale = 1.0 / np.sqrt(1 + du * du + dv * dv)
        L, Mm, Nn = a * scale, b * scale, c * scale
        W = np.linalg.solve(np.array([[E, F], [F, G]]), np.array([[L, Mm], [Mm, Nn]]))
        ev = np.linalg.eigvals(W).real
        k1[i], k2[i] = max(ev), min(ev)
    return k1, k2


def qem_vertex_cost(mesh):
    """Per-vertex QEM importance: min midpoint-collapse cost over incident edges."""
    V = mesh.vertices.view(np.ndarray)
    n = len(V)

    # plane quadric p p^T per face, accumulated to its 3 vertices
    fn = mesh.face_normals
    d = -np.einsum("ij,ij->i", fn, V[mesh.faces[:, 0]])
    p = np.column_stack([fn, d])  # (F, 4)
    Kf = np.einsum("fi,fj->fij", p, p)  # (F, 4, 4)
    Q = np.zeros((n, 4, 4))
    for k in range(3):
        np.add.at(Q, mesh.faces[:, k], Kf)

    e = mesh.edges_unique
    m = np.hstack([(V[e[:, 0]] + V[e[:, 1]]) / 2, np.ones((len(e), 1))])  # (E, 4)
    Qe = Q[e[:, 0]] + Q[e[:, 1]]
    cost = np.einsum("ei,eij,ej->e", m, Qe, m)
    cost = np.maximum(cost, 0)  # numerical noise can go slightly negative

    vc = np.full(n, np.inf)
    np.minimum.at(vc, e[:, 0], cost)
    np.minimum.at(vc, e[:, 1], cost)
    vc[~np.isfinite(vc)] = 0
    return vc


def normalize(x, lo_pct=5, hi_pct=95):
    lo, hi = np.percentile(x, [lo_pct, hi_pct])
    if hi <= lo:
        return np.zeros_like(x)
    return np.clip((x - lo) / (hi - lo), 0, 1)


def smooth_scalar(mesh, x, iterations=10):
    """Uniform Laplacian smoothing of a per-vertex scalar (kills scan noise)."""
    n = len(mesh.vertices)
    e = mesh.edges_unique
    A = sp.csr_matrix(
        (np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])),
        shape=(n, n),
    )
    deg = np.asarray(A.sum(axis=1)).ravel()
    deg[deg == 0] = 1
    for _ in range(iterations):
        x = (A @ x) / deg
    return x


def density_map(mesh, n_rings=2, smooth_iters=10):
    k1, k2 = principal_curvatures(mesh, n_rings)
    curvedness = np.sqrt((k1 ** 2 + k2 ** 2) / 2)
    qem = qem_vertex_cost(mesh)
    curvedness = smooth_scalar(mesh, curvedness, smooth_iters)
    qem = smooth_scalar(mesh, qem, smooth_iters)
    density = 0.5 * normalize(curvedness) + 0.5 * normalize(qem)
    return density, curvedness, qem


def save_outputs(mesh, density, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    cmap = plt.get_cmap("turbo")
    colors = (cmap(density)[:, :3] * 255).astype(np.uint8)

    out_ply = os.path.join(out_dir, f"{name}_density.ply")
    colored = mesh.copy()
    colored.visual.vertex_colors = colors
    colored.export(out_ply)

    # orthographic scatter views (+/- each axis), front-facing vertices only
    V = mesh.vertices.view(np.ndarray)
    N = mesh.vertex_normals
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    views = [(0, 2, 1), (1, 2, 0), (2, 1, 0)]
    for col, (depth_ax, ya, xa) in enumerate(views):
        for row, sign in enumerate([1, -1]):
            ax = axes[row][col]
            vis = N[:, depth_ax] * sign > 0.1  # facing the camera
            order = np.argsort(sign * V[vis, depth_ax])
            ax.scatter(V[vis][order, xa], V[vis][order, ya],
                       c=density[vis][order], cmap="turbo", s=1, vmin=0, vmax=1)
            ax.set_title(f"view {'+' if sign > 0 else '-'}axis{depth_ax}")
            ax.set_aspect("equal")
            ax.axis("off")
    fig.suptitle(f"{name}: density map (red = hot = dense triangles)")
    out_png = os.path.join(out_dir, f"{name}_density.png")
    fig.savefig(out_png, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return out_ply, out_png


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mesh_file")
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(__file__), "..", "output"))
    ap.add_argument("--rings", type=int, default=2)
    args = ap.parse_args()

    mesh = trimesh.load(args.mesh_file, process=True, force="mesh")
    name = os.path.splitext(os.path.basename(args.mesh_file))[0]
    print(f"{name}: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")

    density, curvedness, qem = density_map(mesh, args.rings)
    for label, x in [("curvedness", curvedness), ("qem", qem), ("density", density)]:
        assert np.all(np.isfinite(x)), f"{label} has NaN/inf"
        print(f"{label}: min={x.min():.4g} median={np.median(x):.4g} max={x.max():.4g}")

    out_ply, out_png = save_outputs(mesh, density, args.out_dir, name)
    print("saved:", out_ply)
    print("saved:", out_png)


if __name__ == "__main__":
    main()
