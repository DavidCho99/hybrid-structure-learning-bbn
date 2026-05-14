args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 4) {
  stop("Usage: Rscript r_arges_driver.R <input_csv> <cpdag_output_csv> <repr_output_csv> <skeleton_output_csv>")
}

input_path <- args[1]
cpdag_output_path <- args[2]
repr_output_path <- args[3]
skeleton_output_path <- args[4]

suppressMessages(library(bnlearn))
suppressMessages(library(pcalg))

df <- read.csv(input_path, stringsAsFactors = FALSE, check.names = FALSE)
labels <- names(df)

factor_df <- df
for (column_name in names(factor_df)) {
  factor_df[[column_name]] <- as.factor(factor_df[[column_name]])
}

encoded_df <- factor_df
for (column_name in names(encoded_df)) {
  encoded_df[[column_name]] <- as.integer(encoded_df[[column_name]])
}

hpc_fit <- hpc(factor_df)
hpc_arcs <- arcs(hpc_fit)

skeleton_adj <- matrix(FALSE, nrow = length(labels), ncol = length(labels),
                       dimnames = list(labels, labels))
if (!is.null(hpc_arcs) && nrow(hpc_arcs) > 0) {
  for (i in seq_len(nrow(hpc_arcs))) {
    from <- hpc_arcs[i, "from"]
    to <- hpc_arcs[i, "to"]
    if (!is.na(from) && !is.na(to) && from != to) {
      skeleton_adj[from, to] <- TRUE
      skeleton_adj[to, from] <- TRUE
    }
  }
}

fixed_gaps <- !skeleton_adj
diag(fixed_gaps) <- FALSE

score <- new("GaussL0penObsScore", data.matrix(encoded_df), labels = labels)
arges_fit <- ges(
  score,
  fixedGaps = fixed_gaps,
  adaptive = "triples",
  phase = c("forward", "backward", "turning"),
  iterate = TRUE
)

matrix_to_edge_df <- function(adj_matrix) {
  if (is.null(adj_matrix)) {
    return(data.frame(source = character(), target = character()))
  }

  edges <- which(adj_matrix != 0, arr.ind = TRUE)
  if (nrow(edges) == 0) {
    return(data.frame(source = character(), target = character()))
  }

  data.frame(
    source = rownames(adj_matrix)[edges[, "row"]],
    target = colnames(adj_matrix)[edges[, "col"]],
    stringsAsFactors = FALSE
  )
}

skeleton_edge_df <- matrix_to_edge_df(skeleton_adj)
cpdag_edge_df <- matrix_to_edge_df(as(arges_fit$essgraph, "matrix"))
repr_edge_df <- matrix_to_edge_df(as(arges_fit$repr, "matrix"))

write.csv(cpdag_edge_df, cpdag_output_path, row.names = FALSE)
write.csv(repr_edge_df, repr_output_path, row.names = FALSE)
write.csv(skeleton_edge_df, skeleton_output_path, row.names = FALSE)
