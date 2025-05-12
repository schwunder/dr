import { Database } from "bun:sqlite";

const art = new Database("art.sqlite", { readonly: true });

// PARAM_COLS mapping (copy from db.py)
const PARAM_COLS = {
  umap: ["n_neighbors", "min_dist", "spread", "set_op_mix_ratio", "local_connectivity", "n_components", "metric", "random_state"],
  tsne: ["perplexity", "n_components", "random_state", "learning_rate", "n_iter", "early_exaggeration", "n_iter_without_progress", "min_grad_norm", "metric", "early_exaggeration_iter", "theta", "negative_gradient_method", "initialization", "n_jobs"],
  isomap: ["n_neighbors", "n_components"],
  lle: ["n_neighbors", "n_components", "random_state"],
  spectral: ["n_neighbors", "n_components", "random_state"],
  mds: ["n_components", "random_state"],
  sammon_random: ["n_dims", "n_iter", "tol", "input_type", "random_state"],
  pca: ["n_components", "random_state"],
  ipca: ["n_components", "batch_size", "random_state"],
  svd: ["n_components", "random_state"],
  fa: ["n_components", "random_state"],
  ica: ["n_components", "max_iter", "random_state"],
  agg: ["n_clusters"],
  kpca: ["n_components", "kernel", "gamma", "fit_inverse_transform", "random_state"],
  nystroem_pca: ["n_components", "nystroem_components", "kernel", "gamma", "random_state"],
  grp: ["n_components", "eps", "random_state"],
  srp: ["n_components", "density", "eps", "random_state"],
  nmf: ["n_components", "init", "random_state"],
  dictlearn: ["n_components", "random_state"],
  phate: ["n_components", "knn", "decay", "t", "gamma", "random_state"],
  trimap: ["n_dims", "n_inliers", "n_outliers", "n_random", "distance", "weight_temp", "lr", "n_iters", "random_state", "opt_method", "apply_pca"],
  spacemap: ["n_components", "n_near_field", "n_middle_field", "d_local", "d_global", "eta", "n_epochs", "init", "metric", "verbose", "plot_results", "num_plots"],
  glle: ["method", "k_neighbors", "max_iterations", "n_components", "n_generation_of_embedding", "verbosity"],
  paramrepulsor: ["n_components", "n_neighbors", "n_epochs", "lr", "spread", "repulsion_strength", "apply_pca", "init", "verbose"],
  pacmap: ["n_components", "n_neighbors", "MN_ratio", "FP_ratio", "num_iters", "lr", "apply_pca", "init", "random_state", "verbose"],
  clmds: ["n_clusters", "max_iter", "random_state"],
  tsne_pso: ["n_components", "perplexity", "n_particles", "n_iter", "random_state", "inertia_weight", "h", "f", "use_hybrid", "learning_rate", "init", "metric", "early_exaggeration", "min_grad_norm", "parameter_optimization", "dynamic_weight_adaptation", "small_dataset_handling", "numerical_robustness"],
  slisemap: ["radius", "lasso", "use_slipmap", "y"],
  tsimcne: ["n_components", "total_epochs", "random_state"]
};

// Fetch all configs for a method
function getConfigs(method = "umap") {
  const cols = PARAM_COLS[method] || [];
  const selectCols = ["config_id", "subset_strategy", "subset_size", "runtime", ...cols].join(", ");
  return art
    .query(`SELECT ${selectCols} FROM ${method}_configs ORDER BY config_id DESC`)
    .all();
}

// Fetch a single config by method and config_id
function getConfig(method, config_id) {
  const cols = PARAM_COLS[method] || [];
  const selectCols = ["config_id", "subset_strategy", "subset_size", "runtime", ...cols].join(", ");
  return art
    .query(`SELECT ${selectCols} FROM ${method}_configs WHERE config_id = ?`)
    .get(config_id);
}

// Fetch projection points for a method and config_id
function getProjectionPoints(method, config_id) {
  return art
    .query(
      `SELECT point_id, filename, artist, x, y FROM projection_points WHERE method = ? AND config_id = ?`
    )
    .all(method, config_id);
}

// Fetch all viz_config rows (for dropdown population)
// This will be implemented by calling the Python backend or by using a bridge/FFI if available.
// For now, this is a placeholder and should be implemented in the Python backend.
// Fetch all viz_config rows (for dropdown population)
function getAllVizConfigs() {
  return art.query("SELECT viz_id, method, config_id, low_res, created_at FROM viz_config ORDER BY viz_id DESC").all();
}

// Fetch viz_config by viz_id
function getVizConfig(viz_id) {
  return art.query(`SELECT * FROM viz_config WHERE viz_id = ?`).get(viz_id);
}

// Fetch viz_points by viz_id
function getVizPoints(viz_id) {
  return art.query(`SELECT * FROM viz_points WHERE viz_id = ?`).all(viz_id);
}

// Fetch all artists
function artists() {
  return art
    .query(
      `SELECT name, years, genre, nationality, bio, wikipedia, paintings FROM artists`
    )
    .all();
}

export { getConfigs, getConfig, getProjectionPoints, getVizConfig, getVizPoints, getAllVizConfigs, artists, PARAM_COLS };
