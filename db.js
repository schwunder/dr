import { Database } from "bun:sqlite";

const art = new Database("art.sqlite", { readonly: true });

// New points function: fetches points for a given method and config_id
const points = (method = "umap", config_id) => {
  if (!config_id) throw new Error("config_id is required");
  return art
    .query(
      `SELECT filename, artist, x, y FROM projection_points WHERE method = ? AND config_id = ?`
    )
    .all(method, config_id);
};

const artists = () => {
  return art
    .query(
      `
      SELECT name, years, genre, nationality, bio, wikipedia, paintings
      FROM artists
    `
    )
    .all();
};

// Helper: get available configs for a method
const getConfigs = (method = "umap") => {
  return art
    .query(`SELECT config_id, subset_strategy, subset_size, runtime FROM ${method}_configs ORDER BY config_id DESC`)
    .all();
};

export { points, artists, getConfigs };
